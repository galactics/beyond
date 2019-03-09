import numpy as np

from ..frames.frames import Frame
from ..frames.local import to_tnw, to_qsw


class Cov(np.ndarray):
    """Covariance matrix
    """

    PARENT_FRAME = "parent"

    def __new__(cls, orb, values, frame=PARENT_FRAME):
        """Create a covariance matrix

        Args:
            orb (Orbit): Covariance from which this is the covariance
            values: 2D matrix
            frame (str): Frame in which the covariance is expressed
        """

        if isinstance(values, cls):
            frame = values.frame
            values = values.base

        obj = np.ndarray.__new__(cls, (6, 6), buffer=np.array(values), dtype=float)
        obj._frame = frame
        obj.orb = orb.copy(form="cartesian")

        return obj

    def __repr__(self):  # pragma: no cover
        cols = "x,y,z,vx,vy,vz".split(',')

        txt = "Cov =\n"
        if self.frame is not self.PARENT_FRAME:
            txt += "  frame = {}\n".format(self.frame)
        txt += " " * 7
        txt += "".join([" {:^9} ".format(x) for x in cols])
        txt += "\n"
        for i in range(6):
            txt += " {:>4} ".format(cols[i])
            for j in range(i + 1):
                txt += " {: 0.2e} ".format(self[i, j])
            txt += "\n"
        return txt

    def copy(self, frame=None):
        """"""
        new = self.__class__(self.orb, self.base, frame=self.frame)
        if frame is not None:
            new.frame = frame
        return new

    def __array_finalize__(self, obj):
        if obj is None:
            return

        self._frame = obj._frame
        self.orb = obj.orb

    @property
    def frame(self):
        """Frame of the covariance

        When this value is changed, the covariance is converted
        Accepted frames are 'TNW', 'QSW' and 'parent'
        """
        return self._frame

    @frame.setter
    def frame(self, frame):
        if frame == self._frame:
            return

        if self._frame == "TNW":
            m1 = to_tnw(self.orb).T
        elif self._frame == "QSW":
            m1 = to_qsw(self.orb).T
        else:
            m1 = np.identity(3)

        if frame == "TNW":
            m2 = to_tnw(self.orb)
        elif frame == "QSW":
            m2 = to_qsw(self.orb)
        else:
            m2 = np.identity(3)
        
        m = m2 @ m1
        M = Frame._convert(m, m)

        # https://robotics.stackexchange.com/questions/2556/how-to-rotate-covariance
        cov = M @ self.base @ M.T

        self.base.setfield(cov, dtype=float)
        self._frame = frame
