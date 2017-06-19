
import numpy as np
from abc import ABCMeta, abstractmethod
from datetime import timedelta


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

        orb.info = ""
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
            orb.info = listener.info(end if listener.binary else orb)
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
            str: Information concerning the event listened to
        """
        pass

    @abstractmethod
    def __call__(self, orb):
        pass


class LightListener(Listener):
    """This class compute, for a given orbit, its illumination.
    """

    binary = True

    UMBRA = "umbra"
    PENUMBRA = "penumbra"
    FRAME = "EME2000"

    def __init__(self, event=UMBRA):
        """
        Args:
            event (str): Choose which event to trigger between umbra or penumbra
        """
        self.event = event

    def info(self, orb):
        if self.event == self.UMBRA:
            return "Umbra in" if self(orb) <= 0 else "Umbra out"
        else:
            return "Penumbra in" if self(orb) <= 0 else "Penumbra out"

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

                if self.event == self.PENUMBRA:
                    # Penumbra
                    return -1
                else:

                    y = orb.frame.center.r / np.sin(alpha_umb)
                    umb_vert = np.tan(alpha_umb) * (y - sat_horiz)

                    if sat_vert <= umb_vert:
                        # Unmbra
                        return -1

        return 1


class NodeListener(Listener):
    """Listener for Ascending and Descending Node detection
    """

    def __init__(self, frame="EME2000"):
        self.frame = frame

    def info(self, orb):
        orb = orb.copy(frame=self.frame, form="spherical")
        return "Desc Node" if orb.phi_dot < 0 else "Asc Node"

    def __call__(self, orb):
        orb = orb.copy(form='spherical', frame=self.frame)
        return orb.phi


class ApsideListener(Listener):
    """Listener for Periapside and Apoapside detection
    """

    def __init__(self, frame="EME2000"):
        self.frame = frame

    def info(self, orb):
        return "Periapsis" if self(orb) > self(self.prev) else "Apoapsis"

    def __call__(self, orb):
        orb = orb.copy(form='spherical', frame=self.frame)
        return orb.r_dot


class StationSignalListener(Listener):
    """Listener for AOS and LOS of a given station
    """

    def __init__(self, station, elev=0):
        """
        Args:
            station (TopocentricFrame): Station from which to listen to elevation events
            elev (float): Elevation from which to trigger the listener (in radians)
        """
        self.station = station
        self.elevation = elev

    def info(self, orb):
        orb = orb.copy(frame=self.station, form='spherical')
        return "{} {}".format(
            "AOS" if orb.phi_dot > 0 else "LOS",
            self.station.name
        )

    def __call__(self, orb):
        orb = orb.copy(form='spherical', frame=self.station)
        return orb.phi - self.elevation


class StationMaxListener(Listener):
    """Listener for max elevation of a pass over a station
    """

    def __init__(self, station):
        self.station = station

    def info(self, orb):
        return "{} {}".format("MAX", self.station.name)

    def check(self, orb):
        # Override to disable the computation when the object is not
        # in view of the station
        if orb.copy(frame=self.station, form='spherical').phi <= 0:
            return False
        else:
            return super().check(orb)

    def __call__(self, orb):
        orb = orb.copy(form='spherical', frame=self.station)
        return orb.phi_dot


class ZeroDopplerListener(Listener):

    def __init__(self, frame, sight=False):
        """
        Args:
            frame (~beyond.frames.frame._Frame): Frame from which the computation is made
            sight (bool): If the frame used is a station, it could be interesting to only compute
                the Zero Doppler when the object is in sight
        """
        self.frame = frame
        self.sight = sight

    def info(self, orb):
        return "Zero Doppler"

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

    return listeners
