import numpy as np

from ..orbits import Orbit
from ..orbits.man import ContinuousMan, ImpulsiveMan
from ..dates import timedelta


class CWHelper:
    """This class provides computation helpers for relative motion positioning
    and maneuvers, to be used with the :py:class:`~beyond.propagators.cw.ClohessyWiltshire` propagator

    See the :ref:`docking` script in the documentation for an example of utilisation.
    """

    def __init__(self, propagator):
        self.propagator = propagator

    def __getattr__(self, name):
        try:
            # Allow to directly call for the propagator attributes
            return getattr(self.propagator, name)
        except AttributeError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            ) from None

    @property
    def period(self):
        """Period of the target orbit"""
        return timedelta(seconds=np.pi * 2 / self.n)

    def coelliptic_velocity(self, radial):
        """
        Args:
            radial (float) : radial distance between the target and the chaser
        Return:
            float: Necessary tangential velocity for a coelliptic orbit
        """

        return 1.5 * self.n * radial

    def coelliptic(self, date, radial, tangential):
        """Create an Orbit instance at a given radial and tangential distance
        with the guarantee that it's coelliptic

        Args:
            date (Date) : date
            radial (float) : radial distance (in meters)
            tangential (float) : tangential distance (in meters)
        Return:
            Orbit: coelliptic orbit
        """
        return Orbit(
            self._mat6
            @ [radial, tangential, 0, 0, -self.coelliptic_velocity(radial), 0],
            date,
            form="cartesian",
            frame="Hill",
            propagator=self.propagator,
        )

    def hohmann_distance(self, radial, continuous=False):
        """Compute the tangential distance traveled during a hohmann transfer
        This is interesting to anticipate and place the arrival at a desired position.

        Args:
            radial (float) : radial distance from the target to the chaser
            continuous (bool) : The Hohmann transfer will be done with a ContinuousMan object
        Return:
            float : tangential distance
        """
        res = radial * 3 * np.pi / 4
        return res * 2 if continuous else res

    def hohmann(self, radial, date, continuous=False):
        """Perform a Hohmann transfer

        Args:
            radial (float) : Radial distance to cover
            date (Date) : Begining of the Hohmann transfer
            continuous (bool) :
        Return:
            List[Man]
        """

        dv = (self._mat3 @ [0, 1, 0]) * radial * self.n / 4

        if continuous:
            mans = [ContinuousMan(date, self.period, dv=2 * dv)]
        else:
            mans = [ImpulsiveMan(date, dv), ImpulsiveMan(date + self.period / 2, dv)]

        return mans

    def eccentric_boost(self, tangential, date, continuous=False):
        """Perform an eccentric boost to move tangentially, when the radial distance
        is zero.

        Args:
            tangential (float) : Tangential distance to cover
            date (Date) : Begining of the eccentric boost
            continuous (bool) :
        Return:
            List[Man]
        """

        dv = (self._mat3 @ [-1, 0, 0]) * tangential * self.n / 4
        if continuous:
            mans = [ContinuousMan(date, self.period, dv=2 * dv)]
        else:
            mans = ImpulsiveMan(date, dv), ImpulsiveMan(date + self.period / 2, dv)

        return mans

    def tangential_boost(self, tangential, date):
        """Perform a tangential boost to move tangentially, when the radial distance is zero

        Args:
            tangential (float) : Tangential distance to cover
            date (Date) : Begining of the tangential boost
        Return:
            List[Man]
        """

        dv = (self._mat3 @ [0, -1, 0]) * tangential * self.n / (6 * np.pi)
        mans = ImpulsiveMan(date, dv), ImpulsiveMan(date + self.period, -dv)

        return mans

    def vbar_linear(self, tangential, date, dv):
        """Perform a linear vbar final approach, with radial drift compensation

        Args:
            tangential (float): Tangential distance to cover (in meters)
            date (Date) : Begining of the approach
            dv (float) : velocity of the approach (in meters per seconds)
        Return:
            List[Man]
        """

        duration = timedelta(seconds=abs(tangential / dv))
        dv = np.sign(tangential) * dv
        dv1 = self._mat3 @ [0, dv, 0]
        accel = (self._mat3 @ [-1, 0, 0]) * 2 * self.n * dv
        return (
            ImpulsiveMan(date, dv1),
            ContinuousMan(date, duration, accel=accel),
            ImpulsiveMan(date + duration, -dv1),
        )
