
from numpy import sqrt, zeros
from datetime import timedelta
from collections import namedtuple

from .base import NumericalPropagator
from ..utils import Date
from ..env.jpl import get_body


Obj = namedtuple("Obj", ('orbit', 'mass'))


class Kepler(NumericalPropagator):

    G = 6.67408e-11  # in m³.s⁻².kg⁻¹

    RK4 = 'rk4'
    EULER = 'euler'

    masses = {
        'Sun': 1.98855e30,
        'Earth': 5.97237e24,
        'Moon': 7.342e22,
        'Mars': 6.4171e23,
        'Jupiter': 1.8986e27,
    }

    def __init__(self, step, method=RK4, bodies=('Earth', 'Moon', 'Sun')):
        self.method = method
        self.bodies = [Obj(get_body(body, Date.now()), self.masses[body]) for body in bodies]
        self.step = step

    def dgl(self, date, orb):

        new_body = orb.__class__(date, zeros(6), "cartesian", orb.frame, self.__class__)
        new_body.date = date
        new_body[:3] = orb[3:]

        for body in self.bodies:
            orb_body = body.orbit.propagate(date)
            orb_body.frame = orb.frame
            diff = orb_body[:3] - orb[:3]
            norm = sqrt(sum(diff ** 2)) ** 3
            new_body[3:] += self.G * body.mass * diff / norm  # * step.total_seconds()

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

    def _iter(self, start, stop, step):
        orb = self.orbit

        for date in Date.range(start, stop, step):
            method = getattr(self, self.method)
            orb = method(orb, self.step)
            yield orb.copy()
