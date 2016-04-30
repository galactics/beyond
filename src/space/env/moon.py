
import numpy as np

from space.constants import r_e
from space.orbits import Orbit


def moon_vector(date):
    """Compute the Moon position at a given date

    Args:
        date (~space.utils.date.Date)
    Return:
        ~space.orbits.orbit.Orbit: Position of the Moon in EME2000 frame

    Todo:
        Replace `TT` time scale by `TDB`

    Example:
        >>> from space.utils.date import Date
        >>> moon_vector(Date(1994, 4, 28))
        Orbit =
          date = 1994-04-28T00:00:00 UTC
          form = Cartesian
          frame = EME2000
          propag = MoonPropagator
          coord =
            x = -134181157.317
            y = -311598171.54
            z = -126699062.437
            vx = 0.0
            vy = 0.0
            vz = 0.0
    """

    # This model should use the TDB time scale, but it's not implemented yet
    # and TT is a good approximation
    t_tdb = date.change_scale('TT').julian_century

    cos = lambda x: np.cos(np.radians(x))
    sin = lambda x: np.sin(np.radians(x))

    lambda_el = 218.32 + 481267.8813 * t_tdb + 6.29 * sin(134.9 + 477198.85 * t_tdb) \
        - 1.27 * sin(259.2 - 413335.38 * t_tdb) + 0.66 * sin(235.7 + 890534.23 * t_tdb) \
        + 0.21 * sin(269.9 + 954397.7 * t_tdb) - 0.19 * sin(357.5 + 35999.05 * t_tdb) \
        - 0.11 * sin(186.6 + 966404.05 * t_tdb)

    phi_el = 5.13 * sin(93.3 + 483202.03 * t_tdb) + 0.28 * sin(228.2 + 960400.87 * t_tdb) \
        - 0.28 * sin(318.3 + 6003.18 * t_tdb) - 0.17 * sin(217.6 - 407332.2 * t_tdb)

    p = 0.9508 + 0.0518 * cos(134.9 + 477198.85 * t_tdb) + 0.0095 * cos(259.2 - 413335.38 * t_tdb) \
        + 0.0078 * cos(235.7 + 890534.23 * t_tdb) + 0.0028 * cos(269.9 + 954397.70 * t_tdb)

    e_bar = 23.439291 - 0.0130042 * t_tdb - 1.64e-7 * t_tdb ** 2 + 5.04e-7 * t_tdb ** 3

    r_moon = r_e / sin(p)

    pv = r_moon * np.array([
        cos(phi_el) * cos(lambda_el),
        cos(e_bar) * cos(phi_el) * sin(lambda_el) - sin(e_bar) * sin(phi_el),
        sin(e_bar) * cos(phi_el) * sin(lambda_el) + cos(e_bar) * sin(phi_el),
        0, 0, 0
    ])

    return Orbit(date, pv, 'cartesian', 'EME2000', MoonPropagator)


class MoonPropagator:
    """Dummy propagator for moon position
    """

    def __init__(self, *args, **kwargs):
        pass

    def propagate(self, date):
        """Direct call to :py:func:`~space.env.moon.moon_vector`
        """
        return moon_vector(date)
