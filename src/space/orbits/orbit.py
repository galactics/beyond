#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from numpy import cos, arccos, sin, arcsin, arctan, arctan2, sqrt, arccosh, sinh

from space.utils.node import Node
from space.constants import µ_e


class CoordForm(Node):

    def __init__(self, name, param_names, subcoord=None):
        super().__init__(name, subcoord)
        self.param_names = param_names

    def __repr__(self):  # pragma: no cover
        return "<{} {}>".format(self.__class__.__name__, self.name)

    def __str__(self):  # pragma: no    cover
        return self.name


class Coord(np.ndarray):
    """Coordinate representation
    """

    F_TLE = CoordForm("TLE", ["i", "Ω", "e", "ω", "M", "n"])
    F_KEPL_M = CoordForm("Keplerian_M", ["a", "e", "i", "Ω", "ω", "M"], [F_TLE])
    F_KEPL = CoordForm("Keplerian", ["a", "e", "i", "Ω", "ω", "ν"], [F_KEPL_M])
    F_SPHE = CoordForm("Spherical", ["r", "φ", "θ", "r_dot", "φ_dot", "θ_dot"])
    F_CART = CoordForm("Cartesian", ["x", "y", "z", "vx", "vy", "vz"], [F_KEPL, F_SPHE])

    _tree = F_CART

    def __new__(cls, coord, form, **kwargs):

        if len(coord) != 6:
            raise ValueError("Should be 6 in length")

        if type(form) is str:
            form = cls._tree[form]
        elif form.name not in cls._tree:
            raise ValueError("Unknown form")

        obj = np.ndarray.__new__(cls, (6,), buffer=np.array(coord), dtype=float)
        obj.form = form
        obj.other = kwargs

        return obj

    def copy(self):
        new_obj = self.__class__(self.base.copy(), self.form)
        return new_obj

    @property
    def names(self):
        return self.form.param_names

    def __getattr__(self, name):

        convert = {
            'theta': 'θ',
            'phi': 'φ',
            'Omega': "Ω",
            'omega': 'ω',
            'nu': "ν",
            'theta_dot': 'θ_dot',
            'phi_dot': 'φ_dot',
        }

        # Conversion of variable name to utf-8
        if name in convert:
            name = convert[name]

        # Verification if the variable is available in the current form
        if name not in self.names:
            raise AttributeError("{} unknow for this form of Coord".format(name))

        i = self.names.index(name)
        return self[i]

    def __getitem__(self, key):

        if type(key) in (int, slice):
            return super().__getitem__(key)
        else:
            try:
                return self.__getattr__(key)
            except AttributeError as e:
                raise KeyError(str(e))

    def pv(self):
        """Get the coordinates of the orbit in terms of position and velocity

        Returns:
            tuple: 2-length, first element is position, second is velocity.
                The frame is unchanged
        """
        pv = self._transform(self.F_CART)
        return pv[:3], pv[3:]

    def _transform(self, new_form):
        """Gives the result of the transformation without inplace modifications

        Args:
            new_form (str or CoordForm):
        Returns:
            Coord
        """

        if isinstance(new_form, CoordForm):
            new_form = new_form.name

        coord = self.copy()
        if new_form != self.form.name:
            for a, b in self._tree.steps(self.form.name, new_form):
                a = a.name.lower()
                b = b.name.lower()
                coord = getattr(self, "_{}_to_{}".format(a, b))(coord)

        return coord

    def transform(self, new_form):
        """Changes the form of the coordinates in-place

        Args:
            new_form (str or CoordForm)
        """
        if type(new_form) is str:
            # retrivial of the instance corresponding to the name
            new_form = self._tree[new_form]

        coord = self._transform(new_form)
        self.base.setfield(coord, dtype=float)
        self.form = new_form

    @classmethod
    def _cartesian_to_keplerian(cls, coord):

        r_, v_ = coord[:3], coord[3:]
        h_ = np.cross(r_, v_)                     # angular momentum vector
        h = np.linalg.norm(h_)
        r = np.linalg.norm(r_)
        v = np.linalg.norm(v_)

        K = v ** 2 / 2 - µ_e / r                  # specific energy
        a = - µ_e / (2 * K)                       # semi-major axis
        e = sqrt(1 - h ** 2 / (a * µ_e))          # eccentricity
        p = a * (1 - e ** 2)
        i = arccos(h_[2] / h)                     # inclination
        Ω = arctan2(h_[0], -h_[1]) % (2 * np.pi)  # right ascencion of the ascending node

        ω_ν = arctan2(r_[2] / sin(i), r_[0] * cos(Ω) + r_[1] * sin(Ω))
        ν = arctan2(sqrt(p / µ_e) * np.dot(v_, r_), p - r)
        ω = (ω_ν - ν) % (2 * np.pi)               # argument of the perigee

        return np.array([a, e, i, Ω, ω, ν], dtype=float)

    @classmethod
    def _keplerian_to_cartesian(cls, coord):

        a, e, i, Ω, ω, ν = coord

        p = a * (1 - e ** 2)
        r = p / (1 + e * cos(ν))
        h = sqrt(µ_e * p)
        x = r * (cos(Ω) * cos(ω + ν) - sin(Ω) * sin(ω + ν) * cos(i))
        y = r * (sin(Ω) * cos(ω + ν) + cos(Ω) * sin(ω + ν) * cos(i))
        z = r * sin(i) * sin(ω + ν)
        vx = x * h * e / (r * p) * sin(ν) - h / r * (cos(Ω) * sin(ω + ν) + sin(Ω) * cos(ω + ν) * cos(i))
        vy = y * h * e / (r * p) * sin(ν) - h / r * (sin(Ω) * sin(ω + ν) - cos(Ω) * cos(ω + ν) * cos(i))
        vz = z * h * e / (r * p) * sin(ν) + h / r * sin(i) * cos(ω + ν)

        return np.array([x, y, z, vx, vy, vz], dtype=float)

    @classmethod
    def _keplerian_to_keplerian_m(cls, coord):
        a, e, i, Ω, ω, ν = coord
        if e < 1:
            # Elliptic case
            E = arccos((e + cos(ν)) / (1 + e * cos(ν)))  # Eccentric anomaly
            M = E - e * sin(E)  # Mean anomaly
        else:
            # Hyperbolic case
            H = arccosh((e + cos(ν)) / (1 + e * cos(ν)))
            M = e * sinh(H) - H

        return np.array([a, e, i, Ω, ω, M], dtype=float)

    @classmethod
    def _keplerian_m_to_keplerian(cls, coord):
        a, e, i, Ω, ω, M = coord
        E = cls._m_to_e(e, M)
        ν = arccos((cos(E) - e) / (1 - e * cos(E)))

        return np.array([a, e, i, Ω, ω, ν], dtype=float)

    @classmethod
    def _m_to_e(cls, e, M):
        """Conversion from Mean Anomaly to Excetric anomaly
        """

        k1 = 3 * np.pi + 2
        k2 = np.pi - 1
        k3 = 6 * np.pi - 1
        A = 3 * k2 ** 2 / k1
        B = k3 ** 2 / (6 * k1)

        m1 = float(M)
        if abs(m1) < 1 / 6:
            E = m1 + e * (6 * m1) ** (1 / 3) - m1
        elif m1 < 0:
            w = np.pi + m1
            E = m1 + e * (A * w / (B - w) - np.pi - m1)
        else:
            w = np.pi - m1
            E = m1 + e * (np.pi - A * w / (B - w) - m1)

        e1 = 1 - e
        risk_disabler = (e1 + E ** 2 / 6) >= 0.1

        for i in range(2):
            fdd = e * sin(E)
            fddd = e * cos(E)

            if risk_disabler:
                f = (E - fdd) - m1
                fd = 1 - fddd
            else:
                f = cls._e_e_sin_e(e, E) - m1
                s = sin(E / 2)
                fd = e1 + 2 * e * s ** 2
            dee = f * fd / (0.5 * f * fdd - fd ** 2)

            w = fd + 0.5 * dee * (fdd + dee * fddd / 3)
            fd += dee * (fdd + 0.5 * dee * fddd)
            E -= (f - dee * (fd - w)) / fd

        E += M - m1

        return E

    @classmethod
    def _e_e_sin_e(cls, e, E):
        x = (1 - e) * sin(E)
        term = float(E)
        d = 0
        x0 = np.nan
        while x != x0:
            d += 2
            term *= - E ** 2 / (d * (d + 1))
            x0 = x
            x = x - term
        return x

    @classmethod
    def _tle_to_keplerian_m(cls, coord):
        i, Ω, e, ω, M, n = coord
        a = (µ_e / n ** 2) ** (1 / 3)

        return np.array([a, e, i, Ω, ω, M], dtype=float)

    @classmethod
    def _keplerian_m_to_tle(cls, coord):
        a, e, i, Ω, ω, M = coord
        n = sqrt(µ_e / a ** 3)

        return np.array([i, Ω, e, ω, M, n], dtype=float)

    @classmethod
    def _cartesian_to_spherical(cls, coord):
        x, y, z, vx, vy, vz = coord
        r = np.linalg.norm(coord[:3])
        lat = arcsin(z / r)
        lon = arctan(y / x)

        # Not very sure about this
        r_dot = (x * vx + y * vy + z * vz) / r
        lat_dot = (z * (x * vx + y * vy) - vz * (x ** 2 + y ** 2)) / (r ** 2 * sqrt(x ** 2 + y ** 2))
        lon_dot = (y * vx - x * vy) / (x ** 2 + y ** 2)

        return np.array([r, lat, lon, r_dot, lat_dot, lon_dot], dtype=float)

    @classmethod
    def _spherical_to_cartesian(cls, coord):
        r, lat, lon, r_dot, lat_dot, lon_dot = coord
        x = r * cos(lat) * cos(lon)
        y = r * cos(lat) * sin(lon)
        z = r * sin(lat)

        # Not very sure about that either
        vx = r_dot * x / r + y * lon_dot + z * lat_dot * cos(lon)
        vy = r_dot * y / r - x * lon_dot + z * lat_dot * sin(lon)
        vz = r_dot * z / r - r * lat_dot * cos(lat)

        return np.array([x, y, z, vx, vy, vz], dtype=float)


class Orbit:

    epoch = None
    coord = None

    def __init__(self, epoch, form, coord, data=None):
        self.epoch = epoch
        self.coord = Coord(coord, form)
        self.data = data

    def __repr__(self):  # pragma: no cover
        coord_str = '\n'.join([" " * 4 + "%s = %s" % (name, arg) for name, arg in zip(self.coord.names, self.coord)])
        fmt = "Orbit =\n  epoch = {epoch}\n  coord =\n    form = {form}\n{coord}".format(
            epoch=self.epoch.isoformat(),
            coord=coord_str,
            form=self.coord.form
        )
        return fmt

    def change_form(self, new_form):
        self.coord.transform(new_form)

    @property
    def apoapsis(self):

        coord = self.coord.copy()
        if coord.form not in (Coord.F_KEPL, Coord.F_KEPL_M):
            coord.transform(Coord.F_KEPL)

        a, e = coord[:2]
        return a * (1 + e)

    @property
    def periapsis(self):

        coord = self.coord.copy()
        if coord.form not in (Coord.F_KEPL, Coord.F_KEPL_M):
            coord.transform(Coord.F_KEPL)

        a, e = coord[:2]
        return a * (1 - e)
