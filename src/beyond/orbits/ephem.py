
"""Definition of ephemeris
"""

import numpy as np
from datetime import timedelta

from ..frames.frame import orbit2frame


class Ephem:
    """This class represents a range of orbits

    It provides several useful interfaces in order to compute throught them

    Example:

    .. code-block:: python

        ephem = orb.ephem(Date.now(), timedeltat(hours=6), timedelta(minutes=2))
        ephem.frame = 'ITRF'
        ephem.form = 'spherical'
        latitudes = ephem[:,1]
        longitudes = ephem[:,2]
    """

    LINEAR = "linear"
    LAGRANGE = "lagrange"

    def __init__(self, orbits, method=LAGRANGE, order=8):
        self._orbits = list(sorted(orbits, key=lambda x: x.date))
        self.method = method
        self.order = order

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

    @frame.setter
    def frame(self, frame):
        """Change the frames of all points
        """
        for orb in self:
            orb.frame = frame

    @property
    def form(self):
        """Get the form of the first point
        """
        return self._orbits[0].form

    @form.setter
    def form(self, form):
        """Change the form of all points
        """
        for orb in self:
            orb.form = form

    def interpolate(self, date, method=None, order=None):
        """Interpolate data at a given date

        Args:
            date (Date):
            method (str): Method of interpolation to use
            order (int): In case of ``LAGRANGE`` method is used
        Return:
            Orbit:
        """

        if not self.start <= date <= self.stop:
            raise ValueError("Date '%s' not in range" % date)

        # reseach of the point just after the date we wish to interpolate to
        for next_i, orb in enumerate(self):  # pragma: no branch
            if orb.date > date:
                break

        method = method if method is not None else self.method
        order = order if order is not None else self.order

        if method == self.LINEAR:

            y0 = self[next_i - 1]
            y1 = self[next_i]

            result = y0[:] + (y1[:] - y0[:]) * (date.mjd - y0.date.mjd) / (y1.date.mjd - y0.date.mjd)

        elif method == self.LAGRANGE:

            stop = next_i + order
            start = next_i
            if stop >= len(self):
                start -= stop - len(self)

            # selection of the subset of data, of length 'order' around the desired value
            subset = self[start:stop]
            date_subset = np.array([x.date.mjd for x in subset])

            result = np.zeros(6)

            # Everything is on wikipedia
            #        k
            # L(x) = Σ y_j * l_j(x)
            #        j=0
            #
            # l_j(x) = Π (x - x_m) / (x_j - x_m)
            #     0 <= m <= k
            #        m != j
            for j in range(order):
                # This mask is here to enforce the m != j in the lagrange polynomials
                mask = date_subset != date_subset[j]
                l_j = (date.mjd - date_subset[mask]) / (date_subset[j] - date_subset[mask])
                result = result + l_j.prod() * subset[j]

        else:
            raise ValueError("Unkown interpolation method", method)

        return orb.__class__(date, result, orb.form, orb.frame, orb.propagator)

    def propagate(self, date):
        """Alias of :py:meth:`interpolate`
        """
        return self.interpolate(date)

    def ephemeris(self, **kwargs):
        """Ephemeris generator based on the data of this one, but with different dates

        If an argument is set to ``None`` it will keep the same property as its parent

        Keyword Arguments:
            start (:py:class:`~beyond.utils.date.Date` or None): Date of the first point
            stop (:py:class:`~beyond.utils.date.Date`, :py:class:`~datetime.timedelta` or None): Date
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

    def register_as_frame(self, name, orientation=None):  # pragma: no cover
        """Register the Ephem object as a frame

        see :py:func:`beyond.frames.frame.orbit2frame` for details of the arguments
        """
        orbit2frame(name, self, orientation)
