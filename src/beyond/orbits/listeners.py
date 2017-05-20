
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
        Yield:
            Orbit
        """

        orb.info = ""
        for listener in listeners:
            if listener.check(orb):
                yield self._bisect(listener.prev, orb, listener)

            # Saving of the current value for the next iteration
            listener.prev = orb

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


class NodeListener(Listener):

    def info(self, orb):
        return "AscNode" if abs(self(orb)) < 0.1 else "DscNode"

    def __call__(self, orb):
        orb = orb.copy(form='keplerian', frame="EME2000")
        return ((orb.omega + orb.nu + np.pi) % (2 * np.pi)) - np.pi


class ApsideListener(Listener):

    def info(self, orb):
        return "Perigee" if abs(self(orb)) < 0.1 else "Apogee"

    def __call__(self, orb):
        orb = orb.copy(form='keplerian', frame="EME2000")
        return ((orb.nu + np.pi) % (2 * np.pi)) - np.pi


class StationSignalListener(Listener):

    def __init__(self, station):
        self.station = station

    def info(self, orb):
        orb = orb.copy(frame=self.station, form='spherical')
        return "{} {}".format(
            "AOS" if orb.phi_dot > 0 else "LOS",
            self.station.name
        )

    def __call__(self, orb):
        orb = orb.copy(form='spherical', frame=self.station)
        return orb.phi


class StationMaxListener(Listener):

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


def stations_listeners(stations):
    stations = stations if isinstance(stations, (list, tuple)) else [stations]

    listeners = []
    for sta in stations:
        listeners.append(StationSignalListener(sta))
        listeners.append(StationMaxListener(sta))

    return listeners
