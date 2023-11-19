"""Listeners allow to watch for state transition during the propagation of an orbit.
For example, the :abbr:`AOS (Acquisition Of Signal)` and :abbr:`LOS (Loss Of Signal)` of
a satellite as seen from a station.

Each time a propagator (a subclass of :py:class:`Speaker`) detects a state transition, it
creates an Orbit instance at the date of the event, and add an ``event`` attribute which
is an :py:class:`Event` instance.
"""
import numpy as np
from abc import ABCMeta, abstractmethod
from datetime import timedelta

from ..dates import Date


__all__ = [
    "Speaker",
    "Listener",
    "stations_listeners",
    "StationSignalListener",
    "StationMaxListener",
    "StationMaskListener",
    "LightListener",
    "TerminatorListener",
    "ApsideListener",
    "NodeListener",
    "AnomalyListener",
    "RadialVelocityListener",
    "find_event",
    "events_iterator",
]


class Speaker(metaclass=ABCMeta):
    """This class is used to trigger Listeners.

    By calling :py:meth:`listen`, the subclass can trigger the listeners.
    """

    _eps_bisect = timedelta.resolution

    @classmethod
    def clear_listeners(cls, listeners):
        """Clear Listeners in order to do a propagation with a clean state"""
        if isinstance(listeners, Listener):
            listeners = [listeners]

        for listener in listeners:
            listener.clear()

    def listen(self, orb, listeners):
        """This method allows to loop over the listeners and trigger the :py:meth:`_bisect` method
        in case a watched parameter has its state changed.

        Args:
            orb (Orbit): The current state of the orbit
            listeners (iterable): List of Listener objects
        Return:
            list of Orbit: Orbits corresponding to events, sorted by dates
        """

        if isinstance(listeners, Listener):
            listeners = [listeners]

        orb.event = None
        results = []
        for listener in listeners:
            if listener.check(orb):
                results.append(self._bisect(listener.prev, orb, listener))

            # Saving of the current value for the next iteration
            listener.prev = orb
        return sorted(results, key=lambda x: x.date)

    def _bisect(self, begin, end, listener):
        """This method search for the zero-crossing of the watched parameter

        Args:
            begin (Orbit):
            end (Orbit)
            listener (Listener)
        Return
            Return
        """

        step = (end.date - begin.date) / 2

        while abs(step) >= self._eps_bisect:
            date = begin.date + step
            orb = self.propagate(date)
            if listener(begin) * listener(orb) > 0:
                begin = orb
            else:
                end = orb
            step = (end.date - begin.date) / 2
        else:
            end.event = listener.info(end)
            return end


class Listener(metaclass=ABCMeta):
    """Base class for listeners"""

    prev = None

    def check(self, orb):
        """Method that check whether or not the listener is triggered

        Args:
            orb (Orbit):

        Return:
            bool: True if there is a zero-crossing for the parameter watched by the listener
        """

        return self.prev is not None and np.sign(self(orb)) != np.sign(self(self.prev))

    @abstractmethod
    def info(self, orb):  # pragma: no cover
        """
        Args:
            orb (Orbit)
        Return:
            Event: Information concerning the event listened to
        """
        pass

    @abstractmethod
    def __call__(self, orb):  # pragma: no cover
        pass

    def clear(self):
        """Clear the state of the listener, in order to make a new iteration"""
        self.prev = None


class Event:
    """An instance of this class, or its subclass, is added as attribute to the Orbit
    instance each time a state change is detected.
    """

    def __init__(self, listener, info):
        self.listener = listener
        self.info = info

    def __str__(self):  # pragma: no cover
        return self.info

    def __format__(self, fmt):  # pragma: no cover
        return format(str(self), fmt)


class LightEvent(Event):
    pass


