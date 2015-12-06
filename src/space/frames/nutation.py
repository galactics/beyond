# -*- coding: utf-8 -*-

import numpy as np
from pathlib import Path

from space.utils.dates import Date
from space.utils.matrix import rot1, rot2, rot3


def _tab(max_i=None):

    filepath = Path(__file__).parent / "data" / "tab5.1.txt"

    with filepath.open() as f:
        i = 0
        for line in f.read().splitlines():
            if line.startswith("#") or not line.strip():
                continue

            fields = line.split()
            yield map(int, fields[:5]), map(float, fields[6:])

            i += 1
            if max_i and i >= max_i:
                break
            # print(i)


def _nut_1980(date, terms=106):
    """Model 1980 of nutation as described in Vallado

    Args:
        date (datetime.datetime)
        terms (int)
    Return:
        tuple : 3-elements, all floats in radians
            1. espilon_bar
            2. delta_psi
            3. eps
    """

    jj_cent = Date(date).julian_century

    r = 360.  # * 3600.

    epsilon_bar = 23.439291 - 0.0130042 * jj_cent - 1.64e-7 * jj_cent ** 2\
        + 5.04e-7 * jj_cent ** 3

    # mean anomaly of the moon
    m_m = 134.96340251 + (1325 * r + 198.8675605) * jj_cent\
        + 0.0088553 * jj_cent ** 2 + 1.4343e-5 * jj_cent ** 3

    # mean anomaly of the sun
    m_s = 357.52910918 + (99 * r + 259.0502911) * jj_cent\
        - 0.0001537 * jj_cent ** 2 + 3.8e-8 * jj_cent ** 3

    # L - Omega
    u_m_m = 93.27209062 + (1342 * r + 82.0174577) * jj_cent\
        - 0.003542 * jj_cent ** 2 - 2.88e-7 * jj_cent ** 3

    # Mean elongation of the moon from the sun
    d_s = 297.85019547 + (1236 * r + 307.1114469) * jj_cent\
        - 0.0017696 * jj_cent ** 2 + 1.831e-6 * jj_cent ** 3

    # Mean longitude of the ascending node of the moon
    om_m = 125.04455501 - (5 * r + 134.1361851) * jj_cent\
        + 0.0020756 * jj_cent ** 2 + 2.139e-6 * jj_cent ** 3

    delta_psi = 0.
    delta_eps = 0.
    for integers, reals in _tab(terms):
        # print(list(integers), list(reals))
        a1, a2, a3, a4, a5 = integers
        A, B, C, D = reals
        # print(terms, A, B, C, D)
        a_p = a1 * m_m + a2 * m_s + a3 * u_m_m + a4 * d_s + a5 * om_m
        delta_psi += (A + B * jj_cent) * np.sin(np.deg2rad(a_p)) / 36000000.
        delta_eps += (C + D * jj_cent) * np.cos(np.deg2rad(a_p)) / 36000000.

    return np.deg2rad((epsilon_bar, delta_psi, delta_eps))


def nutation(model, date, eop_correction=True, terms=106):
    t = t_tt(date)
    if model == 1980:
        # Model 1980
        epsilon_bar, delta_psi, delta_epsilon = _nut_1980(date, terms)

        if eop_correction:
            pole = PolePosition.get(date)
            delta_epsilon += np.deg2rad(pole['deps'] / 3600000.)
            delta_psi += np.deg2rad(pole['dpsi'] / 3600000.)

        epsilon = epsilon_bar + delta_epsilon
        return rot1(-epsilon_bar) @ rot3(delta_psi) @ rot1(epsilon)


def precesion(date):

    t = t_tt(date)
    zeta = np.deg2rad((2306.2181 * t + 0.30188 * t ** 2 + 0.017998 * t ** 3) / 3600.)
    theta = np.deg2rad((2004.3109 * t - 0.42665 * t ** 2 - 0.041833 * t ** 3) / 3600.)
    z = np.deg2rad((2306.2181 * t + 1.09468 * t ** 2 + 0.018203 * t ** 3) / 3600.)

    return rot3(zeta) @ rot2(-theta) @ rot3(z)


def sideral(date):

    t = Date(date).change_scale('UT1').julian_century

    return 67310.54841 + (876600 * 3600 + 8640184.812866) * t + 0.093104 * t ** 2\
        - 6.2e-6 * t ** 3
