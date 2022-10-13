"""Generic interpolations
"""

import numpy as np


class Interp:
    """Linear or Lagrangian interpolation

    The constructed object is callable

    Example:

        .. code-block:: python

            f = Interp(xs, ys, "lagrange", 8)
            y1 = f(x1)  # interpolated value at x1
    """

    LINEAR = "linear"
    LAGRANGE = "lagrange"

    def __init__(self, xs, ys, method, order=None):
        """
        Args:
            xs (numpy.array) : 1-D array of real values. Shall be monotonically increasing.
            ys (numpy.array) : 1-D or 2-D array of real values
            method (str) : Selection of the interpolation method
                Either 'linear' or 'lagrange'.
            order (int) : Order of the interpolation. Has no effect on
                a linear interpolation.
        """

        method = method.lower()

        if method == self.LAGRANGE and order is None:  # pragma: no cover
            raise TypeError("An order shall be defined for a Lagrange interpolation")

        self.order = order

        if not all(x0 < x1 for x0, x1 in zip(xs, xs[1:])):  # pragma: no cover
            raise ValueError("xs is not monotonically increasing")

        self.xs = np.asarray(xs)
        self.ys = np.asarray(ys)
        self.method = method

    def __call__(self, x):
        """Compute interpolation at x

        Args:
            x (float) : value to interpolate to
        Return:
            numpy.array :
        """

        if not (self.xs[0] <= x <= self.xs[-1]):
            raise ValueError(f"x is not in range [{self.xs[0]}, {self.xs[-1]}]. x={x}")

        if self.method == self.LINEAR:
            func = self._linear
        elif self.method == self.LAGRANGE:
            func = self._lagrange
        else:  # pragma: no cover
            raise ValueError("Unknown interpolation method", self.method)

        return func(x)

    def _prev_idx(self, x):
        """Binary search of the step just before the desired value."""

        prev_idx = 0
        xs = self.xs

        while True:
            l = len(xs)
            if l == 1:
                break
            k = l // 2

            if x > xs[k]:
                prev_idx += k
                xs = xs[k:]
            else:
                xs = xs[:k]

        return prev_idx

    def _linear(self, x):
        """Linear interpolation"""

        prev_idx = self._prev_idx(x)

        x0, x1 = self.xs[prev_idx : prev_idx + 2]
        y0, y1 = self.ys[prev_idx : prev_idx + 2]

        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

    def _lagrange(self, x):

        prev_idx = self._prev_idx(x)

        stop = prev_idx + 1 + self.order // 2 + self.order % 2
        start = prev_idx - self.order // 2 + 1

        # Edge cases
        if stop >= len(self.ys):
            start -= stop - len(self.ys)
        elif start < 0:
            stop -= start
            start = 0

        # selection of the subset of data, of length 'order' around the desired value
        xs = self.xs[start:stop]
        ys = self.ys[start:stop]

        if len(ys) != self.order:  # pragma: no cover
            raise ValueError(
                f"len={len(ys)} < order={self.order} : impossible to interpolate"
            )

        # Lagrange polynomial
        #        k
        # L(x) = Σ y_j * l_j(x)
        #        j=0
        #
        # l_j(x) = Π (x - x_m) / (x_j - x_m)
        #     0 <= m <= k
        #        m != j

        # x_m and x_j are arrays of shape (k, k).
        # axis=0 is indexed by j, axis=1 by m

        x_m = np.tile(xs, self.order).reshape(self.order, self.order)
        x_j = np.repeat(np.diag(x_m), self.order, axis=0).reshape(
            self.order, self.order
        )

        # mask used in the product to discard the m = j value
        mask = ~np.identity(self.order, dtype=bool)

        l_j = (
            ((x - x_m[mask]) / (x_j[mask] - x_m[mask]))
            .reshape(self.order, self.order - 1)
            .prod(axis=1)
        )
        return l_j @ ys


class DatedInterp(Interp):
    """Interpolation for time series"""

    def __init__(self, dates, ys, method, order=None):
        """
        Args:
            dates (list of Date) : 1-D array of dates. Shall be monotonically increasing.
            ys (numpy.array) : N-D array of real values
            method (str) : Selection of the interpolation method
                Either 'linear' or 'lagrange'.
            order (int) : Order of the interpolation. Has no effect on
                a linear interpolation.
        """
        self.dates = dates
        xs = np.asarray([x._mjd for x in dates])
        super().__init__(xs, ys, method, order)

    def __call__(self, date):
        """Compute interpolation at a given date

        Args:
            date (Date) : Date to interpolate to
        Return:
            numpy.array :
        """
        try:
            return super().__call__(date._mjd)
        except ValueError as e:
            # Catching the "out of bound" exception to convert the message
            # in terms of dates
            if str(e).startswith("x is not in range"):
                raise ValueError(
                    f"Date '{date}' not in range [{self.dates[0]}, {self.dates[-1]}]"
                ) from e
            else:
                raise e
