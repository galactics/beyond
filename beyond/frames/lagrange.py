import numpy as np

from .frames import Frame
from .local import to_qsw
from .orient import Orientation
from .center import Center
from ..propagators.base import AnalyticalPropagator


class LagrangePropagator(AnalyticalPropagator):
    """Propagate the Lagrange point of body1/body2 in a frame centred on body2 in QSW"""

    def __init__(self, frame1, body2, number):
        self.frame1 = frame1
        self.body2 = body2
        self.number = number

        if not (1 <= number <= 5):  # pragma: no cover
            raise ValueError(f"Unknown Lagrange point : {number}")

    def copy(self):  # pragma: no cover
        return self.__class__(self.frame1, self.body2)

    def propagate(self, date):
        orb = self.body2.propagate(date).copy(frame=self.frame1, form="cartesian")
        offset = np.zeros(6)
        r = np.linalg.norm(orb[:3])

        if self.number in (1, 2):
            offset[0] = r * (self.body2.m / (3 * self.frame1.center.body.m)) ** (1 / 3)
            if self.number == 1:
                offset *= -1
        elif self.number == 3:
            offset[0] = r * (5 * self.body2.m / (12 * self.frame1.center.body.m) - 2)
        elif self.number in (4, 5):
            offset[0] = -r / 2
            offset[1] = r * np.sqrt(3) / 2
            if self.number == 5:
                offset[1] *= -1
        else:  # pragma: no cover
            raise ValueError(f"Unknown Lagrange point : {number}")

        return offset


class LagrangeOrient(Orientation):
    def __init__(self, frame1, body2):

        name = f"{frame1.center.body.name}{body2.name}Lagrange"
        super().__init__(name)

        self.frame1 = frame1
        self.body2 = body2

        mtd = f"{name}_to_{frame1.orientation.name}"
        setattr(Orientation, mtd, self._to_parent)
        frame1.orientation + self

    def _to_parent(self, date):
        orb = self.body2.propagate(date).copy(frame=self.frame1, form="cartesian")
        return to_qsw(orb).T, None


def lagrange(frame1, frame2, number, name=None, orientation=None):
    """Create a reference frame centred on Lagrange points

    Args:
        frame1 (Frame) : Most massive object frame
        frame2 (Frame) : Less massive object frame
        number (int) : Lagrange point number (1 for L1, 2 for L2, ...)
        name (str) : Name of the frame created.
        orientation (Orientation): If ``None``, the created frame will be sinodic (i.e. oriented in QSW relative to frame2)

    Return:
        Frame : Centred on the specified Lagrange point.
    """

    c_name = f"{frame1.center.body.name}{frame2.center.body.name}L{number}"

    if name is None:  # pragma: no cover
        name = c_name

    # The offset of the Lagrange point is provided by the propagator, in a frame
    # centred on body2, and oriented in QSW
    l_orient = LagrangeOrient(frame1, frame2.center.body)
    l_prop = LagrangePropagator(frame1, frame2.center.body, number)
    l_center = Center(c_name)
    l_center.add_link(frame2.center, l_orient, l_prop)

    if orientation is None:
        orientation = l_orient

    return Frame(name, orientation, l_center)
