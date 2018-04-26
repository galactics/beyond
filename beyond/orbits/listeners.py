
import numpy as np
from abc import ABCMeta, abstractmethod
from datetime import timedelta

from ..frames.frames import get_frame


__all__ = [
    'Speaker', 'Listener', 'stations_listeners', 'StationSignalListener',
    'StationMaxListener', 'StationMaskListener', 'LightListener', 'ApsideListener',
    'NodeListener', 'ZeroDopplerEvent'
]


class Speaker(metaclass=ABCMeta):
    """This class is used to trigger Listeners.

    By calling :py:meth:`listen`, the subclass can trigger the listeners.
    """

    def listen(self, orb, listeners):
        """This method allows to loop over the listeners and trigger the :py:meth:`_bisect` method
        in case a watched parameter has its state changed.

        Args:
            orb (Orbit): The current state of the orbit
            listeners (iterable): List of Listener objects
        Return:
            list of Orbit: Orbits corresponding to events, sorted by dates
        """

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
        eps = timedelta.resolution

        step = (end.date - begin.date) / 2
        while abs(step) >= eps:
            date = begin.date + step
            orb = self.propagate(date)
            if listener(begin) * listener(orb) > 0:
                begin = orb
            else:
                end = orb
            step = (end.date - begin.date) / 2
        else:
            orb.event = listener.info(end if listener.binary else orb)
            return orb


class Listener(metaclass=ABCMeta):
    """Base class for listeners
    """

    prev = None
    binary = False

    def check(self, orb):
        """Method that check whether or not the listener is trigered

        Args:
            orb (Orbit):
        Return:
            bool: `True` if there is a zero-crossing for the parameter watched
                by the listener
        """

        return self.prev is not None and np.sign(self(orb)) != np.sign(self(self.prev))

    @abstractmethod
    def info(self, orb):
        """
        Args:
            orb (Orbit)
        Return:
            Event: Information concerning the event listened to
        """
        pass

    @abstractmethod
    def __call__(self, orb):
        pass


class Event:

    def __init__(self, listener, info):
        self.listener = listener
        self.info = info

    def __str__(self):
        return self.info

    def __format__(self, fmt):
        return format(str(self), fmt)


class LightEvent(Event):
    pass


class LightListener(Listener):
    """This class compute, for a given orbit, its illumination by the sun, allowing to detect
    umbra and penumbra events.
    """

    event = LightEvent
    binary = True

    UMBRA = "umbra"
    PENUMBRA = "penumbra"
    FRAME = "EME2000"

    def __init__(self, type=UMBRA):
        """
        Args:
            type (str): Choose which event to trigger between umbra or penumbra
        """
        self.type = type

    def info(self, orb):
        if self.type == self.UMBRA:
            return LightEvent(self, "Umbra in" if self(orb) <= 0 else "Umbra out")
        else:
            return LightEvent(self, "Penumbra in" if self(orb) <= 0 else "Penumbra out")

    def __call__(self, orb):
        """
        Args:
            orb (Orbit)
        Return:
            int: Positive value if the satellite is illuminated
        """

        # This import is not at the top of the file to avoid circular imports
        from ..env.solarsystem import get_body

        orb = orb.copy(form="cartesian", frame=self.FRAME)

        alpha_umb = np.radians(0.264121687)
        alpha_pen = np.radians(0.269007205)

        sun = get_body("Sun")

        sun_orb = sun.propagate(orb.date)
        sun_orb.frame = orb.frame
        vec_r_sun = sun_orb[:3]
        r_sun_norm = np.linalg.norm(vec_r_sun)

        vec_r = orb[:3]
        r_norm = np.linalg.norm(vec_r)

        if vec_r_sun @ vec_r < 0:
            zeta = np.arccos(-vec_r_sun @ vec_r / (r_sun_norm * r_norm))

            sat_horiz = r_norm * np.cos(zeta)
            sat_vert = r_norm * np.sin(zeta)

            x = orb.frame.center.r / np.sin(alpha_pen)
            pen_vert = np.tan(alpha_pen) * (x + sat_horiz)

            if sat_vert <= pen_vert:

                if self.type == self.PENUMBRA:
                    # Penumbra
                    return -1
                else:

                    y = orb.frame.center.r / np.sin(alpha_umb)
                    umb_vert = np.tan(alpha_umb) * (y - sat_horiz)

                    if sat_vert <= umb_vert:
                        # Unmbra
                        return -1

        return 1


