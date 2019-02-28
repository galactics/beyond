from numpy import sqrt, zeros, array
from collections import namedtuple
import logging

from ..constants import G
from .base import NumericalPropagator
from ..dates import Date, timedelta


__all__ = ['Kepler', 'SOIPropagator']


log = logging.getLogger(__name__)


class Kepler(NumericalPropagator):
    """Keplerian motion numerical propagator

    This propagator provide three methods of propagation ``euler``, ``rk4`` and
    ``dopri``
    See `Runge-Kutta methods <https://en.wikipedia.org/wiki/Runge%E2%80%93Kutta_methods>`__
    for details.
    """

    RK4 = 'rk4'
    EULER = 'euler'
    DOPRI = 'dopri'
    FRAME = "EME2000"

    SPEAKER_MODE = "iterative"

    # Butcher tableau of the different methods available
    BUTCHER = {
        EULER: {
            "a": array([]),
            "b": array([1]),
            "c": array([0])
        },
        RK4: {
            "a": [
                [],
                array([1/2]),
                array([0, 1/2]),
                array([0, 0, 1])
            ],
            "b" : array([1/6, 1/3, 1/3, 1/6]),
            "c" : array([0, 1/2, 1/2, 1]),
        },
        DOPRI: {
            "a": [
                    [],
                    array([1/5]),
                    array([3/40, 9/40]),
                    array([44/45, -56/15, 32/9]),
                    array([19372/6561, -25360/2187, 64448/6561, -212/729]),
                    array([9017/3168, -355/33, 46732/5247, 49/176, -5103/18656]),
                    array([35/384, 0, 500/1113, 125/192, -2187/6784, 11/84])
                ],
            'b': array([35/384, 0, 500/1113, 125/192, -2187/6784, 11/84, 0 ]),
            'b_star': array([5179/57600, 0, 7571/16695, 393/640, -92097/339200, 187/2100, 1/40]),
            'c': array([0, 1/5, 3/10, 4/5, 8/9, 1, 1]),
        }
    }

    def __init__(self, step, bodies, *, method=RK4, frame=FRAME):
        """
        Args:
            step (datetime.timedelta): Step size of the propagator
            bodies (tuple): List of bodies to take into account
            method (str): Integration method (:py:attr:`DOPRI`, :py:attr:`RK4` or :py:attr:`EULER`)
            frame (str): Frame to use for the propagation
        """

        self.step = step
        self.bodies = bodies if isinstance(bodies, (list, tuple)) else [bodies]
        self.method = method.lower()
        self.frame = frame

    def copy(self):
        return self.__class__(
            self.step,
            self.bodies,
            method=self.method,
            frame=self.frame
        )

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

    def _make_step(self, orb, step):
        """Compute the next step with the selected method
        """

        method = self.BUTCHER[self.method]
        a, b, c = method['a'], method['b'], method['c']

        y_n = orb.copy()
        ks = [self._newton(y_n, timedelta(0))]

        for a, c in zip(a[1:], c[1:]):
            k_plus1 = self._newton(y_n + a @ ks * step.total_seconds(), step * c)
            ks.append(k_plus1)

        y_n_1 = y_n + step.total_seconds() * b @ ks
        y_n_1.date = y_n.date + step

        # Error estimation, in cases where adaptively methods are used
        # if 'b_star' in method:
        #     error = step.total_seconds() * (b - method['b_star']) @ ks

        for man in self.orbit.maneuvers:
            if man.check(orb, step):
                log.debug("Applying maneuver at {} ({})".format(man.date, man.comment))
                y_n_1[3:] += man.dv(y_n_1)

        return y_n_1

    def _iter(self, **kwargs):

        start = kwargs.get('start', self.orbit.date)
        stop = kwargs.get('stop')
        step = kwargs.get('step', self.step)

        orb = self.orbit

        if start > orb.date:
            # Propagation of the current orbit to the starting point requested
            for date in Date.range(orb.date + self.step, start, self.step):
                orb = self._make_step(orb, self.step)

            # Compute the orbit at the real beginning of the requested range
            orb = self._make_step(orb, start - orb.date)

        for date in Date.range(start, stop, step):
            yield orb
            orb = self._make_step(orb, step)

        # Instead of using Date(inclusive=True), we compute the last point manually,
        # allowing to have a different step size to fit the desired stop date
        yield self._make_step(orb, stop - orb.date)


