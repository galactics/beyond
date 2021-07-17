import numpy as np

from ..frames.local import to_local
from ..frames.frames import get_frame


class Cov(np.ndarray):
    """Covariance matrix"""

    def __new__(cls, orb, values, frame):
        """Create a covariance matrix

        Args:
            orb (StateVector): State vector from which this is the covariance
            values: 2D matrix (6x6)
            frame (str): Frame in which the covariance is expressed

        .. warning:: For the time being, only 6x6 matrices are handled, but in the
            future there is no reason why NxN matrix can't be used as well
        """

        if isinstance(values, cls):
            frame = values.frame
            values = values.base

        buf = np.array(values)

        if buf.ndim != 2 or buf.shape[0] != buf.shape[1] or buf.shape[0] != 6:
            raise ValueError(
                f"covariance should be 6x6, {buf.shape[0]}x{buf.shape[1]} provided"
            )

        if not np.allclose(buf, buf.T):
            raise ValueError("Non-symmetric covariance")

        obj = np.ndarray.__new__(cls, (6, 6), buffer=buf, dtype=float)
        obj._data = {}
        obj._frame = frame
        obj.orb = orb
        obj._orb_frame = orb.frame

        return obj

    def __repr__(self):  # pragma: no cover
        cols = "x,y,z,vx,vy,vz".split(",")

        txt = "Cov =\n"
        txt += f"  frame = {self.frame}\n"
        txt += " " * 7
        txt += "".join([" {:^9} ".format(x) for x in cols])
        txt += "\n"
        for i in range(6):
            txt += f" {cols[i]:>4} "
            for j in range(i + 1):
                txt += f" {self[i, j]: 0.2e} "
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

        self._data = obj._data.copy()

    @property
    def frame(self):
        """Frame of the covariance

        When this value is changed, the covariance is converted. Accepted
        frames are regular frames (defined in :ref:`frames`) and 'TNW' or 'QSW'.

        If the frame of this covariance is the same as its parent statevector/orbit,
        a change of its parent frame will trigger a change of this covariance frame
        as well.

        .. code-block:: python

            orb.frame.name      # "EME2000"
            orb.cov.frame.name  # "EME2000"
            orb.frame = "ITRF"
            orb.frame.name      # "ITRF"
            orb.cov.frame.name  # "ITRF"

        It it possible to untangle them by switching only the covariance to an other
        frame

        .. code-block:: python

            orb.frame.name      # "EME2000"
            orb.cov.frame.name  # "EME2000"
            orb.cov.frame = "ITRF"
            orb.frame.name      # "EME2000"
            orb.cov.frame.name  # "ITRF"
        """
        return self._data["frame"]

    @frame.setter
    def frame(self, frame):

        _local = ("TNW", "QSW")

        if isinstance(frame, str) and frame not in _local:
            frame = get_frame(frame)

        if frame == self.frame:
            # The frame is the same as the current one
            return

        # Here we use a two step method
        # First we compute the matrix m1, which represents the
        # rotation from the current frame to the parent frame
        # Second we compute the matrix m2 which represents the
        # rotation from the parent frame to the target frame

        # Handle previous frame to parent frame conversion
        if self.frame in ("TNW", "QSW"):
            m1 = to_local(self.frame, self.orb).T
        elif self.frame != self._orb_frame:
            m1 = self.frame.orientation.convert_to(
                self.orb.date, self._orb_frame.orientation
            )
        else:
            m1 = np.identity(6)

        # handle parent frame to target frame conversion
        if frame in ("TNW", "QSW"):
            m2 = to_local(frame, self.orb)
        elif self._orb_frame != frame:
            m2 = self._orb_frame.orientation.convert_to(
                self.orb.date, frame.orientation
            )
        else:
            m2 = np.identity(6)

        M = m2 @ m1

        # https://robotics.stackexchange.com/questions/2556/how-to-rotate-covariance
        cov = M @ self.base @ M.T

        self.base.setfield(cov, dtype=float)
        self._data["frame"] = frame
        if frame not in ("TNW", "QSW"):
            self.orb.frame = frame

    @property
    def _frame(self):
        """Allow to set the frame without triggering a computation"""
        return self._data["frame"]

    @_frame.setter
    def _frame(self, value):
        self._data["frame"] = value

    @property
    def orb(self):
        return self._data["orb"]

    @orb.setter
    def orb(self, value):
        orb = value.copy(form="cartesian")
        if orb.cov is not None:
            del orb.cov
        self._data["orb"] = orb