class LightListener(Listener):
    """This class compute, for a given orbit, its illumination by the sun, allowing to detect
    umbra and penumbra events.

    .. image:: /_static/light.svg

    Angles in this image are over-exaggerated
    """

    event = LightEvent

    UMBRA = "umbra"
    """Penumbra <-> Shadow"""
    PENUMBRA = "penumbra"
    """Light <-> Penumbra"""

    def __init__(self, type=UMBRA, frame=None):
        """
        Args:
            type (str): Choose which event to trigger between umbra or penumbra
            frame (str) : Name of the reference frame from which to compute.
                If ``None`` the frame is unchanged.
        """
        self.type = type
        self.frame = frame

    def info(self, orb):
        if self.type == self.UMBRA:
            return LightEvent(self, "Umbra entry" if self(orb) <= 0 else "Umbra exit")
        else:
            return LightEvent(
                self, "Penumbra entry" if self(orb) <= 0 else "Penumbra exit"
            )

    def __call__(self, orb):
        """
        Args:
            orb (Orbit)
        Return:
            int: Positive value if the satellite is illuminated
        """

        # This import is not at the top of the file to avoid circular imports
        from ..env.solarsystem import get_body

        sun = get_body("Sun")
        sun_orb = sun.propagate(orb.date).copy(frame=self.frame)
        orb = orb.copy(form="cartesian", frame=sun_orb.frame)

        x_sun = np.array(sun_orb[:3])
        norm_x_sun = np.linalg.norm(x_sun)

        x_sat = np.array(orb[:3])
        norm_x_sat = np.linalg.norm(x_sat)

        # This should be the real way to compute alpha_umb and alpha_pen, but the
        # benefit is not that great, as the angles don't change a lot throughout
        # the year.
        alpha_umb = np.arcsin((sun.r - orb.frame.center.body.r) / norm_x_sun)
        alpha_pen = np.arcsin((sun.r - orb.frame.center.body.r) / norm_x_sun)

        # Fixed values of angles, for a simplified computation
        # alpha_umb = np.radians(0.264121687)
        # alpha_pen = np.radians(0.269007205)

        if x_sun @ x_sat < 0:
            zeta = np.arccos(-x_sun @ x_sat / (norm_x_sun * norm_x_sat))

            sat_horiz = norm_x_sat * np.cos(zeta)
            sat_vert = norm_x_sat * np.sin(zeta)

            x = orb.frame.center.body.r / np.sin(alpha_pen)
            pen_vert = np.tan(alpha_pen) * (x + sat_horiz)

            if sat_vert <= pen_vert:
                if self.type == self.PENUMBRA:
                    # Penumbra
                    return -1
                else:
                    y = orb.frame.center.body.r / np.sin(alpha_umb)
                    umb_vert = np.tan(alpha_umb) * (y - sat_horiz)

                    if sat_vert <= umb_vert:
                        # Umbra
                        return -1

        return 1


class TerminatorEvent(Event):
    pass


class TerminatorListener(Listener):
    """Detect the night/day transition at the surface of the earth, at
    the zenith
    """

    event = TerminatorEvent

    _frame_name = "SunFrame"

    def __init__(self):
        """"""

        from ..env.solarsystem import get_body

        self.sun = get_body("Sun")
        self._frame = self.sun.propagate(Date.now()).as_frame(self._frame_name)

    def info(self, orb):
        orb2 = orb.copy(frame=self._frame, form="spherical")

        if orb2.r_dot > 0:
            msg = "Night Terminator"
        else:
            msg = "Day Terminator"

        return TerminatorEvent(self, msg)

    def __call__(self, orb):
        sun_pos = self.sun.propagate(orb.date).copy(frame=orb.frame, form="cartesian")[
            :3
        ]
        sat_pos = orb.copy(form="cartesian")[:3]

        sun_norm = np.linalg.norm(sun_pos)
        sat_norm = np.linalg.norm(sat_pos)

        return (sat_pos @ sun_pos) / (sun_norm * sat_norm)


class NodeEvent(Event):
    pass


