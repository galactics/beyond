
"""Definition of ephemeris
"""

import numpy as np


class Ephem:
    """This class represents a range of orbits

    It provides several useful interfaces in order to compute throught them

    Example:
        ephem = orb.ephem(Date.now(), timedeltat(hours=6), timedelta(minutes=2))
        ephem.change_frame('ITRF')
        ephem.change_form('spherical')
        latitudes = ephem[:,1]
        longitudes = ephem[:,2]
    """

    def __init__(self, orbits):
        self._orbits = list(sorted(orbits, key=lambda x: x.date))

    def __iter__(self):
        self._i = -1
        return self

    def __next__(self):
        self._i += 1
        if self._i >= len(self._orbits):
            raise StopIteration
        return self._orbits[self._i]

    def __getitem__(self, index):
        if isinstance(index, (slice, int)):
            return self._orbits[index]
        elif isinstance(index, tuple) and len(index) == 2:
            return np.array(self._orbits)[index]
        else:
            raise IndexError(index)

    def __len__(self):
        return len(self._orbits)

    @property
    def start(self):
        """Date of the first element
        """
        return self._orbits[0].date

    @property
    def stop(self):
        """Date of the last element
        """
        return self._orbits[-1].date

    def change_frame(self, frame):
        """Change the frames of all points
        """
        for orb in self:
            orb.change_frame(frame)

    def change_form(self, form):
        """Change the form of all points
        """
        for orb in self:
            orb.change_form(form)

    def interpolate(self, date):
        """Interpolate data at a given date

        Args:
            date (Date):
        Return:
            Orbit:
        """

        if not self.start <= date <= self.stop:
            raise ValueError("Date '%s' not in range" % date)

        for i, orb in enumerate(reversed(self)):
            if orb.date < date:
                break
        else:
            raise ValueError("Date not in range")

        y0 = orb
        y1 = self[-i]

        result = y0[:] + (y1[:] - y0[:]) * (date.mjd - y0.date.mjd) / (y1.date.mjd - y0.date.mjd)

        return orb.__class__(date, result, orb.form, orb.frame, orb.propagator)
