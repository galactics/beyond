
import numpy as np

from ..frames.local import to_qsw, to_tnw


class Maneuver:

    def __init__(self, date, dv, frame=None):
        """
        Args:
            date (Date): Date of application of the maneuver
            dv (list): Vector of length 3 describing the velocity increment
            frame (str): Which frame is used for applying the increment : ``'TNW'``, ``'QSW'`` or
                ``None``. If ``frame = None`` the same frame as the orbit is used
        """

        if len(dv) != 3:
            raise ValueError("dv should be 3 in lenght")

        self.date = date
        self._dv = np.array(dv)
        self.frame = frame

    def dv(self, orb):
        """Computation of the velocity increment in the reference frame of the orbit

        Args:
            orb (Orbit):
        Return:
            numpy.array: Velocity increment, length 3
        """

        orb = orb.copy(form="cartesian")

        if self.frame == "QSW":
            mat = to_qsw(orb).T
        elif self.frame == "TNW":
            mat = to_tnw(orb).T
        else:
            mat = np.identity(3)

        # velocity increment in the same reference frame as the orbit
        return mat @ self._dv