class NodeListener(Listener):
    """Listener for Ascending and Descending Node detection"""

    event = NodeEvent

    def __init__(self, frame=None):
        """
        Args:
            frame (str) : Name of the reference frame from which to compute
                If ``None`` the frame is unchanged.
        """
        self.frame = frame

    def info(self, orb):
        orb = orb.copy(frame=self.frame, form="spherical")
        return NodeEvent(self, "Desc Node" if orb.phi_dot < 0 else "Asc Node")

    def __call__(self, orb):
        orb = orb.copy(form="spherical", frame=self.frame)
        return orb.phi


class ApsideEvent(Event):
    pass


class ApsideListener(Listener):
    """Listener for Periapside and Apoapside detection"""

    event = ApsideEvent

    def __init__(self, frame=None):
        """
        Args:
            frame (str) : Name of the reference frame from which to compute
                If ``None`` the frame is unchanged.
        """
        self.frame = frame

    def info(self, orb):
        return ApsideEvent(
            self, "Periapsis" if self(orb) > self(self.prev) else "Apoapsis"
        )

    def __call__(self, orb):
        orb = orb.copy(form="spherical", frame=self.frame)
        return orb.r_dot


class AnomalyEvent(Event):
    pass


class AnomalyListener(Listener):
    """Listener for anomaly (in the orbital sense)"""

    event = AnomalyEvent

    ANOMALIES = {
        "true": ("keplerian", "ν"),
        "mean": ("keplerian_mean", "M"),
        "eccentric": ("keplerian_eccentric", "E"),
        "aol": ("keplerian_circular", "u"),
    }

    def __init__(self, value, anomaly="true", frame=None):
        """
        Args:
            value (float):
            anomaly (str): Type of anomaly, can be any from 'true', 'mean', 'eccentric' or 'aol'
            frame (str):
        """
        self.value = value
        self.anomaly = anomaly
        self.frame = frame

    @property
    def _anomaly(self):
        if self.anomaly not in self.ANOMALIES:  # pragma: no cover
            raise ValueError(f"Unknown anomaly type : {self.anomaly}")

        return self.ANOMALIES[self.anomaly]

    @property
    def form(self):
        return self._anomaly[0]

    @property
    def attr(self):
        return self._anomaly[1]

    def _diff(self, orb):
        return (self._convert(orb) - self.value + np.pi) % (2 * np.pi) - np.pi

    def check(self, orb):
        return abs(self._diff(orb)) < 2 and super().check(orb)

    def info(self, orb):
        # breakpoint()
        if self.anomaly == "aol":
            txt = "Argument of Latitude"
        else:
            txt = f"{self.anomaly.title()} Anomaly"

        return AnomalyEvent(self, f"{txt} = {np.degrees(self._convert(orb)):.2f}")

    def _convert(self, orb):
        return getattr(orb.copy(frame=self.frame, form=self.form), self.attr)

    def __call__(self, orb):
        return self._diff(orb)


class SignalEvent(Event):  # pragma: no cover
    def __str__(self):
        return f"{self.info} {self.elev} {self.station}"

    @property
    def elev(self):
        return self.listener.elev

    @property
    def station(self):
        return self.listener.station


class StationSignalListener(Listener):
    """Listener for AOS and LOS of a given station"""

    event = SignalEvent

    def __init__(self, station, elev=0):
        """
        Args:
            station (TopocentricFrame): Station from which to listen to elevation events
            elev (float): Elevation from which to trigger the listener (in radians)
        """
        self.station = station
        self.elev = elev

    def info(self, orb):
        orb = orb.copy(frame=self.station, form="spherical")
        return self.event(self, "AOS" if orb.phi_dot > 0 else "LOS")

    def __call__(self, orb):
        orb = orb.copy(form="spherical", frame=self.station)
        return orb.phi - self.elev


class MaskEvent(SignalEvent):
    @property
    def elev(self):
        return "Mask"


