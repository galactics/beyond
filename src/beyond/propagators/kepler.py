"""Keplerian motion numerical propagator

"""

from numpy import sqrt, zeros

from ..constants import G
from .base import NumericalPropagator
from ..utils import Date


class Kepler(NumericalPropagator):

    RK4 = 'rk4'
    EULER = 'euler'

    def __init__(self, step, bodies, method=RK4):
        """
        Args:
            step (datetime.timedelta): Step size of the propagator
            bodies (tuple): List of bodies to take into account
            method (str): Integration method (:py:attr:`RK4` or :py:attr:`EULER`)
        """

        self.step = step
        self.bodies = bodies if isinstance(bodies, (list, tuple)) else [bodies]
        self.method = method

    @property
    def orbit(self):
        return self._orbit if hasattr(self, '_orbit') else None

    @orbit.setter
    def orbit(self, orbit):
        self._orbit = orbit.copy(form="cartesian", frame="EME2000")

    def dgl(self, date, orb):

        new_body = orb.__class__(date, zeros(6), "cartesian", orb.frame, self.__class__)
        new_body.date = date
        new_body[:3] = orb[3:]

        for body in self.bodies:
            orb_body = body.propagate(date)
            orb_body.frame = orb.frame
            diff = orb_body[:3] - orb[:3]
            norm = sqrt(sum(diff ** 2)) ** 3
            new_body[3:] += G * body.mass * diff / norm  # * step.total_seconds()

        return new_body

    def rk4(self, orb, h):
        """Application of the Runge-Kutta 4th order method of iteration
        """

        y_n = orb.copy()

        k1 = self.dgl(y_n.date, y_n)
        k2 = self.dgl(y_n.date + h / 2, y_n + k1 * h.total_seconds() / 2)
        k3 = self.dgl(y_n.date + h / 2, y_n + k2 * h.total_seconds() / 2)
        k4 = self.dgl(y_n.date + h, y_n + k3 * h.total_seconds())

        # This is the y_n+1 value
        y_n_1 = y_n + h.total_seconds() / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        y_n_1.date = y_n.date + h

        return y_n_1

    def euler(self, orb, h):
        y_n = orb.copy()
        y_n_1 = y_n + h.total_seconds() * self.dgl(y_n.date, y_n)
        y_n_1.date = y_n.date + h

        return y_n_1

    def _iter(self, start, stop, step, **kwargs):
        orb = self.orbit

        yield orb.copy()
        for date in Date.range(start, stop, step, inclusive=kwargs.get("inclusive", False)):
            orb = getattr(self, self.method)(orb, self.step)
            yield orb.copy()
