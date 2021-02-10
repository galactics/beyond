import numpy as np

from ..dates import timedelta
from ..env.solarsystem import get_body
from .base import AnalyticalPropagator
from ..utils.matrix import expand
from ..orbits.man import ImpulsiveMan, ContinuousMan
from ..frames.frames import HillFrame, get_frame


class ClohessyWiltshire(AnalyticalPropagator):
    """`Clohessy-Wiltshire <https://en.wikipedia.org/wiki/Clohessy%E2%80%93Wiltshire_equations>`__
    analytical propagator for relative motion

    This propagator does not work like other propagators found in the beyond
    library. It works only with orbits defined in the
    :data:`Hill frame <beyond.frames.frames.Hill>`, which is centered on a
    target spacecraft and is curvilinear along its track.

    The initial Orbit is treated as the chaser spacecraft at a relative distance
    and velocity from the target, and propagated Orbits are the evolution of
    the motion of the chaser relative to the target.

    This analytical propagator is able to propagate through impulsive and
    continuous maneuvers.

    You can use :py:class:`~beyond.utils.cwhelper.CWHelper` for
    intilisation and maneuvers
    """

    # Define the rotation matrix to pass from QSW to TNW, this transformation
    # is only valid if the target orbit is circular, which is mandatory for the
    # Clohessy-Wiltshire relations to be true
    QSW2TNW = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])

    def __init__(self, sma, frame="Hill"):
        """
        Args:
            sma (float) : Semi major-axis of the target object (in meters)
            orientation (str) : Local orbital reference frame orientation (QSW or TNW)
            body (str) : Central body
        """

        if isinstance(frame, str):
            frame = get_frame(frame)

        if not isinstance(frame, HillFrame):  # pragma: no cover
            raise TypeError(f"Incompatible frame type : {orientation}")

        self.sma = sma
        self.frame = frame

    @classmethod
    def from_orbit(
        cls, orbit, orientation=HillFrame.DEFAULT_ORIENTATION, name="cw_frame"
    ):
        """Use an Orbit object as target for a Clohessy-Wiltshire propagator

        Args:
            orbit (Orbit) : target
            orientation (str) :
            name (str) : name of the reference frame
        """

        frame = orbit.as_frame(name, orientation=orientation)
        return cls(orbit.infos.kep.a, frame="Hill")

    @property
    def n(self):
        """Mean motion of the target spacecraft"""
        if not hasattr(self, "_n"):
            self._n = np.sqrt(self.frame.center.body.µ / self.sma ** 3)
        return self._n

    @property
    def orbit(self):
        return self._orbit if hasattr(self, "_orbit") else None

    @orbit.setter
    def orbit(self, orb):

        if not isinstance(orb.frame, HillFrame):
            raise TypeError(
                "Frame should be 'Hill' for ClohessyWiltshire propagator. {} found".format(
                    orb.frame.name
                )
            )

        self._orbit = orb.copy(form="cartesian")

    @property
    def _mat3(self):
        """3x3 transformation matrix from the computational frame to the requested frame
        The computational frame is always QSW, and the requested frame may be TNW
        """
        if self.frame.orientation == HillFrame.DEFAULT_ORIENTATION:
            return np.identity(3)
        else:
            return self.QSW2TNW

    @property
    def _mat6(self):
        """6x6 transformation matrix, expanded from :py:attr:`_mat3`"""
        return expand(self._mat3)

    def copy(self):
        return self.__class__(self.sma, frame=self.frame)

    def propagate(self, date):

        if isinstance(date, timedelta):
            date = self.orbit.date + date

        orb = self.orbit

        # Maneuvers handling
        for man in self.orbit.maneuvers:
            if isinstance(man, ImpulsiveMan) and date >= man.date:
                orb = self._propagate(man.date, orb)
                orb[3:] += man.dv(orb)
            elif isinstance(man, ContinuousMan) and date >= man.start:
                orb = self._propagate(man.start, orb)
                if man.check(date):
                    # If the date of propagation is during a continuous maneuver
                    return self._propagate(date, orb, man.accel(orb))
                else:
                    # If the date of propagation is after a continuous maneuver
                    orb = self._propagate(man.stop, orb, man.accel(orb))

        return self._propagate(date, orb)

    def _propagate(self, date, orb, accel=None):
        """This method does the real legwork of propagation, with acceleration
        handling
        """

        if accel is None:
            accel = np.zeros(3)

        dt = date - orb.date
        n = self.n
        t = dt.total_seconds()
        nt = n * t
        cs = np.cos(nt)
        sn = np.sin(nt)

        # Evolution matrix in QSW
        evol_mat = np.array(
            [
                [4 - 3 * cs, 0, 0, sn / n, 2 / n * (1 - cs), 0],
                [
                    6 * (sn - nt),
                    1,
                    0,
                    2 / n * (cs - 1),
                    (4 * sn - 3 * nt) / n,
                    0,
                ],
                [0, 0, cs, 0, 0, sn / n],
                [3 * n * sn, 0, 0, cs, 2 * sn, 0],
                [6 * n * (cs - 1), 0, 0, -2 * sn, 4 * cs - 3, 0],
                [0, 0, -n * sn, 0, 0, cs],
            ]
        )

        # Acceleration matrix
        accel_mat = np.array(
            [
                [(1 - cs) / n ** 2, 2 / n ** 2 * (nt - sn), 0],
                [
                    2 / n ** 2 * (sn - nt),
                    1 / n ** 2 * (4 * (1 - cs) - 3 / 2 * nt ** 2),
                    0,
                ],
                [0, 0, (1 - cs) / n ** 2],
                [sn / n, 2 / n * (1 - cs), 0],
                [2 / n * (cs - 1), (4 * sn - 3 * nt) / n, 0],
                [0, 0, sn / n],
            ]
        )

        if self.frame.orientation != HillFrame.DEFAULT_ORIENTATION:
            # As both evolution and acceleration matrices are defined in QSW, if we want to work in
            # an other reference frame, we have to rotate them
            evol_mat = self._mat6 @ evol_mat @ self._mat6.T
            accel_mat[:3, :] = self._mat3 @ accel_mat[:3, :] @ self._mat3.T
            accel_mat[3:, :] = self._mat3 @ accel_mat[3:, :] @ self._mat3.T

        new = evol_mat @ orb + accel_mat @ accel
        new.date = orb.date + dt

        return new