SOI = namedtuple('SOI', 'radius frame')


class SOIPropagator(Kepler):
    """Kepler propagator capable of switching between the Sphere of Influence of
    different solar system bodies
    """

    SOI = {
        'Mercury': SOI(112408000, 'Mercury'),
        'Venus': SOI(616270000, 'Venus'),
        'Earth': SOI(924642000, 'EME2000'),
        'Moon': SOI(66168000, 'Moon'),
        'Mars': SOI(577223000, 'Mars'),
        'Jupiter': SOI(48219667000, 'Jupiter'),
        'Saturn': SOI(54800713000, 'Saturn'),
        'Uranus': SOI(51839589000, 'Uranus'),
        'Neptune': SOI(84758736000, 'Neptune')
    }

    def __init__(self, central_step, alt_step, central, alt, *, method=Kepler.RK4, frame=None):
        """
        Args:
            central_step (timedelta): Step to use in computation when only the
                central body is taken into account
            alt_step (timedelta): Step to use in computations under the
                influence of an alternate body
            central (Body): Central body
            alt (list of Body): Objects to potentially use
            method (str): Method of extrapolation (see :py:class:`Kepler`)
            frame (str): Frame of the resulting extrapolation. If ``None``, the
                result will change frame depending on the sphere of influence
                it is in
        """

        self.alt_step = alt_step
        self.central_step = central_step
        self.central = central
        self.alt = alt if isinstance(alt, (list, tuple)) else [alt]
        self.method = method
        self.out_frame = frame
        self.active = central.name

    @property
    def orbit(self):
        return self._orbit if hasattr(self, '_orbit') else None

    @orbit.setter
    def orbit(self, orbit):
        soi = self._soi(orbit)
        self._change_soi(soi)
        self._orbit = orbit.copy(form="cartesian", frame=self.frame)

    def copy(self):
        return self.__class__(
            self.central_step,
            self.alt_step,
            self.central,
            self.alt,
            method=self.method,
            frame=self.out_frame
        )

    def _soi(self, orb):
        """Evaluate the need for SOI transition, by comparing the radial distance
        between the considered body and the spacecraft

        If therer is no body in sight, default to central body.
        """

        for body in self.alt:
            soi = self.SOI[body.name]
            sph = orb.copy(frame=soi.frame, form='spherical')
            if sph.r < soi.radius:
                active = body
                break
        else:
            active = self.central

        return active

    def _change_soi(self, body):
        """Modify the inner parameters of the Kepler propagator in order to place
        the spacecraft in the right Sphere of Influence
        """

        if body == self.central:
            self.bodies = [self.central]
            self.step = self.central_step
            self.active = self.central.name
            self.frame = self.central.name
        else:
            soi = self.SOI[body.name]
            self.bodies = [body]
            self.step = self.alt_step
            self.active = body.name
            self.frame = soi.frame

    def _iter(self, start=None, stop=None, step=None, **kwargs):

        orb = self.orbit
        soi = self._soi(orb)

        while orb.date < stop:

            current = soi

            # At each step of the computation, evaluate the need of SOI transition.
            # If needed, stop the iteration, change the parameters of the
            # propagation (frame, step, central body), then start it again from the
            # last point
            for orb in super()._iter(start=start, stop=stop, step=self.step, **kwargs):
                yield orb.copy(frame=self.out_frame)
                soi = self._soi(orb)
                if soi != current:
                    break

            start = orb.date
            self.orbit = orb

            if start < stop:
                log.debug("SOI change {} => {} at {}".format(current, soi, orb.date))
