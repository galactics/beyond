
"""Definition of ephemeris
"""

import numpy as np
from datetime import timedelta


class Ephem:
    """This class represents a range of orbits

    It provides several useful interfaces in order to compute throught them

    Example:

    .. code-block:: python

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
            # retrieve a defined Orbit object
            return self._orbits[index]
        else:
            # In order to comply with numpy array handling (e.g. column selection)
            return np.array(self._orbits)[index]

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

    # @property
    # def steps(self):
    #     """Time intervals used in the ephemeris
    #     """
    #     return set([self[i].date - self[i + 1].date for i in range(len(self) - 1)])

    @property
    def frame(self):
        """Get the frame of the first point
        """
        return self._orbits[0].frame

    def change_frame(self, frame):  # pragma: no cover
        """Change the frames of all points
        """
        for orb in self:
            orb.change_frame(frame)

    def change_form(self, form):  # pragma: no cover
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

        for i, orb in enumerate(reversed(self)):  # pragma: no branch
            if orb.date <= date:
                break

        y0 = orb
        y1 = self[-i]

        result = y0[:] + (y1[:] - y0[:]) * (date.mjd - y0.date.mjd) / (y1.date.mjd - y0.date.mjd)

        return orb.__class__(date, result, orb.form, orb.frame, orb.propagator)

    def propagate(self, date):
        """Alias of :py:meth:`interpolate`
        """
        return self.interpolate(date)

    def ephemeris(self, **kwargs):
        """Ephemeris generator based on the data of this one, but with different dates

        If an argument is set to ``None`` it will keep the same property as its parent

        Keyword Arguments:
            start (:py:class:`~space.utils.date.Date` or None): Date of the first point
            stop (:py:class:`~space.utils.date.Date`, :py:class:`~datetime.timedelta` or None): Date
                of the last point
            step (:py:class:`~datetime.timedelta` or None): Step to use during the computation
        Yield:
            :py:class:`Orbit`:
        """

        start = kwargs.get('start', self.start)
        stop = kwargs.get('stop', self.stop)
        step = kwargs.get('step', None)

        if isinstance(stop, timedelta):
            stop = start + stop

        if step is None:

            dates = [x.date for x in self]
            if start not in dates:
                raise ValueError("If 'step' is not defined, 'start' should be an existing point")
            if stop not in dates:
                raise ValueError("If 'step' is not defined, 'stop' should be an existing point")

            # The step stays the same as the original ephemeris
            for cursor in self:

                if cursor.date < start:
                    continue

                if cursor.date > stop:
                    break

                yield cursor
        else:
            # create as ephemeris with a different step than the original
            date = start
            while date <= stop:
                yield self.interpolate(date)
                date += step

    def ephem(self, **kwargs):
        """Create an Ephem object which is a subset of this one

        Take the same keyword arguments as :py:meth:`ephemeris`

        Return:
            Ephem:
        """

        return self.__class__(self.ephemeris(**kwargs))
