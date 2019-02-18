"""Analytical computation of Solar System bodies
"""

import numpy as np

from ..constants import Earth, Moon, Sun
from ..errors import UnknownBodyError
from ..orbits import Orbit
from ..utils.units import AU
from ..propagators.base import AnalyticalPropagator


def get_body(name):
    """Retrieve a given body orbits and parameters

    Args:
        name (str): Object name
    Return:
        Body:
    """

    try:

        body, propag = _bodies[name.lower()]
        # attach a propagator to the object
        body.propagate = propag.propagate
    except KeyError as e:
        raise UnknownBodyError(e.args[0])

    return body


class EarthPropagator(AnalyticalPropagator):

    orbit = None

    @classmethod
    def propagate(cls, date):
        return Orbit(date, [0] * 6, 'cartesian', 'EME2000', cls())


class MoonPropagator(AnalyticalPropagator):
    """Dummy propagator for moon position
    """

    orbit = None

    @classmethod
    def propagate(cls, date):
        """Compute the Moon position at a given date

        Args:
            date (~beyond.utils.date.Date)
        Return:
            ~beyond.orbits.orbit.Orbit: Position of the Moon in EME2000 frame
        Example:

            .. code-block:: python

                from beyond.utils.date import Date
                MoonPropagator.propagate(Date(1994, 4, 28))
                # Orbit =
                #   date = 1994-04-28T00:00:00 UTC
                #   form = Cartesian
                #   frame = EME2000
                #   propag = MoonPropagator
                #   coord =
                #     x = -134181157.317
                #     y = -311598171.54
                #     z = -126699062.437
                #     vx = 0.0
                #     vy = 0.0
                #     vz = 0.0
        """

        date = date.change_scale('TDB')
        t_tdb = date.julian_century

        def cos(angle):
            """cosine in degrees"""
            return np.cos(np.radians(angle))

        def sin(angle):
            """sine in degrees"""
            return np.sin(np.radians(angle))

        lambda_el = 218.32 + 481267.8813 * t_tdb + 6.29 * sin(134.9 + 477198.85 * t_tdb) \
            - 1.27 * sin(259.2 - 413335.38 * t_tdb) + 0.66 * sin(235.7 + 890534.23 * t_tdb) \
            + 0.21 * sin(269.9 + 954397.7 * t_tdb) - 0.19 * sin(357.5 + 35999.05 * t_tdb) \
            - 0.11 * sin(186.6 + 966404.05 * t_tdb)

        phi_el = 5.13 * sin(93.3 + 483202.03 * t_tdb) + 0.28 * sin(228.2 + 960400.87 * t_tdb) \
            - 0.28 * sin(318.3 + 6003.18 * t_tdb) - 0.17 * sin(217.6 - 407332.2 * t_tdb)

        p = 0.9508 + 0.0518 * cos(134.9 + 477198.85 * t_tdb) + 0.0095 * cos(259.2 - 413335.38 * t_tdb) \
            + 0.0078 * cos(235.7 + 890534.23 * t_tdb) + 0.0028 * cos(269.9 + 954397.70 * t_tdb)

        e_bar = 23.439291 - 0.0130042 * t_tdb - 1.64e-7 * t_tdb ** 2 + 5.04e-7 * t_tdb ** 3

        r_moon = Earth.r / sin(p)

        state_vector = r_moon * np.array([
            cos(phi_el) * cos(lambda_el),
            cos(e_bar) * cos(phi_el) * sin(lambda_el) - sin(e_bar) * sin(phi_el),
            sin(e_bar) * cos(phi_el) * sin(lambda_el) + cos(e_bar) * sin(phi_el),
            0, 0, 0
        ])

        return Orbit(date, state_vector, 'cartesian', 'EME2000', cls())


class SunPropagator(AnalyticalPropagator):
    """Dummy propagator for Sun position
    """

    orbit = None

    @classmethod
    def propagate(cls, date):
        """Compute the position of the sun at a given date

        Args:
            date (~beyond.utils.date.Date)

        Return:
            ~beyond.orbits.orbit.Orbit: Position of the sun in MOD frame

        Example:

            .. code-block:: python

                from beyond.utils.date import Date
                SunPropagator.propagate(Date(2006, 4, 2))
                # Orbit =
                #   date = 2006-04-02T00:00:00 UTC
                #   form = Cartesian
                #   frame = MOD
                #   propag = SunPropagator
                #   coord =
                #     x = 146186235644.0
                #     y = 28789144480.5
                #     z = 12481136552.3
                #     vx = 0.0
                #     vy = 0.0
                #     vz = 0.0
        """

        date = date.change_scale('UT1')
        t_ut1 = date.julian_century

        lambda_M = 280.460 + 36000.771 * t_ut1
        M = np.radians(357.5291092 + 35999.05034 * t_ut1)
        lambda_el = np.radians(lambda_M + 1.914666471 * np.sin(M) + 0.019994643 * np.sin(2 * M))

        r = 1.000140612 - 0.016708617 * np.cos(M) - 0.000139589 * np.cos(2 * M)
        eps = np.radians(23.439291 - 0.0130042 * t_ut1)

        pv = r * np.array([
            np.cos(lambda_el),
            np.cos(eps) * np.sin(lambda_el),
            np.sin(eps) * np.sin(lambda_el),
            0,
            0,
            0
        ]) * AU

        return Orbit(date, pv, 'cartesian', 'MOD', cls())


_bodies = {
    'moon': (Moon, MoonPropagator),
    'sun': (Sun, SunPropagator),
    'earth': (Earth, EarthPropagator)
}
