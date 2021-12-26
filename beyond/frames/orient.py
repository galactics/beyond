import numpy as np

from ..utils.node import Node
from ..utils.matrix import rot2, rot3, expand
from . import iau1980, iau2010, local


class Orientation(Node):
    """Rotation matrix generator for frame transformation handling"""

    def convert_to(self, date, new_orient):
        """Provide the rotation matrix to transform a vector in a given orientation (self)
        to another (new_orient)

        Args:
            date (Date):
            new_orient (str or Orientation)
        return:
            numpy.ndarray: 6x6 rotation matrix
        """

        if isinstance(new_orient, self.__class__):
            new_orient = new_orient.name

        m = np.identity(6)

        for a, b in self.steps(new_orient):
            direct = f"{a}_to_{b}"
            reverse = f"{b}_to_{a}"

            if hasattr(self, direct):
                m1, rate = getattr(self, direct)(date)
            elif hasattr(self, reverse):
                m1, rate = getattr(self, reverse)(date)
                m1 = m1.T
                rate = -rate if rate is not None else None
            else:
                raise ValueError(f"Unknown transformation {a} <-> {b}")

            M = expand(m1, rate=rate)

            m = M @ m

        return m

    def TEME_to_TOD(self, date):
        equin = iau1980.equinox(date, eop_correction=False, terms=4, kinematic=False)
        return rot3(-np.deg2rad(equin)), None

    def PEF_to_TOD(self, date):
        m = iau1980.sideral(date, model="apparent", eop_correction=False)
        return m, -iau1980.rate(date)

    def TOD_to_MOD(self, date):
        return iau1980.nutation(date, eop_correction=False), None

    def MOD_to_EME2000(self, date):
        return iau1980.precesion(date), None

    def ITRF_to_PEF(self, date):
        return iau1980.earth_orientation(date), None

    def ITRF_to_TIRF(self, date):
        return iau2010.earth_orientation(date), None

    def TIRF_to_CIRF(self, date):
        m = iau2010.sideral(date)
        return m, -iau2010.rate(date)

    def CIRF_to_GCRF(self, date):
        return iau2010.precesion_nutation(date), None

    def G50_to_EME2000(self, date):
        return (
            np.array(
                [
                    [0.9999256794956877, -0.0111814832204662, -0.0048590038153592],
                    [0.0111814832391717, 0.9999374848933135, -0.0000271625947142],
                    [0.0048590037723143, -0.0000271702937440, 0.9999881946023742],
                ]
            ),
            None,
        )

    def GCRF_to_EME2000(self, date):
        return (
            np.array(
                [
                    [
                        0.9999_9999_9999_9942,
                        0.0000_0007_0782_7948,
                        -0.0000_0008_0562_1738,
                    ],
                    [
                        -0.0000_0007_0782_7974,
                        0.9999_9999_9999_9969,
                        -0.0000_0003_3060_4088,
                    ],
                    [
                        0.0000_0008_0562_1715,
                        0.0000_0003_3060_4145,
                        0.9999_9999_9999_9962,
                    ],
                ]
            ),
            None,
        )


TEME = Orientation("TEME")
PEF = Orientation("PEF")
TOD = Orientation("TOD")
MOD = Orientation("MOD")
EME2000 = Orientation("EME2000")
G50 = Orientation("G50")

ITRF = Orientation("ITRF")
TIRF = Orientation("TIRF")
CIRF = Orientation("CIRF")
GCRF = Orientation("GCRF")

ITRF + PEF + TOD + MOD + EME2000 + G50
TOD + TEME
ITRF + TIRF + CIRF + GCRF


class TopocentricOrientation(Orientation):
    """Orientation for handling topocentric frames i.e. ground stations"""

    def __init__(self, name, latlonalt, parent=ITRF):
        super().__init__(name)
        self.parent = parent
        self.latlonalt = latlonalt

        mtd = f"{name}_to_{parent.name}"
        setattr(self, mtd, self._to_parent)

        self.parent + self

    def _to_parent(self, date):
        lat, lon, _ = self.latlonalt
        # the 'rot3(np.pi)' is here to place the X axis along the north direction
        m = rot3(-lon) @ rot2(lat - np.pi / 2.0) @ rot3(np.pi)
        return m, None


class LocalOrbitalOrientation(Orientation):
    """Local Orbital Orientation"""

    def __init__(self, name, statevector, orient, parent):
        """
        Args:
            name (str) : Name of the frame
            statevector (StateVector) : Point in space and time to which the
                local orbital frame is attached
            orient (str) : Orientation of the local orbital frame (QSW or TNW)
            parent (Frame) : Inertial frame (such as EME2000)
        """

        super().__init__(name)
        self.statevector = statevector
        self.orient = orient
        self.parent = parent

        mtd = f"{name}_to_{parent.orientation.name}"
        setattr(Orientation, mtd, self._to_parent)

        self.parent.orientation + self

    def _to_parent(self, date):

        if hasattr(self.statevector, "propagate"):
            sv = self.statevector.propagate(date)
        else:
            sv = self.statevector

        sv = sv.copy(form="cartesian", frame=self.parent)

        return local.to_local(self.orient, sv, expanded=False).T, None


if __name__ == "__main__":

    from ..dates import Date

    print(EME2000.convert_to(Date.now(), GCRF))
    # GCRF.convert_to(Date.now(), ITRF)