class StationMaskListener(StationSignalListener):
    """Listener for time of rising above the physical horizon (real horizon may be blocked by
    terrain, vegetation, buildings, etc.).
    """

    event = MaskEvent

    def __init__(self, station):
        """
        Args:
            station (TopocentricFrame): Station from which to listen to elevation events
        """
        self.station = station

    def info(self, orb):
        return self.event(self, "AOS" if self(orb) > self(self.prev) else "LOS")

    def check(self, orb):
        # Override to disable the computation when the object is not
        # in view of the station
        orb2 = orb.copy(frame=self.station, form="spherical")
        if orb2.phi <= 0:
            return False
        else:
            return super().check(orb)

    def __call__(self, orb):
        orb = orb.copy(form="spherical", frame=self.station)
        return orb.phi - self.station.get_mask(orb.theta)


class MaxEvent(Event):  # pragma: no cover
    def __init__(self, listener):
        super().__init__(listener, "MAX")

    def __str__(self):
        return f"MAX {self.station}"

    @property
    def station(self):
        return self.listener.station


class StationMaxListener(Listener):
    """Listener for max elevation of a pass over a station"""

    event = MaxEvent

    def __init__(self, station):
        """
        Args:
            station (TopocentricFrame): Station from which to listen to elevation events
        """
        self.station = station

    def info(self, orb):
        return MaxEvent(self)

    def check(self, orb):
        # Override to disable the computation when the object is not
        # in view of the station
        orb2 = orb.copy(frame=self.station, form="spherical")
        if orb2.phi <= 0 or orb2.phi_dot > 0:
            return False
        else:
            return super().check(orb)

    def __call__(self, orb):
        orb = orb.copy(form="spherical", frame=self.station)
        return orb.phi_dot


class RadialVelocityEvent(Event):  # pragma: no cover
    def __init__(self, listener):
        super().__init__(listener, "Radial Velocity")

    @property
    def frame(self):
        return self.listener.frame

    def __str__(self):
        return f"Zero Doppler {self.frame}"


class RadialVelocityListener(Listener):
    event = RadialVelocityEvent

    def __init__(self, frame, sight=False):
        """
        Args:
            frame (~beyond.frames.frames.Frame): Frame from which the computation is made
            sight (bool): If the frame used is a station, it could be interesting to only compute
                the Zero Doppler when the object is in sight
        """
        self.frame = frame
        self.sight = sight

    def info(self, orb):
        return self.event(self)

    def check(self, orb):
        # Override to disable the computation when the object is not in view of the station
        if self.sight and orb.copy(frame=self.frame, form="spherical").phi <= 0:
            return False
        else:
            return super().check(orb)

    def __call__(self, orb):
        return orb.copy(frame=self.frame, form="spherical").r_dot


def stations_listeners(stations):
    """Function for creating listeners for a a list of station

    Each station will have the following Listeners attached:

        - :py:class:`StationSignalListener`
        - :py:class:`StationMaxListener`
        - :py:class:`StationMaskListener` if the station has a mask defined
          (see :py:func:`~beyond.frames.stations.create_station` for details)

    Args:
        stations (iterable): List of TopocentricFrame
    Return:
        list of Listeners
    """
    stations = stations if isinstance(stations, (list, tuple)) else [stations]

    listeners = []
    for sta in stations:
        listeners.append(StationSignalListener(sta))
        listeners.append(StationMaxListener(sta))
        if sta.mask is not None:
            listeners.append(StationMaskListener(sta))

    return listeners


def find_event(iterator, event, offset=0):
    """Find a specific event in an extropolation

    Args:
        iterator (Iterable[Orbit]): Itertator in which to look for the event
        event (str or Event): Event to look for
        offset (int): The function will return the Nth event detected
    Return:
        Orbit
    """

    if isinstance(event, Event):  # pragma: no cover
        event = event.info

    for i, orb in enumerate(events_iterator(iterator, event)):
        if i == offset:
            break
    else:
        raise RuntimeError(f"No event '{event}' found at offset={offset}")

    return orb


def events_iterator(iterator, *events):
    """Iterate only over the listed events

    Args:
        iterator (Iterable[Orbit])
        events (List[str]):
    Yield:
        Orbit:
    """

    for orb in iterator:
        if orb.event and (not events or orb.event.info in events):
            yield orb
