
"""Definition of ephemeris
"""

import numpy as np
from datetime import timedelta

from .listeners import Speaker
from ..frames.frames import orbit2frame


class Ephem(Speaker):
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
    DEFAULT_ORDER = 8

    def __init__(self, orbits, method=None, order=None):
        self._orbits = list(sorted(orbits, key=lambda x: x.date))
        self.method = self.LAGRANGE if method is None else method
        self.order = order if isinstance(order, int) else self.DEFAULT_ORDER

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

    def iter(self, start=None, stop=None, step=None, strict=True, **kwargs):
        """Ephemeris generator based on the data of this one, but with different dates

        If an argument is set to ``None`` it will keep the same property as the generating ephemeris

        Keyword Arguments:
            start (Date or None): Date of the first point
            stop (Date, timedelta or None): Date of the last point
            step (timedelta or None): Step to use during the computation. Use the same step as
                `self` if `None`
            strict (bool): If True, the method will return a ValueError if ``start`` or ``stop`` is
                not in the range of the ephemeris. If False, it will take the closest point in each
                case.
        Yield:
            :py:class:`Orbit`:

        Examples:

        .. code-block:: python

            # In the examples below, we consider the 'ephem' object to be an ephemeris starting on
            # 2017-01-01 00:00:00 UTC and ending and 2017-01-02 00:00:00 UTC (included) with a fixed
            # step of 3 minutes.

            # These two calls will generate exactly the same points starting at 00:00 and ending at
            # 12:00, as 12:02 does not fall on a date included in the original 'ephem' object.
            ephem.iter(stop=Date(2017, 1, 1, 12))
            ephem.iter(stop=Date(2017, 1, 1, 12, 2))

            # Similarly, these calls will generate the same points starting at 12:00 and ending at
            # 00:00, as 11:58 does not fall on date included in the 'ephem' object.
            ephem.iter(start=Date(2017, 1, 1, 11, 58))
            ephem.iter(start=Date(2017, 1, 1, 12))

            # This call will generate an ephemeris, wich is a subpart of the initial one
            ephem.iter(start=Date(2017, 1, 1, 8), stop=Date(2017, 1, 1, 16))
        """

        # To allow for a loose control of the dates we have to compute
        # the real starting date of the iterator
        real_start = None

        if start is None:
            start = self.start
        elif start < self.start:
            if strict:
                raise ValueError("Start date not in range")
            else:
                real_start = self.start

        if stop is None:
            stop = self.stop
        else:
            if isinstance(stop, timedelta):
                stop = start + stop
            if stop > self.stop:
                if strict:
                    raise ValueError("Stop date not in range")
                else:
                    stop = self.stop

        if real_start is not None:
            start = real_start

        listeners = kwargs.get('listeners', [])

        if step is None:

            # The step stays the same as the original ephemeris
            for orb in self:

                if orb.date < start:
                    continue

                if orb.date > stop:
                    break

                # Listeners
                for listen_orb in self.listen(orb, listeners):
                    yield listen_orb

                # yield a copy of the recorded orbit to avoid later modification
                # which could have dire consequences
                yield orb.copy()
        else:
            # create as ephemeris with a different step than the original
            date = start
            while date <= stop:

                orb = self.propagate(date)

                # Listeners
                for listen_orb in self.listen(orb, listeners):
                    yield listen_orb

                yield orb
                date += step

    def ephemeris(self, *args, **kwargs):
        """Same as :py:meth:`self.iter() <iter>`

        Implemented to expose the same methods as :py:class:`Orbit`
        """
        return self.iter(*args, **kwargs)

    def ephem(self, *args, **kwargs):
        """Create an Ephem object which is a subset of this one

        Take the same keyword arguments as :py:meth:`ephemeris`

        Return:
            Ephem:
        """

        return self.__class__(self.ephemeris(*args, **kwargs))

    def copy(self, *, form=None, frame=None):
        """Create a deep copy of the ephemeris, and allow frame and form changing
        """
        new = self.ephem()
        if frame:
            new.frame = frame
        if form:
            new.form = form

        return new

    def as_frame(self, name, **kwargs):  # pragma: no cover
        """Register the Ephem object as a frame

        see :py:func:`beyond.frames.frames.orbit2frame` for details of the arguments
        """
        return orbit2frame(name, self, **kwargs)
