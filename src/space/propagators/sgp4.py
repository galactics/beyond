#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from numpy import cos, sqrt, sin, arctan

from space.orbits.tle import Tle


class WGS72Old:
    µ_e = 3.9860079964e5       # in km³.s⁻²
    r_e = 6378.135             # km
    k_e = 0.0743669161
    j2 = 0.001082616
    j3 = -0.00000253881
    j4 = -0.00000165597


class WGS72:
    µ_e = 3.986008e5           # in km³.s⁻²
    r_e = 6378.135             # km
    k_e = 60.0 / sqrt(r_e ** 3 / µ_e)
    j2 = 0.001082616
    j3 = -0.00000253881
    j4 = -0.00000165597


class WGS84:
    µ_e = 3.986005e5           # in km³.s⁻²
    r_e = 6378.137             # in km
    k_e = 60.0 / sqrt(r_e ** 3 / µ_e)
    j2 = 0.00108262998905
    j3 = -0.00000253215306
    j4 = -0.00000161098761


class SGP4:

    def __init__(self, tle, gravity=WGS72):

        if type(tle) is not Tle:
            raise TypeError("tle")

        self.gravity = gravity
        self.tle = tle

    def propagate(self, date):

        # ----------------------- earth constants ---------------------- */
        # sgp4fix identify constants and allow alternate values
        j2 = self.gravity.j2
        j3 = self.gravity.j3
        j4 = self.gravity.j4
        µ = self.gravity.µ_e
        r_e = self.gravity.r_e
        k_e = self.gravity.k_e
        i0, Ω0, e0, ω0, M0, n0 = self.tle.to_list()
        t0 = self.tle.epoch
        tdiff = (date - t0).total_seconds() / 60.
        bstar = self.tle.bstar

        # We work in dimensionless variables
        A30 = -j3
        k2 = 1 / 2 * j2
        k4 = - 3 / 8 * j4

        # print("bstar =", bstar)
        # print("e =", e0)
        # print("ω0 =", ω0)
        # print("i0 =", i0)
        # print("M0 =", M0)
        # print("n0 =", n0)
        # print("Ω0 =", Ω0)

        delta = 3 / 2 * k2 * (3.0 * cos(i0) ** 2 - 1.0) / ((1. - e0 ** 2) ** (3. / 2.))

        a1 = (k_e / n0) ** (2 / 3)
        delta_1 = delta / a1 ** 2
        a0 = a1 * (1 - 1 / 3 * delta_1 - delta_1 ** 2 - 134. * delta_1 ** 3 / 81.)
        delta_0 = delta / a0 ** 2
        n0 = n0 / (1 + delta_0)
        a0 = a0 / (1 - delta_0)
        rp = a0 * (1 - e0)  # perigee in fraction of earth radius
        rp_alt = (rp - 1) * r_e # altitude of the perigee in km

        s = 78. / r_e + 1
        q0 = 120. / r_e + 1

        if rp_alt < 156:
            s = rp_alt - 78
            if rp_alt < 98:
                s = 20

            s = s / r_e + 1

        θ = cos(i0)
        ξ = 1 / (a0 - s)
        β_0 = sqrt(1 - e0 ** 2)
        η = a0 * e0 * ξ

        C2 = (q0 - s) ** 4 * ξ ** 4 * n0 * (1 - η ** 2) ** (- 7 / 2) * (a0 * (1 + 3 / 2 * η ** 2 + 4 * e0 * η + e0 * η ** 3) + 3 * k2 * ξ * (- 0.5 + 3 / 2 * θ ** 2) * (8 + 24 * η ** 2 + 3 * η ** 4) / (2 * (1 - η ** 2)))
        C1 = bstar * C2
        # print(C2)
        C3 = (q0 - s) ** 4 * ξ ** 5 * A30 * n0 * sin(i0) / (k2 * e0)
        C4 = 2 * n0 * (q0 - s) ** 4 * ξ ** 4 * a0 * β_0 ** 2 * (1 - η ** 2) ** (- 7 / 2) * ((2 * η * (1 + e0 * η) + 0.5 * e0 + 0.5 * η ** 3) - 2 * k2 * ξ / (a0 * (1 - η ** 2)) * (3 * (1 - 3 * θ ** 2) * (1 + 3 / 2 * η ** 2 - 2 * e0 * η - 0.5 * e0 * η ** 3) + (3 / 4 * (1 - θ ** 2) * (2 * η ** 2 - e0 * η - e0 * η ** 3) * cos(2 * ω0))))
        C5 = 2 * (q0 - s) ** 4 * ξ ** 4 * a0 * β_0 ** 2 * (1 - η ** 2) ** (- 7 / 2) * (1 + 11 / 4 * η * (η + e0) + (e0 * η ** 3))

        D2 = 4 * a0 * ξ * C1 ** 2
        D3 = 4 / 3 * a0 * ξ ** 2 * (17 * a0 + s) * C1 ** 3
        D4 = 2 / 3 * a0 * ξ ** 3 * (221 * a0 + 31 * s) * C1 ** 4

        Mdot = (1 + (3 * k2 * (3 * θ ** 2 - 1)) / (2 * a0 ** (3 / 2) * β_0 ** 3) + (3 * k2 ** 2 * (13 - 78 * θ ** 2 + 137 * θ ** 4)) / (16 * a0 ** (7 / 2) * β_0 ** 7))
        Mdf = M0 + Mdot * n0 * tdiff
        ωdf = ω0 + (-3 * k2 * (1 - 5 * θ ** 2) / (2 * a0 ** 2 * β_0 ** 4) + 3 * k2 ** 2 * (7 - 114 * θ ** 2 + 395 * θ ** 4) / (16 * a0 ** 4 * β_0 ** 8) + 5 * k4 * (3 - 36 * θ ** 2 + 49 * θ ** 4) / (4 * a0 ** 4 * β_0 ** 8)) * n0 * tdiff
        Ωdf = Ω0 + (- 3 * k2 * θ / (a0 ** 2 * β_0 ** 4) + 3 * k2 ** 2 * (4 * θ - 19 * θ ** 3) / (2 * a0 ** 4 * β_0 ** 8) + 5 * k4 ** θ * (3 - 7 * θ ** 2) / (2 * a0 ** 4 * β_0 ** 8)) * n0 * tdiff

        delta_ω = bstar * C3 * cos(ω0) * tdiff
        delta_M = - 2 / 3 * (q0 - s) ** 4 * bstar * ξ ** 4 * r_e / (e0 * η) * ((1 * η * cos(Mdf)) ** 3 - (1 + η * cos(M0)) ** 3)

        Mp = Mdf + delta_ω + delta_M
        # print("M0", M0)
        # print("Mdf", Mdf)
        # print("Mp", Mp)
        ω = ωdf - delta_ω - delta_M
        Ω = Ωdf - 21 * n0 * k2 * θ / (2 * a0 ** 2 ** β_0 ** 2) * C1 * tdiff ** 2
        e = e0 - bstar * C4 * tdiff - bstar * C5 * (sin(Mp) - sin(M0))
        a = a0 * (1 - C1 * tdiff - D2 * tdiff ** 2 - D3 * tdiff ** 3 - D4 * tdiff ** 4) ** 2

        L = Mp + ω + Ω + n0 * (3 / 2 * C1 * tdiff ** 2 + (D2 + 2 * C1 ** 2) * tdiff ** 3 + 1 / 4 * (3 * D3 + 12 * C1 * D2 + 10 * C1 ** 3) * tdiff ** 4 + 1 / 5 * (3 * D4 + 12 * C1 * D3 + 6 * D2 ** 2 + 30 * C1 ** 2 * D2 + 15 * C1 ** 4) * tdiff ** 5)

        β = sqrt(1 - e ** 2)
        n = µ / (a ** (3 / 2))

        # Long-period terms
        axN = e * cos(ω)
        ayNL = A30 * sin(i0) / (4 * k2 * a * β ** 2)
        L_L = ayNL / 2 * axN * ((3 + 5 * θ) / (1 + θ))

        L_T = L + L_L
        ayN = e * sin(ω) + ayNL

        # Resolving of kepler equation
        U = L_T - Ω
        Epω = U
        for i in range(2):
            delta_Epω = (U - ayN * cos(Epω) + axN * sin(Epω) - Epω) / (-ayN * sin(Epω) - axN * cos(Epω) + 1)
            Epω = Epω + delta_Epω

        # Short-period terms
        ecosE = axN * cos(Epω) + ayN * sin(Epω)
        esinE = axN * sin(Epω) - ayN * cos(Epω)
        e_L = sqrt(axN ** 2 + ayN ** 2)
        p_L = a * (1 - e_L ** 2)
        r = a * (1 - ecosE)
        rdot = µ * sqrt(a) / r * esinE
        rfdot = µ * sqrt(p_L) / r

        cosu = a / r * (cos(Epω) - axN + ayN * esinE / (1 + sqrt(1 - e_L ** 2)))
        sinu = a / r * (sin(Epω) - ayN - axN * esinE / (1 + sqrt(1 - e_L ** 2)))
        u = arctan(sinu / cosu)

        Delta_r = k2 / (2 * p_L) * (1 - θ ** 2) * cos(2 * u)
        Delta_u = - k2 / (4 * p_L ** 2) * (7 * θ ** 2 - 1) * sin(2 * u)
        Delta_Ω = 3 * k2 * θ / (2 * p_L ** 2) * sin(2 * u)
        Delta_i = 3 * k2 * θ / (2 * p_L ** 2) * sin(i0) * cos(2 * u)
        Delta_rdot = - k2 * n / p_L * (1 - θ ** 2) * sin(2 * u)
        Delta_rfdot = k2 * n / p_L * ((1 - θ ** 2) * cos(2 * u) - 3 / 2 * (1 - 3 * θ ** 2))

        rk = r * (1 - 3 / 2 * k2 * sqrt(1 - e_L ** 2) / p_L ** 2 * (3 * θ ** 2 - 1)) + Delta_r
        uk = u + Delta_u
        Ωk = Ω + Delta_Ω
        ik = i + Delta_i
        rdotk = rdot + Delta_rdot
        rfdotk = rfdot + Delta_rfdot

        # Vectors
        vM = np.array([- sin(Ωk) * cos(ik), cos(Ωk) * cos(ik), sin(ik)])
        vN = np.array([cos(Ωk), sin(Ωk), 0])

        vU = vM * sin(uk) + vN * cos(uk)
        vV = vM * cos(uk) - vN * sin(uk)

        vR = rk * vU
        vRdot = rdotk * vU + rfdotk * vV

        return vR, vRdot

    # def propagate(self, date):

    #     tsince = (self.tle.epoch - date).total_seconds() / 60.

    #     j2 = self.gravity.j2
    #     j4 = self.gravity.j4
    #     µ=self.gravity.µ_e * 10 ** -9  # in km³.s⁻²
    #     i, Ω, e, ω, M, n = self.tle.to_list()
    #     n = n / 60  # in min⁻²

    #     a = (µ / n ** 2) ** (1 / 3)
    #     p = a * (1 - e ** 2)
    #     temp1 = 3 / 2. * j2 * n / p ** 2
    #     temp2 = temp1 / 2 * j2 / p ** 2
    #     temp3 = -0.46875 * j4 * n / p ** 4
    #     con42 = 1 - 5 * cos(i)
    #     con41 = - con42 - 2 * cos(i) ** 2

    #     cc2 = coef1 * n * (a * (1 + 1.5 * etasq + eeta * (4 + etasq)) +
    #                        0.375 * j2 * tsi / psisq * con41 * (8 + 3 * etasq * (8 + etasq)))
    #     cc1 = self.tle.bstar * cc2

    #     Mdot = n + (temp1 * np.sqrt(1 - e ** 2) * con41) / 2. + 0.0625 * temp2 * np.sqrt(1 - e ** 2) * 13. - 78.0 * cos(i) ** 2 + 137.0 * cos(i) ** 4
    #     ωdot = temp1 * con42 / 2 + 0.0625 * temp2 * (7.0 - 114 * cos(i) ** 2 + 395 * cos(i) ** 4) + temp3 * (3 - 36 * cos(i) ** 2 + 395 * cos(i) ** 4)
    #     Ωdot = - temp1 * cos(i) + (0.5 * temp2 * (4.0 - 19.0 * cos(i) ** 2) + 2.0 * temp3 * (3.0 - 7.0 * cos(i) ** 2)) * cos(i)
    #     Ωcf = 3.5 * sqrt(1 - e ** 2) * - temp1 * cos(i) * cc1

    #     # Secular gravity and atmospheric drag
    #     Mdf = M + Mdot * tsince
    #     ωdf = ω + ωdot * tsince
    #     Ωdf = Ω + Ωdot * tsince
    #     Ωm = Ωdf + Ωcf * tsince ** 2
    #     xmcof = 0. if e <= 1.0e-4 else -(2. / 3.) * coef * bstar / eeta


class Satellite:
    pass
