"""Implementation of the IAU 2010 Earth orientation model
"""

from pathlib import Path

import numpy as np

from ..utils.matrix import rot1, rot2, rot3
from ..utils.memoize import memoize

__all__ = ['sideral', 'precesion_nutation', 'earth_orientation', 'rate']


@memoize
def _tab(element):
    """Extraction and caching of IAU2000 nutation coefficients
    """

    elements = {
        'x': 'tab5.2a.txt',
        'y': 'tab5.2b.txt',
        's': 'tab5.2d.txt'
    }

    if element.lower() not in elements.keys():
        raise ValueError('Unknown element \'%s\'' % element)

    filepath = Path(__file__).parent / "data" / elements[element.lower()]

    total = []
    with filepath.open() as fhd:

        for line in fhd.read().splitlines():

            line = line.strip()

            if line.startswith("#") or not line.strip():
                continue

            if line.startswith('j = '):
                result = []
                total.append(result)
                continue

            # The first field is only an index
            fields = line.split()[1:]
            fields[:2] = [float(x) for x in fields[:2]]
            fields[2:] = [int(x) for x in fields[2:]]
            result.append(fields)

    return total


def _earth_orientation(date):
    """Earth orientation parameters in degrees
    """

    ttt = date.change_scale('TT').julian_century
    # a_a = 0.12
    # a_c = 0.26
    # s_prime = -0.0015 * (a_c ** 2 / 1.2 + a_a ** 2) * ttt
    s_prime = - 0.000047 * ttt

    return date.eop.x / 3600., date.eop.y / 3600., s_prime / 3600


def earth_orientation(date):
    """Earth orientation as a rotating matrix
    """

    x_p, y_p, s_prime = np.deg2rad(_earth_orientation(date))
    return rot3(-s_prime) @ rot2(x_p) @ rot1(y_p)


def _sideral(date):
    """Sideral time in radians
    """
    jd = date.change_scale('UT1').jd
    return 2 * np.pi * (0.779057273264 + 1.00273781191135448 * (jd - 2451545.0))


def sideral(date):
    """Sideral time as a rotation matrix
    """
    return rot3(-_sideral(date))


def rate(date):
    """Return the rotation rate vector of the earth for a given date
    """
    lod = date.eop.lod / 1000.
    return np.array([0, 0, 7.292115146706979e-5 * (1 - lod / 86400.)])


def _planets(date):

    ttt = date.change_scale('TT').julian_century

    M_moon = 485868.249036 + 1717915923.2178 * ttt + 31.8792 * ttt ** 2\
        + 0.051635 * ttt ** 3 - 0.0002447 * ttt ** 4

    M_sun = 1287104.79305 + 129596581.0481 * ttt - 0.5532 * ttt ** 2\
        + 0.000136 * ttt ** 3 - 0.00001149 * ttt ** 4

    u_M_moon = 335779.526232 + 1739527262.8478 * ttt - 12.7512 * ttt ** 2\
        - 0.001037 * ttt ** 3 + 0.00000417 * ttt ** 4

    D_sun = 1072260.70369 + 1602961601.209 * ttt - 6.3706 * ttt ** 2\
        + 0.006593 * ttt ** 3 - 0.00003169 * ttt ** 4

    Omega_moon = 450160.398036 - 6962890.5431 * ttt + 7.4722 * ttt ** 2\
        + 0.007702 * ttt ** 3 - 0.00005939 * ttt ** 4

    lambda_M_mercury = 4.402608842 + 2608.7903141574 * ttt
    lambda_M_venus = 3.176146697 + 1021.3285546211 * ttt
    lambda_M_earth = 1.753470314 + 628.3075849991 * ttt
    lambda_M_mars = 6.203480913 + 334.06124267 * ttt
    lambda_M_jupiter = 0.599546497 + 52.9690962641 * ttt
    lambda_M_saturn = 0.874016757 + 21.3299104960 * ttt
    lambda_M_uranus = 5.481293872 + 7.4781598567 * ttt
    lambda_M_neptune = 5.311886287 + 3.8133035638 * ttt
    p_lambda = 0.02438175 * ttt + 0.00000538691 * ttt ** 2

    planets = np.array([
        M_moon, M_sun, u_M_moon, D_sun, Omega_moon, lambda_M_mercury, lambda_M_venus,
        lambda_M_earth, lambda_M_mars, lambda_M_jupiter, lambda_M_saturn, lambda_M_uranus,
        lambda_M_neptune, p_lambda
    ])

    planets[:5] = np.radians((planets[:5] / 3600) % 360)

    return planets


