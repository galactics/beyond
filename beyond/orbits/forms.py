#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module declares the different meanings that the Orbit 6 components can take
and their conversions
"""

from numpy import cos, arccos, sin, arcsin, arctan2, sqrt, arctanh, sinh, cosh

import numpy as np

from ..errors import UnknownFormError
from ..utils.node import Node


class Form(Node):
    """Base class for orbital form definition
    """

    alt = {
        "theta": "θ",
        "phi": "φ",
        "raan": "Ω",
        "Omega": "Ω",
        "omega": "ω",
        "nu": "ν",
        "theta_dot": "θ_dot",
        "phi_dot": "φ_dot",
        "aol": "u",
        "H": "E",  # The hyperbolic anomaly is available under the eccentric anomaly
    }

    def __init__(self, name, param_names):
        super().__init__(name)
        self.param_names = param_names

    def __str__(self):  # pragma: no cover
        return self.name

    def __call__(self, orbit, new_form):
        """Gives the result of the transformation without in-place modifications

        Args:
            orbit (Orbit):
            new_form (str or Form):
        Returns:
            Coord
        """

        if isinstance(new_form, Form):
            new_form = new_form.name

        coord = orbit.copy()
        if new_form != orbit.form.name:
            for a, b in self.steps(new_form):

                coord = getattr(
                    self, "_{}_to_{}".format(a.name.lower(), b.name.lower())
                )(coord, orbit.frame.center.body)

        return coord

    @classmethod
    def _cartesian_to_keplerian(cls, coord, center):
        """Conversion from cartesian (position and velocity) to keplerian

        The keplerian form is

            * a : semi-major axis
            * e : eccentricity
            * i : inclination
            * Ω : right-ascension of ascending node
            * ω : Argument of perigee
            * ν : True anomaly
        """

        r, v = coord[:3], coord[3:]
        h = np.cross(r, v)  # angular momentum vector
        h_norm = np.linalg.norm(h)
        r_norm = np.linalg.norm(r)
        v_norm = np.linalg.norm(v)

        K = v_norm ** 2 / 2 - center.µ / r_norm  # specific energy
        a = -center.µ / (2 * K)  # semi-major axis
        e = sqrt(1 - h_norm ** 2 / (a * center.µ))  # eccentricity
        p = a * (1 - e ** 2)  # semi parameter
        i = arccos(h[2] / h_norm)  # inclination
        Ω = arctan2(h[0], -h[1]) % (2 * np.pi)  # right ascension of the ascending node

        ω_ν = arctan2(r[2] / sin(i), r[0] * cos(Ω) + r[1] * sin(Ω))
        ν = arctan2(sqrt(p / center.µ) * np.dot(v, r), p - r_norm) % (2 * np.pi)
        ω = (ω_ν - ν) % (2 * np.pi)  # argument of the perigee

        return np.array([a, e, i, Ω, ω, ν], dtype=float)

    @classmethod
    def _keplerian_to_cartesian(cls, coord, center):
        """Conversion from Keplerian to Cartesian coordinates
        """

        a, e, i, Ω, ω, ν = coord

        p = a * (1 - e ** 2)
        r = p / (1 + e * cos(ν))
        h = sqrt(center.µ * p)
        x = r * (cos(Ω) * cos(ω + ν) - sin(Ω) * sin(ω + ν) * cos(i))
        y = r * (sin(Ω) * cos(ω + ν) + cos(Ω) * sin(ω + ν) * cos(i))
        z = r * sin(i) * sin(ω + ν)
        vx = x * h * e / (r * p) * sin(ν) - h / r * (
            cos(Ω) * sin(ω + ν) + sin(Ω) * cos(ω + ν) * cos(i)
        )
        vy = y * h * e / (r * p) * sin(ν) - h / r * (
            sin(Ω) * sin(ω + ν) - cos(Ω) * cos(ω + ν) * cos(i)
        )
        vz = z * h * e / (r * p) * sin(ν) + h / r * sin(i) * cos(ω + ν)

        return np.array([x, y, z, vx, vy, vz], dtype=float)

    @classmethod
    def _keplerian_to_keplerian_eccentric(cls, coord, center):
        """Conversion from Keplerian to Keplerian Eccentric
        """

        a, e, i, Ω, ω, ν = coord
        if e < 1:
            # Elliptic case
            cos_E = (e + cos(ν)) / (1 + e * cos(ν))
            sin_E = (sin(ν) * sqrt(1 - e ** 2)) / (1 + e * cos(ν))
            E = arctan2(sin_E, cos_E) % (2 * np.pi)
        else:
            # Hyperbolic case, E usually marked as H
            cosh_E = (e + cos(ν)) / (1 + e * cos(ν))
            sinh_E = (sin(ν) * sqrt(e ** 2 - 1)) / (1 + e * cos(ν))
            E = arctanh(sinh_E / cosh_E)

        return np.array([a, e, i, Ω, ω, E], dtype=float)

    @classmethod
    def _keplerian_eccentric_to_keplerian_mean(cls, coord, center):
        """Conversion from Keplerian Eccentric to Keplerian Mean
        """
        a, e, i, Ω, ω, E = coord

        if e < 1:
            M = E - e * sin(E)
        else:
            # Hyperbolic case, E usually marked as H
            M = e * sinh(E) - E

        return np.array([a, e, i, Ω, ω, M], dtype=float)

    @classmethod
    def _keplerian_mean_to_keplerian_eccentric(cls, coord, center):
        """Conversion from Mean Keplerian to Keplerian Eccentric
        """
        a, e, i, Ω, ω, M = coord
        E = cls.M2E(e, M)

        return np.array([a, e, i, Ω, ω, E], dtype=float)

    @classmethod
    def _keplerian_eccentric_to_keplerian(cls, coord, center):
        """Conversion from Mean Keplerian to True Keplerian
        """

        a, e, i, Ω, ω, E = coord

        if e < 1:
            cos_ν = (cos(E) - e) / (1 - e * cos(E))
            sin_ν = (sin(E) * sqrt(1 - e ** 2)) / (1 - e * cos(E))
        else:
            # Hyperbolic case, E usually marked as H
            cos_ν = (cosh(E) - e) / (1 - e * cosh(E))
            sin_ν = -(sinh(E) * sqrt(e ** 2 - 1)) / (1 - e * cosh(E))

        ν = arctan2(sin_ν, cos_ν) % (np.pi * 2)

        return np.array([a, e, i, Ω, ω, ν], dtype=float)

    @classmethod
    def M2E(cls, e, M):
        """Conversion from Mean Anomaly to Eccentric anomaly,
        or Hyperbolic anomaly.
    
        from Vallado
        """

        tol = 1e-8

        if e < 1:
            # Ellipse
            if -np.pi < M < 0 or M > np.pi:
                E = M - e
            else:
                E = M + e

            def next_E(E, e, M):
                return E + (M - E + e * sin(E)) / (1 - e * cos(E))

            E1 = next_E(E, e, M)
            while abs(E1 - E) >= tol:
                E = E1
                E1 = next_E(E, e, M)

            return E1
        else:
            # Hyperbolic
            if e < 1.6:
                if -np.pi < M < 0 or M > np.pi:
                    H = M - e
                else:
                    H = M + e
            else:
                if e < 3.6 and abs(M) > np.pi:
                    H = M - np.sign(M) * e
                else:
                    H = M / (e - 1)

            def next_H(H, e, M):
                return H + (M - e * sinh(H) + H) / (e * cosh(H) - 1)

            H1 = next_H(H, e, M)
            while abs(H1 - H) >= tol:
                H = H1
                H1 = next_H(H, e, M)

            return H1

    @classmethod
    def _e_e_sin_e(cls, e, E):
        x = (1 - e) * sin(E)
        term = float(E)
        d = 0
        x0 = np.nan
        while x != x0:
            d += 2
            term *= -(E ** 2) / (d * (d + 1))
            x0 = x
            x = x - term
        return x

    @classmethod
    def _keplerian_circular_to_keplerian(cls, coord, center):
        """Conversion from Keplerian near-circular elements to Mean Keplerian
        """
        a, ex, ey, i, Ω, u = coord

        e = sqrt(ex ** 2 + ey ** 2)
        ω = arctan2(ey / e, ex / e)
        ν = u - ω

        return np.array([a, e, i, Ω, ω, ν], dtype=float)

    @classmethod
    def _keplerian_to_keplerian_circular(cls, coord, center):
        """Conversion from Mean Keplerian to Keplerian near-circular elements
        """
        a, e, i, Ω, ω, ν = coord

        ex = e * cos(ω)
        ey = e * sin(ω)
        u = (ω + ν) % (np.pi * 2)

        return np.array([a, ex, ey, i, Ω, u], dtype=float)

    @classmethod
    def _tle_to_keplerian_mean(cls, coord, center):
        """Conversion from the TLE standard format to the Mean Keplerian

        see :py:class:`Tle` for more information.
        """
        i, Ω, e, ω, M, n = coord
        a = (center.µ / n ** 2) ** (1 / 3)

        return np.array([a, e, i, Ω, ω, M], dtype=float)

    @classmethod
    def _keplerian_mean_to_tle(cls, coord, center):
        """Mean Keplerian to TLE format conversion
        """
        a, e, i, Ω, ω, M = coord
        n = sqrt(center.µ / a ** 3)

        return np.array([i, Ω, e, ω, M, n], dtype=float)

    @classmethod
    def _cartesian_to_spherical(cls, coord, center):
        """Cartesian to Spherical conversion

        .. warning:: The spherical form is equatorial, not zenithal
        """
        x, y, z, vx, vy, vz = coord
        r = np.linalg.norm(coord[:3])
        phi = arcsin(z / r)
        theta = arctan2(y, x)

        r_dot = (x * vx + y * vy + z * vz) / r
        phi_dot = (vz * (x ** 2 + y ** 2) - z * (x * vx + y * vy)) / (
            r ** 2 * sqrt(x ** 2 + y ** 2)
        )
        theta_dot = (x * vy - y * vx) / (x ** 2 + y ** 2)

        return np.array([r, theta, phi, r_dot, theta_dot, phi_dot], dtype=float)

    @classmethod
    def _spherical_to_cartesian(cls, coord, center):
        """Spherical to cartesian conversion
        """
        r, theta, phi, r_dot, theta_dot, phi_dot = coord
        x = r * cos(phi) * cos(theta)
        y = r * cos(phi) * sin(theta)
        z = r * sin(phi)

        vx = r_dot * x / r - y * theta_dot - z * phi_dot * cos(theta)
        vy = r_dot * y / r + x * theta_dot - z * phi_dot * sin(theta)
        vz = r_dot * z / r + r * phi_dot * cos(phi)

        return np.array([x, y, z, vx, vy, vz], dtype=float)


TLE = Form("tle", ["i", "Ω", "e", "ω", "M", "n"])
"""TLE special form

    * i : inclination
    * Ω : right-ascension of ascending node
    * e : eccentricity
    * ω : argument of perigee
    * M : mean anomaly
    * n : mean motion

