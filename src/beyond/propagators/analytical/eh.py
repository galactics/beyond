import logging
import numpy as np

from ...dates import timedelta
from ..base import AnalyticalPropagator
from ...orbits import MeanOrbit, StateVector

log = logging.getLogger(__name__)


class EcksteinHechler(AnalyticalPropagator):
    """Eckstein-Hechler propagator

    This analytical propagator takes into account the central force and
    zonal harmonics up to J6.
    This propagator is suited for orbits that are nearly circular (e < 0.1)
    and does not work for orbits near the critical inclination (63.43 and 116.57
    deg) or equatorial (both direct or retrograde).

    Based on Eckstein, M. C., and F. Hechler. "A reliable Derivation of the
    perturbations due to any zonal and tesseral harmonics of the geopotential
    for nearly-circular satellite orbits" ESRO-SR-13, 1970.

    While the original publication uses all terms up to degree 9 and order 6,
    this implementation is limited to zonal harmonics up to degree 6.

    This is an adaptation of the Scilab implementation present in `Celestlab
    <https://atoms.scilab.org/toolboxes/celestlab>`__, developped by A. Lamy.
    """

    J = np.array(
        [
            1,
            0,
            1.0826266835531513e-03,
            -2.5326564853322355e-06,
            -1.6196215913670001e-06,
            -2.2729608286869828e-07,
            5.4068123910708486e-07,
        ]
    )
    mu = 3.986004415e14
    re = 6378136.3
    FRAME = "CIRF"

    def __init__(self, osculating=True):
        """
        Args:
            osculating (bool) : When True the propagator will provide osculating
                elements, otherwise it will provide mean elements.
        """
        self.osculating = osculating

    @property
    def orbit(self):
        return self._orbit if hasattr(self, "_orbit") else None

    @orbit.setter
    def orbit(self, orb):
        if not isinstance(orb, MeanOrbit):  # pragma: no cover
            raise TypeError(f"MeanOrbit expected, got {orb.__class__.__name__}")

        self._orbit = orb.copy(form="mean_circular", frame=self.FRAME)

    def propagate(self, date):
        """
        Args:
            date (Date or timedelta)
        Return:
            :py:class:`~beyond.orbits.statevector.StateVector` if ``osculating == True``,
                :py:class:`~beyond.orbits.orbit.MeanOrbit` otherwise : Orbit at the given date
        """

        if isinstance(date, timedelta):
            date = self.orbit.date + date

        t = (date - self.orbit.date).total_seconds()

        a0, ex0, ey0, i0, Ω0, α0 = self.orbit
        G = -self.J * (self.re / a0) ** np.arange(7)

        n0 = a0**-1.5 * self.mu**0.5

        c = np.cos(i0)
        beta = np.sin(i0)
        beta2, beta4, beta6 = beta ** np.arange(2, 8, 2)

        e = np.sqrt(ex0**2 + ey0**2)

        if e > 0.1:  # pragma: no cover
            raise RuntimeError(f"Eccentricity too large : {e:0.2e} > 0.1")
        elif e > 5e-3:  # pragma: no cover
            log.warning(f"Eccentricity too large for good precision : {e:0.2e} > 5e-3")
        if beta2 < 1e-10:  # pragma: no cover
            raise RuntimeError("Nearly equatorial orbit")
        elif abs(beta2 - 4 / 5) < 1e-3:  # pragma: no cover
            raise RuntimeError("Nearly critical orbit")

        #######################
        # Mean semi major-axis
        #######################
        mean_a = a0

        #######################
        # Mean Eccentricity vector
        #######################
        omega_prime = -0.75 * G[2] * (4 - 5 * beta2)
        omega_second = 1.5 * (
            5 * G[4] * (1 - 31 / 8 * beta2 + 49 / 16 * beta4) - 35 / 4 * G[6]
        )
        xi_star = (omega_prime + omega_second) * n0 * t
        cx = np.cos(xi_star)
        sx = np.sin(xi_star)

        tmp_eps1 = (3 / 32) / omega_prime
        eps1 = tmp_eps1 * G[4] * beta2 * (30 - 35 * beta2) - 175 * tmp_eps1 * G[
            6
        ] * beta2 * (1 - 3 * beta2 + (33 / 16) * beta4)
        tmp_eps2 = (3 / 8) * beta / omega_prime
        eps2 = tmp_eps2 * G[3] * (4 - 5 * beta2) - tmp_eps2 * G[5] * (
            10 - 35 * beta2 + 26.25 * beta4
        )

        mean_ex = ex0 * cx - (1 - eps1) * (ey0 - eps2) * sx
        mean_ey = (1 + eps1) * ex0 * sx + (ey0 - eps2) * cx + eps2

        #######################
        # Mean Inclination
        #######################
        mean_i = i0

        #######################
        # Mean Right Ascension of Ascending Node
        #######################
        tmp_Ω = (
            1.5 * G[2]
            - 2.25 * (G[2] ** 2) * (2.5 - (19 / 6) * beta2)
            + (15 / 16) * G[4] * (7 * beta2 - 4)
            + (105 / 32) * G[6] * (2 - 9 * beta2 + (33 / 4) * beta4)
        )
        mean_Ω = (Ω0 + tmp_Ω * c * n0 * t) % (2 * np.pi)

        #######################
        # Mean Argument of Latitude
        #######################
        delta_α = 1 - 1.5 * G[2] * (3 - 4 * beta2)
        tmp_α = (
            delta_α
            + 2.25 * (G[2] ** 2) * (9 - (263 / 12) * beta2 + (341 / 24) * beta4)
            + (15 / 16) * G[4] * (8 - 31 * beta2 + 24.5 * beta4)
            + (105 / 32)
            * G[6]
            * (-(10 / 3) + 25 * beta2 - 48.75 * beta4 + 27.5 * beta6)
        )
        mean_α = (α0 + tmp_α * n0 * t) % (2 * np.pi)

        if not self.osculating:
            return MeanOrbit(
                [
                    mean_a,
                    mean_ex,
                    mean_ey,
                    mean_i,
                    mean_Ω,
                    mean_α,
                ],
                date,
                "mean_circular",
                self.FRAME,
                self.copy(),
            )
        else:
            mα_r = mean_α * np.arange(1, 7)

            cosα = np.cos(mα_r)
            sinα = np.sin(mα_r)

            qq = -1.5 * G[2] / delta_α
            qh = 3 * (mean_ey - eps2) / (8 * omega_prime)
            ql = 3 * mean_ex / (8 * beta * omega_prime)

            ###################
            # Osculating semi major-axis
            ###################
            # Effect of J2 on semi major-axis
            fa2 = (
                (2 - 3.5 * beta2) * mean_ex * cosα[0]
                + (2 - 2.5 * beta2) * mean_ey * sinα[0]
                + beta2 * cosα[1]
                + 3.5 * beta2 * (mean_ex * cosα[2] + mean_ey * sinα[2])
            )
            delta_a = qq * fa2

            # Effect of J2^2 on semi major-axis
            qa22 = 0.75 * (G[2] ** 2) * beta2
            fa22 = 7 * (2 - 3 * beta2) * cosα[1] + beta2 * cosα[3]
            delta_a += qa22 * fa22

            # Effect of J3 on semi major-axis
            qa3 = -0.75 * G[3] * beta
            fa3 = (4 - 5 * beta2) * sinα[0] + (5 / 3) * beta2 * sinα[2]
            delta_a += qa3 * fa3

            # Effect of J4 on semi major-axis
            qa4 = 0.25 * G[4] * beta2
            fa4 = (15 - 17.5 * beta2) * cosα[1] + 4.375 * beta2 * cosα[3]
            delta_a += qa4 * fa4

            # Effect of J5 on semi major-axis
            qa5 = 3.75 * G[5] * beta
            fa5 = (
                (2.625 * beta4 - 3.5 * beta2 + 1) * sinα[0]
                + (7 / 6) * beta2 * (1 - 1.125 * beta2) * sinα[2]
                + (21 / 80) * beta4 * sinα[4]
            )
            delta_a += qa5 * fa5

            # Effect of J6 on semi major-axis
            qa6 = (105 / 16) * G[6] * beta2
            fa6 = (
                (3 * beta2 - 1 - (33 / 16) * beta4) * cosα[1]
                + 0.75 * (1.1 * beta4 - beta2) * cosα[3]
                - (11 / 80) * beta4 * cosα[5]
            )
            delta_a += qa6 * fa6

            ###################
            # Osculating ex
            ###################
            # Effect of J2
            fex2 = (
                (1 - 1.25 * beta2) * cosα[0]
                + 0.5 * (3 - 5 * beta2) * mean_ex * cosα[1]
                + (2 - 1.5 * beta2) * mean_ey * sinα[1]
                + (7 / 12) * beta2 * cosα[2]
                + (17 / 8) * beta2 * (mean_ex * cosα[3] + mean_ey * sinα[3])
            )
            delta_ex = qq * fex2

            ###################
            # Osculating ey
            ###################
            # Effect of J2
            fey2 = (
                (1 - 1.75 * beta2) * sinα[0]
                + (1 - 3 * beta2) * mean_ex * sinα[1]
                + (2 * beta2 - 1.5) * mean_ey * cosα[1]
                + (7 / 12) * beta2 * sinα[2]
                + (17 / 8) * beta2 * (mean_ex * sinα[3] - mean_ey * cosα[3])
            )
            delta_ey = qq * fey2

            ###################
            # Osculating Right Ascension of Ascending Node
            ###################
            # Effect of J2
            qΩ2 = -qq * c
            fΩ2 = (
                3.5 * mean_ex * sinα[0]
                - 2.5 * mean_ey * cosα[0]
                - 0.5 * sinα[1]
                + (7 / 6) * (mean_ey * cosα[2] - mean_ex * sinα[2])
            )
            delta_Ω = qΩ2 * fΩ2

            # Effect of J3
            fΩ3 = G[3] * c * (4 - 15 * beta2)
            delta_Ω += ql * fΩ3

            # Effect of J5
            fΩ5 = 2.5 * G[5] * c * (4 - 42 * beta2 + 52.5 * beta4)
            delta_Ω += -ql * fΩ5

            ###################
            # Osculating Inclination
            ###################
            # Effect of J2
            qi2 = 0.5 * qq * beta * c
            fi2 = (
                mean_ey * sinα[0]
                - mean_ex * cosα[0]
                + cosα[1]
                + (7 / 3) * (mean_ex * cosα[2] + mean_ey * sinα[2])
            )
            delta_i = qi2 * fi2

            # Effect of J3
            fi3 = G[3] * c * (4 - 5 * beta2)
            delta_i += -qh * fi3

            # Effect of J5
            fi5 = 2.5 * G[5] * c * (4 - 14 * beta2 + 10.5 * beta4)
            delta_i += qh * fi5

            ###################
            # Osculating Argument of Latitude
            ###################
            # Effect of J2
            fα2 = (
                (7 - (77 / 8) * beta2) * mean_ex * sinα[0]
                + ((55 / 8) * beta2 - 7.5) * mean_ey * cosα[0]
                + (1.25 * beta2 - 0.5) * sinα[1]
                + ((77 / 24) * beta2 - (7 / 6))
                * (mean_ex * sinα[2] - mean_ey * cosα[2])
            )
            delta_α = qq * fα2

            # Effect of J3
            fα3 = G[3] * (53 * beta2 - 4 - 57.5 * beta4)
            delta_α += ql * fα3

            # Effect of J5
            fα5 = 2.5 * G[5] * (4 - 96 * beta2 + 269.5 * beta4 - 183.75 * beta6)
            delta_α += ql * fα5

            # Final osculating elements computation
            a = mean_a * (1 + delta_a)
            ex = mean_ex + delta_ex
            ey = mean_ey + delta_ey
            i = mean_i + delta_i
            Ω = (mean_Ω + delta_Ω) % (2 * np.pi)
            α = (mean_α + delta_α) % (2 * np.pi)

            return StateVector([a, ex, ey, i, Ω, α], date, "mean_circular", self.FRAME)

    @classmethod
    def fit_statevector(cls, target):
        """Find the MeanOrbit that provide the input StateVector

        Args:
            target (StateVector)
        Return:
            MeanOrbit:
                MeanOrbit object which, when propagated at the same date,
                returns the input StateVector
        """

        MAX_ITER = 10
        p_eps = 10e-4  # 0.1 mm
        v_eps = 10e-7  # 0.1 µm/s

        target = target.copy(frame=cls.FRAME, form="cartesian")

        # Initiate with the osculating value, which is the best initial guess
        current = target.as_orbit(cls(osculating=True))
        log.debug(f"Fitting StateVector with {cls.__name__}")

        for n in range(MAX_ITER):
            log.debug(f"iteration {n}")

            res = current.propagate(target.date).copy(same=target)
            diff = res - target

            log.debug(f"Difference in position {diff.base[:3]}")
            log.debug(f"Difference in velocity {diff.base[3:]}")
            if (abs(diff[:3]) < p_eps).all() and (abs(diff[3:]) < v_eps).all():
                log.debug(f"Convergence in {n} iterations")
                break

            current.base -= diff.base
        else:  # pragma: no cover
            raise RuntimeError(f"Maximum number of iterations exceeded ({MAX_ITER})")

        return current
