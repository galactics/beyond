
from datetime import timedelta

from .base import AnalyticalPropagator
from ..orbits import Tle

from sgp4.earth_gravity import wgs72
from sgp4.io import twoline2rv


class Sgp4(AnalyticalPropagator):
    """Interface to the `sgp4 <https://github.com/brandon-rhodes/python-sgp4/>`__
    library
    """

    @property
    def orbit(self):
        return self._orbit if hasattr(self, '_orbit') else None

    @orbit.setter
    def orbit(self, orbit):
        """Initialize the propagator

        Args:
            orbit (Orbit)
        """

        self._orbit = orbit
        tle = Tle.from_orbit(orbit)
        lines = tle.text.splitlines()

        if len(lines) == 3:
            _, line1, line2 = lines
        else:
            line1, line2 = lines

        self.tle = twoline2rv(line1, line2, wgs72)

    def propagate(self, date):
        """Propagate the initialized orbit

        Args:
            date (Date or datetime.timedelta)
        Return:
            Orbit
        """

        if type(date) is timedelta:
            date = self.orbit.date + date

        # Convert the date to a tuple usable by the sgp4 library
        _date = [float(x) for x in "{:%Y %m %d %H %M %S.%f}".format(date).split()]
        p, v = self.tle.propagate(*_date)

        # Convert from km to meters
        result = [x * 1000 for x in p + v]

        return self.orbit.__class__(
            date,
            result,
            'cartesian',
            'TEME',
            self.__class__(),
            **self.orbit.complements
        )
