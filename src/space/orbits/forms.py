#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from numpy import cos, arccos, sin, arcsin, arctan2, sqrt, arccosh, sinh

from space.utils.node import Node
from space.constants import µ_e


class Form(Node):

    _case = False

    def __init__(self, name, param_names, subcoord=None):
        super().__init__(name, subcoord)
        self.param_names = param_names

    def __str__(self):  # pragma: no cover
        return self.name


class FormTransform:

    TLE = Form("TLE", ["i", "Ω", "e", "ω", "M", "n"])
    KEPL_M = Form("Keplerian_M", ["a", "e", "i", "Ω", "ω", "M"], [TLE])
    KEPL = Form("Keplerian", ["a", "e", "i", "Ω", "ω", "ν"], [KEPL_M])
    SPHE = Form("Spherical", ["r", "φ", "θ", "r_dot", "φ_dot", "θ_dot"])
    CART = Form("Cartesian", ["x", "y", "z", "vx", "vy", "vz"], [KEPL, SPHE])

    _tree = CART

    def __init__(self, orbit):
        self.orbit = orbit

    def transform(self, new_form):
        """Gives the result of the transformation without inplace modifications

        Args:
            new_form (str or Form):
        Returns:
            Coord
        """

        if isinstance(new_form, Form):
            new_form = new_form.name

        coord = self.orbit.copy()
        if new_form != self.orbit.form.name:
            for a, b in self._tree.steps(self.orbit.form.name, new_form):
                a = a.name.lower()
                b = b.name.lower()
                coord = getattr(self, "_{}_to_{}".format(a, b))(coord)

        return coord

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
        """Cartesin to Spherical conversion

        .. warning:: The spherical form is equatorial, not zenithal
        """
        x, y, z, vx, vy, vz = coord
        r = np.linalg.norm(coord[:3])
        lat = arcsin(z / r)
        lon = arctan2(y, x)

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
