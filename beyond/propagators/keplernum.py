from numpy import zeros, array, sign, linalg

from .base import NumericalPropagator
from ..orbits.ephem import Ephem
from ..orbits.man import ImpulsiveMan, ContinuousMan

__all__ = ["KeplerNum"]


class KeplerNum(NumericalPropagator):
    """Keplerian motion numerical propagator

    This propagator provide three methods of propagation ``euler``, ``rk4`` and
    ``dopri``
    See `Runge-Kutta methods <https://en.wikipedia.org/wiki/Runge%E2%80%93Kutta_methods>`__
    for details.

    For adaptive step size, the highest order is used to compute the next
    state, and the lowest to determine the error and adapt the stepsize.
    For example RKF54 use order 5 for state computation, and order 4 for
    error estimation.
    """

    RK4 = "rk4"
    """Runge-Kutta 4th order fixed stepsize integrator"""

    RKF54 = "rkf54"
    """Runge-Kutta 5th order adaptive stepsize integrator"""

    EULER = "euler"
    """Euler fixed-step integrator"""

    DOPRI54 = "dopri54"
    """Dormand-Prince 5th order adaptive stepsize integrator"""

    FRAME = "EME2000"

    # Butcher tableau of the different methods available
    BUTCHER = {
        EULER: {"a": array([]), "b": array([1]), "c": array([0])},
        RK4: {
            "a": [[], array([1 / 2]), array([0, 1 / 2]), array([0, 0, 1])],
            "b": array([1 / 6, 1 / 3, 1 / 3, 1 / 6]),
            "c": array([0, 1 / 2, 1 / 2, 1]),
        },
        RKF54: {
            "a": [
                [],
                array([1 / 4]),
                array([3 / 32, 9 / 32]),
                array([1932 / 2197, -7200 / 2197, 7296 / 2197]),
                array([439 / 216, -8, 3680 / 513, -845 / 4104]),
                array([-8 / 27, 2, -3544 / 2565, 1859 / 4104, -11 / 40]),
            ],
            "b": array([16 / 135, 0, 6656 / 12825, 28561 / 56430, -9 / 50, 2 / 55]),
            "b_star": array([25 / 216, 0, 1408 / 2565, 2197 / 4104, -1 / 5, 0]),
            "c": array([0, 1 / 4, 3 / 8, 12 / 13, 1, 1 / 2]),
        },
        DOPRI54: {
            "a": [
                [],
                array([1 / 5]),
                array([3 / 40, 9 / 40]),
                array([44 / 45, -56 / 15, 32 / 9]),
                array([19372 / 6561, -25360 / 2187, 64448 / 6561, -212 / 729]),
                array([9017 / 3168, -355 / 33, 46732 / 5247, 49 / 176, -5103 / 18656]),
                array([35 / 384, 0, 500 / 1113, 125 / 192, -2187 / 6784, 11 / 84]),
            ],
            "b": array([35 / 384, 0, 500 / 1113, 125 / 192, -2187 / 6784, 11 / 84, 0]),
            "b_star": array(
                [
                    5179 / 57600,
                    0,
                    7571 / 16695,
                    393 / 640,
                    -92097 / 339200,
                    187 / 2100,
                    1 / 40,
                ]
            ),
            "c": array([0, 1 / 5, 3 / 10, 4 / 5, 8 / 9, 1, 1]),
        },
    }

    def __init__(self, step, bodies, *, method=RK4, frame=FRAME, tol=1e-3):
        """
        Args:
            step (datetime.timedelta): Step size of the propagator
            bodies (tuple): List of bodies to take into account
            method (str): Integration method (see class attributes)
            frame (str): Frame to use for the propagation
            tol (float): Error tolerance for adaptive stepsize methods
        """

        self.step = step
        self.bodies = bodies if isinstance(bodies, (list, tuple)) else [bodies]
        self.method = method.lower()
        self.frame = frame
        self.tol = tol

    def copy(self):
        return self.__class__(
            self.step, self.bodies, method=self.method, frame=self.frame
        )

    @property
    def orbit(self):
        return self._orbit if hasattr(self, "_orbit") else None

    @orbit.setter
    def orbit(self, orbit):
        self._orbit = orbit.copy(form="cartesian", frame=self.frame)

    @property
    def butcher(self):
        return self.BUTCHER[self.method]

    def _accel(self, orb):
        """Newton's Law of Universal Gravitation"""

        new_body = zeros(6)
        new_body[:3] = orb[3:]

        for body in self.bodies:
            # retrieve the position of the body at the given date
            orb_body = body.propagate(orb.date)
            orb_body.frame = orb.frame

            # Compute induced attraction to the object of interest
            diff = orb_body[:3] - orb[:3]
            norm = linalg.norm(diff) ** 3
            new_body[3:] += body.µ * diff / norm

        for man in self.orbit.maneuvers:
            if isinstance(man, ContinuousMan) and man.check(orb.date):
                new_body[3:] += man.accel(orb)

        return new_body

    def _make_step(self, orb, step):
        """Compute the next step with the selected method"""

        aa, bb, cc = self.butcher["a"], self.butcher["b"], self.butcher["c"]
        b_star = self.butcher.get("b_star")

        y_n = orb.copy()

        MAX_ITER = 10

        for i in range(MAX_ITER):

            ks = [self._accel(y_n)]
            i += 1
            for a, c in zip(aa[1:], cc[1:]):
                y_n_prime = y_n + a @ ks * step.total_seconds()
                y_n_prime.date += step * c
                ks.append(self._accel(y_n_prime))

            y_n_1 = y_n + step.total_seconds() * bb @ ks
            y_n_1.date = y_n.date + step

            # Error estimation, in cases where adaptive stepsize methods are used
            if b_star is None:
                # This is not an adaptive stepsize method, there is no need to iterate
                # here
                break

            error = step.total_seconds() * (bb - self.butcher["b_star"]) @ ks

            p_error = linalg.norm(error[:3])
            # v_eps = linalg.norm(error[3:])

            if p_error <= self.tol:
                # The target accuracy is met, the current step size is sufficient
                break

            # Modify the step size
            step = min(
                self.step, step * (self.tol / (2 * p_error)) ** (1 / (len(bb) - 1))
            )
        else:
            raise RuntimeError(
                "{} : No convergence in step size after {} iterations.".format(
                    self.method, MAX_ITER
                )
            )

        for man in self.orbit.maneuvers:
            if isinstance(man, ImpulsiveMan) and man.check(orb.date, step):
                y_n_1[3:] += man.dv(y_n_1, step=step)

        return step, y_n_1

    def _iter(self, **kwargs):

        dates = kwargs.get("dates")

        if dates is not None:
            start = dates.start
            stop = dates.stop
            step = None
        else:
            start = kwargs.get("start", self.orbit.date)
            stop = kwargs.get("stop")
            step = kwargs.get("step")

        listeners = kwargs.get("listeners", [])

        # Not very clean !
        if step is self.step:
            step = None

        orb = self.orbit

        if start != orb.date:
            # Position the start of the real extrapolation when requested
            # by extrapolation or retropolation

            # Step size for initial extrapolation or retropolation
            _step = sign((start - orb.date).total_seconds()) * self.step

            ephem = [orb]

            date = orb.date
            mname = "__lt__" if _step.total_seconds() > 0 else "__gt__"
            while getattr(date, mname)(start):
                real_step, orb = self._make_step(orb, _step)
                ephem.append(orb)
                date += real_step

            # Provide enough extra steps to allow Ephem to interpolate
            # with order DEFAULT_ORDER
            for i in range(Ephem.DEFAULT_ORDER - len(ephem)):
                real_step, orb = self._make_step(orb, _step)
                ephem.append(orb)

            ephem = Ephem(ephem)
            # Interpolation of the ephemeris to get the desired start date
            orb = ephem.propagate(start)

        # In order to compute the propagation with the reference step size
        # (ie self.step), but give the result at the requested step size
        # (ie step), we use an Ephem object for interpolation
        ephem = [orb]

        date = start
        while date < stop:
            real_step, orb = self._make_step(orb, self.step)
            ephem.append(orb)
            date += real_step

        ephem = Ephem(ephem)

        if kwargs.get("real_steps", False):
            ephem_iter = ephem.iter(dates=dates, listeners=listeners)
        else:
            ephem_iter = ephem.iter(dates=dates, step=step, listeners=listeners)

        for orb in ephem_iter:
            yield orb.as_orbit(self.copy())