see :py:class:`~beyond.orbits.tle.Tle` for details
"""

KEPL_C = Form("keplerian_circular", ["a", "ex", "ey", "i", "Ω", "u"])
"""Special case for near-circular orbits

    * a : semi-major axis
    * ex : e * cos(ω)
    * ey : e * sin(ω)
    * i : inclination
    * Ω : right-ascension of ascending node
    * u : argument of latitude (ω + ν)
"""

KEPL_E = Form("keplerian_eccentric", ["a", "e", "i", "Ω", "ω", "E"])
"""Same as Keplerian, but replaces True anomaly with
`Eccentric anomaly <https://en.wikipedia.org/wiki/Eccentric_anomaly>`__
"""

KEPL_M = Form("keplerian_mean", ["a", "e", "i", "Ω", "ω", "M"])
"""Same as Keplerian, but replaces True anomaly with
`Mean anomaly <https://en.wikipedia.org/wiki/Mean_anomaly>`__
"""

KEPL = Form("keplerian", ["a", "e", "i", "Ω", "ω", "ν"])
"""The keplerian form is

    * a : semi-major axis
    * e : eccentricity
    * i : inclination
    * Ω : right-ascension of ascending node
    * ω : Argument of perigee
    * ν : True anomaly

see `wikipedia <https://en.wikipedia.org/wiki/Orbital_elements>`__ for details
"""

SPHE = Form("spherical", ["r", "θ", "φ", "r_dot", "θ_dot", "φ_dot"])
"""Spherical form

    * r : radial distance / altitude
    * θ : azimuth / longitude
    * φ : elevation / latitude
    * r_dot : first derivative of radial distance / altitude
    * θ_dot : first derivative of azimuth / longitude
    * φ_dot : first derivative of elevation / latitude
"""

CART = Form("cartesian", ["x", "y", "z", "vx", "vy", "vz"])
"""Cartesian form"""


SPHE + CART + KEPL + KEPL_E + KEPL_M + TLE
KEPL + KEPL_C


_cache = {
    "tle": TLE,
    "keplerian_circular": KEPL_C,
    "keplerian_mean": KEPL_M,
    "keplerian_eccentric": KEPL_E,
    "keplerian": KEPL,
    "spherical": SPHE,
    "cartesian": CART,
}


def get_form(form):  # pragma: no cover
    if form.lower() not in _cache:
        raise UnknownFormError(form)

    return _cache[form.lower()]
