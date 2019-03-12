
import numpy as np

from ..frames.local import to_qsw, to_tnw


class Maneuver:

    def __init__(self, date, dv, frame=None, comment=None):
        """
        Args:
            date (Date): Date of application of the maneuver
            dv (list): Vector of length 3 describing the velocity increment
            frame (str): Which frame is used for applying the increment : ``'TNW'``,
                ``'QSW'`` (or its aliases 'RSW' and 'LVLH') or ``None``.
                If ``frame = None`` the same frame as the orbit is used
            comment (str): Free text to give context on a given maneuver
                ('apogee maneuver', 'inclination correction')
        """

        if len(dv) != 3:
            raise ValueError("dv should be 3 in length")
        if isinstance(frame, str):
            frame = frame.upper()
        if frame in ("RSW", 'LVLH', 'QSW'):
            frame = "QSW"

        self.date = date
        self._dv = np.array(dv)
        self.frame = frame
        self.comment = comment

    def __repr__(self):  # pragma: no cover
        txt = "Man =\n  date = {}\n".format(self.date)
        if self.frame:
            txt += "  frame = {}\n".format(self.frame)
        if self.comment:
            txt += "  comment = {}\n".format(self.comment)
        txt += "  dv = \n"
        for i, x in enumerate("xyz"):
            txt += "    {} = {:0.2g}\n".format(x, self._dv[i])
        return txt

    def check(self, orb, step):
        return orb.date < self.date <= orb.date + step

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


class DeltaCombined(Maneuver):
    """Compute directly the desired osculating element changes

    For maximum efficiency:
        * 'a' should be modified at apoapsis or periapsis, via delta_a
        * 'i' should be modified at descending or ascending node, via delta_angle
        * 'Ω' should be modified at argument of latitude +/- 90 deg, via delta_angle
    """

    def __init__(self, date, *, delta_a=0, delta_angle=0, comment=None):
        self.date = date
        self.delta_a = delta_a
        self.delta_angle = delta_angle
        self.comment = comment

    def __repr__(self):  # pragma: no cover
        txt = "Man =\n  date = {}\n".format(self.date)
        if self.delta_a:
            txt += "  delta_a = {}\n".format(self.delta_a)
        if self.delta_angle:
            txt += "  delta_angle = {}\n".format(self.delta_angle)
        if self.comment:
            txt += "  comment = {}\n".format(self.comment)
        return txt

    def dv(self, orb):
        delta_v_a = orb.frame.center.mu * self.delta_a / (2 * orb.infos.v * orb.infos.kep.a ** 2)

        v_final = orb.infos.v + delta_v_a
        delta_v = np.sqrt(orb.infos.v ** 2 + v_final ** 2 - 2 * orb.infos.v * v_final * np.cos(self.delta_angle))
        delta_v_t = v_final * np.cos(self.delta_angle) - orb.infos.v

        ratio = delta_v_t / delta_v
        # Due to some floating point operation rounding, this ratio
        # can be superior to one.
        if np.isclose(ratio, 1):
            delta_v_w = 0
        else:
            alpha = np.arccos(ratio)
            delta_v_w = delta_v * np.sin(alpha)

        self._dv = [delta_v_t, 0, delta_v_w]

        return to_tnw(orb).T @ self._dv