class NodeEvent(Event):
    pass


class NodeListener(Listener):
    """Listener for Ascending and Descending Node detection
    """

    event = NodeEvent

    def __init__(self, frame="EME2000"):
        self.frame = frame

    def info(self, orb):
        orb = orb.copy(frame=self.frame, form="spherical")
        return NodeEvent(self, "Desc Node" if orb.phi_dot < 0 else "Asc Node")

    def __call__(self, orb):
        orb = orb.copy(form='spherical', frame=self.frame)
        return orb.phi


class ApsideEvent(Event):
    pass


class ApsideListener(Listener):
    """Listener for Periapside and Apoapside detection
    """

    event = ApsideEvent

    def __init__(self, frame="EME2000"):
        self.frame = frame

    def info(self, orb):
        return ApsideEvent(self, "Periapsis" if self(orb) > self(self.prev) else "Apoapsis")

    def __call__(self, orb):
        orb = orb.copy(form='spherical', frame=self.frame)
        return orb.r_dot


class SignalEvent(Event):

    def __str__(self):
        return "{} {} {}".format(
            self.info,
            self.elev,
            self.station
        )

    @property
    def elev(self):
        return self.listener.elev

    @property
    def station(self):
        return self.listener.station


class StationSignalListener(Listener):
    """Listener for AOS and LOS of a given station
    """

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
        orb = orb.copy(frame=self.station, form='spherical')
        return self.event(self, "AOS" if orb.phi_dot > 0 else "LOS")

    def __call__(self, orb):
        orb = orb.copy(form='spherical', frame=self.station)
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

        if station.mask is None:
            raise ValueError("No mask defined for this station")

        self.station = station

    def info(self, orb):
        return self.event(self, "AOS" if self(orb) > self(self.prev) else "LOS")

    def check(self, orb):
        # Override to disable the computation when the object is not
        # in view of the station
        orb2 = orb.copy(frame=self.station, form='spherical')
        if orb2.phi <= 0:
            return False
        else:
            return super().check(orb)

    def __call__(self, orb):
        orb = orb.copy(form='spherical', frame=self.station)
        return orb.phi - self.station.get_mask(orb.theta)


class MaxEvent(Event):

    def __init__(self, listener):
        super().__init__(listener, "MAX")

    def __str__(self):
        return "MAX {}".format(self.station)

    @property
    def station(self):
        return self.listener.station


class StationMaxListener(Listener):
    """Listener for max elevation of a pass over a station
    """

    event = MaxEvent

    def __init__(self, station):
        self.station = station

    def info(self, orb):
        return MaxEvent(self)

    def check(self, orb):
        # Override to disable the computation when the object is not
        # in view of the station
        orb2 = orb.copy(frame=self.station, form='spherical')
        if orb2.phi <= 0 or orb2.phi_dot > 0:
            return False
        else:
            return super().check(orb)

    def __call__(self, orb):
        orb = orb.copy(form='spherical', frame=self.station)
        return orb.phi_dot


class ZeroDopplerEvent(Event):

    def __init__(self, listener):
        super().__init__(listener, "Zero Doppler")

    @property
    def frame(self):
        return self.listener.frame

    def __str__(self):
        return "Zero Doppler {}".format(self.frame)


class ZeroDopplerListener(Listener):

    event = ZeroDopplerEvent

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
        return ZeroDopplerEvent(self)

    def check(self, orb):
        # Override to disable the computation when the object is not in view of the station
        if self.sight and orb.copy(frame=self.frame, form='spherical').phi <= 0:
            return False
        else:
            return super().check(orb)

    def __call__(self, orb):
        return orb.copy(frame=self.frame, form='spherical').r_dot


def stations_listeners(stations):
    """Function for creating listeners for a a list of station

    Args:
        stations (iterable): List of TopocentricFrame
    Return:
        list of Listener
    """
    stations = stations if isinstance(stations, (list, tuple)) else [stations]

    listeners = []
    for sta in stations:

        listeners.append(StationSignalListener(sta))
        listeners.append(StationMaxListener(sta))
        if sta.mask is not None:
            listeners.append(StationMaskListener(sta))

    return listeners
