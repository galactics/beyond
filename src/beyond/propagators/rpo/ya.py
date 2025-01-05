import numpy as np

from numpy import sin, cos

from ...dates import timedelta
from ...orbits import StateVector
from ...frames.frames import HillFrame
from ...frames.local import to_local
from ..base import AnalyticalPropagator


class YamanakaAnkersen(AnalyticalPropagator):
    """Yamanaka-Ankersen propagator for relative motion

    This propagator allows for analytical propagation of relative motion, with a target
    on an arbitrary elliptical orbit.

    The algorithm is directly taken from the original paper

        New State Transition Matrix for Relative Motion on an Arbitrary Elliptical Orbit
        Koji Yamanaka and Finn Ankersen.
        Journal of Guidance, Control, and Dynamics 25, no. 1 (January 2002): 60–66.
        https://doi.org/10.2514/2.4875.
    """

    FRAME = "EME2000"
    FORM = "keplerian"
    DEFAULT_ORIENT = "LVLH"
    """Orientation used for the computation"""

    def __init__(self, target, orientation=DEFAULT_ORIENT):
        self.target = target.copy(form=self.FORM, frame=self.FRAME)
        self.orientation = orientation

    def copy(self):
        return self.__class__(self.target)

    @property
    def orbit(self):
        if hasattr(self, "_orbit"):
            return self._orbit
        else:
            None

    @orbit.setter
    def orbit(self, orb):
        """Chaser orbit, converted to the LVLH local orbital frame of the target"""

        if not isinstance(orb.frame, HillFrame):
            raise TypeError(
                f"Frame should be 'Hill' for YamanakaAnkersen propagator. {orb.frame} found"
            )

        self.target_at_date0 = self.target.propagate(orb.date).copy(
            frame=self.FRAME, form=self.FORM
        )
        cart = self.target_at_date0.copy(form="cartesian")

        if orb.frame.orientation == self.DEFAULT_ORIENT:
            m_in = np.identity(6)
        else:
            m_in = (
                to_local(self.DEFAULT_ORIENT, cart)
                @ to_local(orb.frame.orientation, cart).T
            )

        self._orbit = m_in @ orb.copy(form="cartesian")

    def propagate(self, date):
        if isinstance(date, timedelta):
            date = self.orbit.date + date

        dt = date - self.orbit.date

        target_at_date = self.target.propagate(date)

        a0, e0, _, _, _, ν0 = self.target_at_date0.copy(
            frame=self.FRAME, form=self.FORM
        )
        a, e, _, _, _, ν = target_at_date.copy(frame=self.FRAME, form=self.FORM)

        rho_theta0 = 1 + e0 * cos(ν0)
        c_theta0 = rho_theta0 * cos(ν0)
        s_theta0 = rho_theta0 * sin(ν0)

        rho_theta = 1 + e * cos(ν)
        c_theta = rho_theta * cos(ν)
        s_theta = rho_theta * sin(ν)
        cp_theta = -(sin(ν) + e * sin(2 * ν))
        sp_theta = cos(ν) + e * cos(2 * ν)

        rho_diff = 1 + e * cos(ν - ν0)
        c_diff = rho_diff * cos(ν - ν0)
        s_diff = rho_diff * sin(ν - ν0)

        p = a0 * (1 - e0**2)
        h = np.sqrt(self.target.frame.center.body.µ * p)
        k2 = h / p**2

        # Transformed coordinates (Eq. 86)
        x0, y0, z0 = rho_theta0 * self.orbit[:3]
        vx0, vy0, vz0 = -e0 * sin(ν0) * self.orbit[:3] + self.orbit[3:] / (
            k2 * rho_theta0
        )

        # Pseudo-initial transition matrix for in plane (Eq. 82)
        m1 = (
            1
            / (1 - e0**2)
            * np.array(
                [
                    [
                        1 - e0**2,
                        3 * e0 * s_theta0 * (1 / rho_theta0 + 1 / (rho_theta0**2)),
                        -e0 * s_theta0 * (1 + 1 / rho_theta0),
                        -e0 * c_theta0 + 2,
                    ],
                    [
                        0,
                        -3 * s_theta0 * (1 / rho_theta0 + e0**2 / rho_theta0**2),
                        s_theta0 * (1 + 1 / rho_theta0),
                        c_theta0 - 2 * e0,
                    ],
                    [
                        0,
                        -3 * (c_theta0 / rho_theta0 + e0),
                        c_theta0 * (1 + 1 / rho_theta0) + e0,
                        -s_theta0,
                    ],
                    [
                        0,
                        3 * rho_theta0 + e0**2 - 1,
                        -(rho_theta0**2),
                        e0 * s_theta0,
                    ],
                ]
            )
        )

        # Relative state transition matrix for in plane (Eq. 83)
        J = k2 * dt.total_seconds()
        m1bis = np.array(
            [
                [
                    1,
                    -c_theta * (1 + 1 / rho_theta),
                    s_theta * (1 + 1 / rho_theta),
                    3 * rho_theta**2 * J,
                ],
                [0, s_theta, c_theta, 2 - 3 * e * s_theta * J],
                [0, 2 * s_theta, 2 * c_theta - e, 3 * (1 - 2 * e * s_theta * J)],
                [
                    0,
                    sp_theta,
                    cp_theta,
                    -3 * e * (sp_theta * J + s_theta / rho_theta**2),
                ],
            ]
        )

        # Relative state transition matrix for out-of plane (Eq. 84)
        m2 = 1 / rho_diff * np.array([[c_diff, s_diff], [-s_diff, c_diff]])

        xbar0, zbar0, vxbar0, vzbar0 = m1 @ [x0, z0, vx0, vz0]
        x, z, vx, vz = m1bis @ [xbar0, zbar0, vxbar0, vzbar0]
        y, vy = m2 @ [y0, vy0]

        rt = np.array([x, y, z])
        vt = np.array([vx, vy, vz])
        x, y, z = rt / rho_theta
        vx, vy, vz = k2 * (e * sin(ν) * rt + rho_theta * vt)

        if self.orientation == self.DEFAULT_ORIENT:
            m_out = np.identity(6)
        else:
            m_out = (
                to_local(self.orientation, target_at_date)
                @ to_local(self.DEFAULT_ORIENT, target_at_date).T
            )

        return StateVector(
            m_out @ [x, y, z, vx, vy, vz],
            date,
            form="cartesian",
            frame=HillFrame(self.orientation),
        )
