#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from numpy import cos, sqrt, sin, arctan2
from datetime import timedelta

from space.utils.date import Date
from space.orbits.forms import FormTransform

__all__ = ['Sgp4']


class WGS72Old:
    """Constants for WGS72 old model
    """
    µ_e = 3.9860079964e5       # in km³.s⁻²
    r_e = 6378.135             # km
    k_e = 0.0743669161
    j2 = 0.001082616
    j3 = -0.00000253881
    j4 = -0.00000165597


class WGS72:
    """Constants for WGS72 model
    """
    µ_e = 3.986008e5           # in km³.s⁻²
    r_e = 6378.135             # km
    k_e = 60.0 / sqrt(r_e ** 3 / µ_e)
    j2 = 0.001082616
    j3 = -0.00000253881
    j4 = -0.00000165597


class WGS84:
    """Constants for WGS84 model
    """
    µ_e = 3.986005e5           # in km³.s⁻²
    r_e = 6378.137             # in km
    k_e = 60.0 / sqrt(r_e ** 3 / µ_e)
    j2 = 0.00108262998905
    j3 = -0.00000253215306
    j4 = -0.00000161098761


class Init:
    pass


class Sgp4:
    """This class is a simplistic implementation of SGP4 model. It doesn't
    implement SDP4 model at the moment.

    It is highly under-optimised, and serves only the purpose of testing.
    """

    def __init__(self, orbit, gravity=WGS72):

        if orbit.form != FormTransform.TLE:
            raise TypeError("Not TLE")

        self.gravity = gravity
        self.tle = orbit
        self._sgp4_init()

    def _sgp4_init(self):

        self._init = Init()

        i0, Ω0, e0, ω0, M0, n0 = self.tle
        n0 *= 60  # conversion to min⁻¹
        bstar = self.tle.complements['bstar']

        j2 = self.gravity.j2
        j3 = self.gravity.j3
        j4 = self.gravity.j4
        r_e = self.gravity.r_e
        k_e = self.gravity.k_e

        # We work in dimensionless variables
        self._init.A30 = -j3
        self._init.k2 = 1 / 2 * j2
        k4 = - 3 / 8 * j4

        delta = 3 / 2 * self._init.k2 * (3.0 * cos(i0) ** 2 - 1.0) / ((1. - e0 ** 2) ** (3. / 2.))

        a1 = (k_e / n0) ** (2 / 3)
        delta_1 = delta / a1 ** 2
        self._init.a0 = a1 * (1 - 1 / 3 * delta_1 - delta_1 ** 2 - 134. * delta_1 ** 3 / 81.)
        delta_0 = delta / self._init.a0 ** 2
        self._init.n0 = n0 / (1 + delta_0)
        self._init.a0 = self._init.a0 / (1 - delta_0)
        rp = self._init.a0 * (1 - e0)  # perigee in fraction of earth radius
        rp_alt = (rp - 1) * r_e        # altitude of the perigee in km

        self._init.s = 78. / r_e + 1
        self._init.q0 = 120. / r_e + 1

        if rp_alt < 156:
            self._init.s = rp_alt - 78
            if rp_alt < 98:
                self._init.s = 20

            self._init.s = self._init.s / r_e + 1

        self._init.θ = cos(i0)
        self._init.ξ = 1 / (self._init.a0 - self._init.s)
        self._init.β_0 = sqrt(1 - e0 ** 2)
        self._init.η = self._init.a0 * e0 * self._init.ξ

        C2 = (self._init.q0 - self._init.s) ** 4 * self._init.ξ ** 4 * self._init.n0 * (1 - self._init.η ** 2) ** (- 7 / 2) * (self._init.a0 * (1 + 3 / 2 * self._init.η ** 2 + 4 * e0 * self._init.η + e0 * self._init.η ** 3) + 3 * self._init.k2 * self._init.ξ * (- 0.5 + 3 / 2 * self._init.θ ** 2) * (8 + 24 * self._init.η ** 2 + 3 * self._init.η ** 4) / (2 * (1 - self._init.η ** 2)))
        self._init.C1 = bstar * C2

        self._init.C3 = 0.
        if e0 > 1e-4:
            self._init.C3 = (self._init.q0 - self._init.s) ** 4 * self._init.ξ ** 5 * self._init.A30 * self._init.n0 * sin(i0) / (self._init.k2 * e0)

        self._init.C4 = 2 * self._init.n0 * (self._init.q0 - self._init.s) ** 4 * self._init.ξ ** 4 * self._init.a0 * self._init.β_0 ** 2 * (1 - self._init.η ** 2) ** (- 7 / 2) * ((2 * self._init.η * (1 + e0 * self._init.η) + 0.5 * e0 + 0.5 * self._init.η ** 3) - 2 * self._init.k2 * self._init.ξ / (self._init.a0 * (1 - self._init.η ** 2)) * (3 * (1 - 3 * self._init.θ ** 2) * (1 + 3 / 2 * self._init.η ** 2 - 2 * e0 * self._init.η - 0.5 * e0 * self._init.η ** 3) + (3 / 4 * (1 - self._init.θ ** 2) * (2 * self._init.η ** 2 - e0 * self._init.η - e0 * self._init.η ** 3) * cos(2 * ω0))))
        self._init.C5 = 2 * (self._init.q0 - self._init.s) ** 4 * self._init.ξ ** 4 * self._init.a0 * self._init.β_0 ** 2 * (1 - self._init.η ** 2) ** (- 7 / 2) * (1 + 11 / 4 * self._init.η * (self._init.η + e0) + (e0 * self._init.η ** 3))
        self._init.D2 = 4 * self._init.a0 * self._init.ξ * self._init.C1 ** 2
        self._init.D3 = 4 / 3 * self._init.a0 * self._init.ξ ** 2 * (17 * self._init.a0 + self._init.s) * self._init.C1 ** 3
        self._init.D4 = 2 / 3 * self._init.a0 ** 2 * self._init.ξ ** 3 * (221 * self._init.a0 + 31 * self._init.s) * self._init.C1 ** 4

        self._init.Mdot = (1 + (3 * self._init.k2 * (3 * self._init.θ ** 2 - 1)) / (2 * self._init.a0 ** 2 * self._init.β_0 ** 3) + (3 * self._init.k2 ** 2 * (13 - 78 * self._init.θ ** 2 + 137 * self._init.θ ** 4)) / (16 * self._init.a0 ** 4 * self._init.β_0 ** 7))
        self._init.ωdot = (- 3 * self._init.k2 * (1 - 5 * self._init.θ ** 2) / (2 * self._init.a0 ** 2 * self._init.β_0 ** 4) + 3 * self._init.k2 ** 2 * (7 - 114 * self._init.θ ** 2 + 395 * self._init.θ ** 4) / (16 * self._init.a0 ** 4 * self._init.β_0 ** 8) + 5 * k4 * (3 - 36 * self._init.θ ** 2 + 49 * self._init.θ ** 4) / (4 * self._init.a0 ** 4 * self._init.β_0 ** 8))
        self._init.Ωdot = (- 3 * self._init.k2 * self._init.θ / (self._init.a0 ** 2 * self._init.β_0 ** 4) + 3 * self._init.k2 ** 2 * (4 * self._init.θ - 19 * self._init.θ ** 3) / (2 * self._init.a0 ** 4 * self._init.β_0 ** 8) + 5 * k4 * self._init.θ * (3 - 7 * self._init.θ ** 2) / (2 * self._init.a0 ** 4 * self._init.β_0 ** 8))

    def propagate(self, date):
        """Compute state of orbit at a given date, past or future

        Args:
            date (Date)
        Return:
            Orbit:
        """

        i0, Ω0, e0, ω0, M0, n0 = self.tle
        n0 *= 60  # conversion to min⁻¹
        if isinstance(date, Date):
            t0 = self.tle.date.datetime
            tdiff = (date.datetime - t0).total_seconds() / 60.
        elif isinstance(date, timedelta):
            tdiff = date.total_seconds() / 60.
            date = self.tle.date + date
        else:
            raise TypeError("Unhandled type for 'date': %s" % type(date))

        bstar = self.tle.complements['bstar']
        µ = self.gravity.µ_e
        r_e = self.gravity.r_e
        k_e = self.gravity.k_e

        # retrieve initialised variables
        _i = self._init
        n0 = _i.n0

        Mdf = M0 + _i.Mdot * n0 * tdiff
        ωdf = ω0 + _i.ωdot * n0 * tdiff
        Ωdf = Ω0 + _i.Ωdot * n0 * tdiff

        delta_ω = bstar * _i.C3 * cos(ω0) * tdiff
        delta_M = 0.
        if e0 > 1e-4:
            delta_M = - 2 / 3 * (_i.q0 - _i.s) ** 4 * bstar * _i.ξ ** 4 / (e0 * _i.η) * ((1 + _i.η * cos(Mdf)) ** 3 - (1 + _i.η * cos(M0)) ** 3)

        Mp = (Mdf + delta_ω + delta_M) % (2 * np.pi)
        ω = ωdf - delta_ω - delta_M
        Ω = Ωdf - 21 * n0 * _i.k2 * _i.θ / (2 * _i.a0 ** 2 * _i.β_0 ** 2) * _i.C1 * tdiff ** 2
        e = e0 - bstar * _i.C4 * tdiff - bstar * _i.C5 * (sin(Mp) - sin(M0))

        if e < 1e-6:
            e = 1e-6

        a = _i.a0 * (1 - _i.C1 * tdiff - _i.D2 * tdiff ** 2 - _i.D3 * tdiff ** 3 - _i.D4 * tdiff ** 4) ** 2

        L = Mp + ω + Ω + n0 * (3 / 2 * _i.C1 * tdiff ** 2 + (_i.D2 + 2 * _i.C1 ** 2) * tdiff ** 3 + 1 / 4 * (3 * _i.D3 + 12 * _i.C1 * _i.D2 + 10 * _i.C1 ** 3) * tdiff ** 4 + 1 / 5 * (3 * _i.D4 + 12 * _i.C1 * _i.D3 + 6 * _i.D2 ** 2 + 30 * _i.C1 ** 2 * _i.D2 + 15 * _i.C1 ** 4) * tdiff ** 5)

        β = sqrt(1 - e ** 2)
        n = µ / (a ** (3 / 2))

        # Long-period terms
        axN = e * cos(ω)
        ayNL = _i.A30 * sin(i0) / (4 * _i.k2 * a * β ** 2)
        tmp = (1 + _i.θ) if (1 + _i.θ) > 1.5e-12 else 1.5e-12
        L_L = ayNL / 2 * axN * ((3 + 5 * _i.θ) / tmp)

        L_T = L + L_L
        ayN = e * sin(ω) + ayNL

        # Resolving of kepler equation
        U = (L_T - Ω) % (2 * np.pi)
        Epω = U
        for xxx in range(10):
            delta_Epω = (U - ayN * cos(Epω) + axN * sin(Epω) - Epω) / (1 - ayN * sin(Epω) - axN * cos(Epω))
            if abs(delta_Epω) < 1e-12:
                break
            Epω = Epω + delta_Epω

        # Short-period terms
        ecosE = axN * cos(Epω) + ayN * sin(Epω)
        esinE = axN * sin(Epω) - ayN * cos(Epω)
        e_L = sqrt(axN ** 2 + ayN ** 2)
        p_L = a * (1 - e_L ** 2)
        r = a * (1 - ecosE)
        rdot = sqrt(a) / r * esinE
        rfdot = sqrt(p_L) / r

        cosu = a / r * (cos(Epω) - axN + ayN * esinE / (1 + sqrt(1 - e_L ** 2)))
        sinu = a / r * (sin(Epω) - ayN - axN * esinE / (1 + sqrt(1 - e_L ** 2)))
        u = arctan2(sinu, cosu)

        Delta_r = _i.k2 / (2 * p_L) * (1 - _i.θ ** 2) * cos(2 * u)
        Delta_u = - _i.k2 / (4 * p_L ** 2) * (7 * _i.θ ** 2 - 1) * sin(2 * u)
        Delta_Ω = 3 * _i.k2 * _i.θ / (2 * p_L ** 2) * sin(2 * u)
        Delta_i = 3 * _i.k2 * _i.θ / (2 * p_L ** 2) * sin(i0) * cos(2 * u)
        Delta_rdot = - n * _i.k2 * (1 - _i.θ ** 2) * sin(2 * u) / (p_L * µ)
        Delta_rfdot = _i.k2 * n * ((1 - _i.θ ** 2) * cos(2 * u) - 3 / 2 * (1 - 3 * _i.θ ** 2)) / (p_L * µ)

        rk = r * (1 - 3 / 2 * _i.k2 * sqrt(1 - e_L ** 2) / (p_L ** 2) * (3 * _i.θ ** 2 - 1)) + Delta_r
        uk = u + Delta_u
        Ωk = Ω + Delta_Ω
        ik = i0 + Delta_i
        rdotk = rdot + Delta_rdot
        rfdotk = rfdot + Delta_rfdot

        # Vectors
        vM = np.array([- sin(Ωk) * cos(ik), cos(Ωk) * cos(ik), sin(ik)])
        vN = np.array([cos(Ωk), sin(Ωk), 0])

        vU = vM * sin(uk) + vN * cos(uk)
        vV = vM * cos(uk) - vN * sin(uk)

        vR = rk * vU * r_e
        vRdot = (rdotk * vU + rfdotk * vV) * (r_e * k_e / 60.)

        return self.tle.__class__(date, np.concatenate((vR, vRdot)) * 1000, 'cartesian', 'TEME', self.__class__)
