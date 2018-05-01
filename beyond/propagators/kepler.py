from numpy import sqrt, zeros

from ..constants import G
from .base import NumericalPropagator
from ..dates import Date, timedelta


class Kepler(NumericalPropagator):
    """Keplerian motion numerical propagator

    This propagator provide two distinct methods of propagation ``euler`` and ``rk4``.
    ``rk4`` stands for `Runge-Kutta of order 4
    <https://en.wikipedia.org/wiki/Runge%E2%80%93Kutta_methods>`__.
    """

    RK4 = 'rk4'
    EULER = 'euler'
    FRAME = "EME2000"

    SPEAKER_MODE = "iterative"

    def __init__(self, step, bodies, method=RK4, frame=FRAME):
        """
        Args:
            step (datetime.timedelta): Step size of the propagator
            bodies (tuple): List of bodies to take into account
            method (str): Integration method (:py:attr:`RK4` or :py:attr:`EULER`)
            frame (str): Frame to use for the propagation
        """

        self.step = step
        self.bodies = bodies if isinstance(bodies, (list, tuple)) else [bodies]
        self.method = method.lower()
        self.frame = frame

    def copy(self):
        return self.__class__(self.step, self.bodies, self.method)

    @property
    def orbit(self):
        return self._orbit if hasattr(self, '_orbit') else None

    @orbit.setter
    def orbit(self, orbit):
        self._orbit = orbit.copy(form="cartesian", frame=self.frame)

    def _newton(self, orb, step):
        """Newton's Law of Universal Gravitation
        """

        date = orb.date + step

        new_body = zeros(6)
        new_body[:3] = orb[3:]

        for body in self.bodies:
            # retrieve the position of the body at the given date
            orb_body = body.propagate(date)
            orb_body.frame = orb.frame

            # Compute induced attraction to the object of interest
            diff = orb_body[:3] - orb[:3]
            norm = sqrt(sum(diff ** 2)) ** 3
            new_body[3:] += G * body.mass * diff / norm

        return new_body

    def _method(self, orb, step):
        """Method switch depending on the self._method value
        """
        return getattr(self, "_%s" % self.method)(orb, step)

    def _rk4(self, orb, step):
        """Application of the Runge-Kutta 4th order (RK4) method of iteration

        Args:
            orb (Orbit): Orbit to propagate to the next iteration
            step (~datetime.timedelta): step size of the iteration
        Return:
            Orbit
        """

        y_n = orb.copy()

        k1 = self._newton(y_n, timedelta(0))
        k2 = self._newton(y_n + k1 * step.total_seconds() / 2, step / 2)
        k3 = self._newton(y_n + k2 * step.total_seconds() / 2, step / 2)
        k4 = self._newton(y_n + k3 * step.total_seconds(), step)

        # This is the y_n+1 value
        y_n_1 = y_n + step.total_seconds() / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        y_n_1.date = y_n.date + step

        for man in self.orbit.maneuvers:
            if orb.date < man.date <= orb.date + step:
                y_n_1[3:] += man.dv(y_n_1)

        return y_n_1

    def _euler(self, orb, step):
        """Simple step propagator
        """
        y_n = orb.copy()
        y_n_1 = y_n + step.total_seconds() * self._newton(y_n, step)
        y_n_1.date = y_n.date + step

        return y_n_1

    def _iter(self, start, stop, step, **kwargs):

        orb = self.orbit

        if start > orb.date:
            # Propagation of the current orbit to the starting point requested
            for date in Date.range(orb.date + self.step, start, self.step):
                orb = self._method(orb, self.step)

            # Compute the orbit at the real begining of the requested range
            orb = self._method(orb, start - orb.date)

        for date in Date.range(start, stop, step):
            yield orb
            orb = self._method(orb, step)

        # Instead of using Date(inclusive=True), we compute the last point manually,
        # allowing to have a different step size to fit the desired stop date
        yield self._method(orb, stop - orb.date)