def _xysxy2(date):
    """Here we deviate from what has been done everywhere else. Instead of taking the formulas
    available in the Vallado, we take those described in the files tab5.2{a,b,d}.txt.

    The result should be equivalent, but they are the last iteration of the IAU2000A as of June 2016

    Args:
        date (Date)
    Return:
        3-tuple of float: Values of X, Y, s + XY/2 in arcsecond
    """

    planets = _planets(date)
    x_tab, y_tab, s_tab = _tab('X'), _tab('Y'), _tab('s')

    ttt = date.change_scale('TT').julian_century

    # Units: micro-arcsecond
    X = -16616.99 + 2004191742.88 * ttt - 427219.05 * ttt ** 2 - 198620.54 * ttt ** 3\
        - 46.05 * ttt ** 4 + 5.98 * ttt ** 5

    Y = -6950.78 - 25381.99 * ttt - 22407250.99 * ttt ** 2 + 1842.28 * ttt ** 3\
        + 1113.06 * ttt ** 4 + 0.99 * ttt ** 5

    s_xy2 = 94.0 + 3808.65 * ttt - 122.68 * ttt ** 2 - 72574.11 * ttt ** 3\
        + 27.98 * ttt ** 4 + 15.62 * ttt ** 5

    for j in range(5):

        _x, _y, _s = 0, 0, 0
        for i in range(len(x_tab[j])):
            Axs, Axc, *p_coefs = x_tab[j][i]
            ax_p = np.dot(p_coefs, planets)
            _x += Axs * np.sin(ax_p) + Axc * np.cos(ax_p)

        for i in range(len(y_tab[j])):
            Ays, Ayc, *p_coefs = y_tab[j][i]
            ay_p = np.dot(p_coefs, planets)
            _y += Ays * np.sin(ay_p) + Ayc * np.cos(ay_p)

        for i in range(len(s_tab[j])):
            Ass, Asc, *p_coefs = s_tab[j][i]
            as_p = np.dot(p_coefs, planets)
            _s += Ass * np.sin(as_p) + Asc * np.cos(as_p)

        X += _x * ttt ** j
        Y += _y * ttt ** j
        s_xy2 += _s * ttt ** j

    # Conversion to arcsecond
    return X * 1e-6, Y * 1e-6, s_xy2 * 1e-6


def _xys(date):
    """Get The X, Y and s coordinates

    Args:
        date (Date):
    Return:
        3-tuple of float: Values of X, Y and s, in radians
    """

    X, Y, s_xy2 = _xysxy2(date)

    # convert milli-arcsecond to arcsecond
    dX, dY = date.eop.dx / 1000., date.eop.dy / 1000.

    # Convert arcsecond to degrees then to radians
    X = np.radians((X + dX) / 3600.)
    Y = np.radians((Y + dY) / 3600.)
    s = np.radians(s_xy2 / 3600.) - (X * Y / 2)

    return X, Y, s


def precesion_nutation(date):
    """Precession/nutation joint rotation matrix for the IAU2010 model
    """

    X, Y, s = _xys(date)

    d = np.arctan(np.sqrt((X**2 + Y**2) / (1 - X ** 2 - Y ** 2)))
    a = 1 / (1 + np.cos(d))

    return np.array([
        [1 - a * X ** 2, -a * X * Y, X],
        [-a * X * Y, 1 - a * Y ** 2, Y],
        [-X, -Y, 1 - a * (X**2 + Y**2)]
    ]) @ rot3(s)
