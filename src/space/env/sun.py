
import numpy as np

from space.orbits import Orbit
from space.utils.units import AU


def sun_vector(date):
    """Compute the position of the sun at a given date

    Args:
        date (~space.utils.date.Date)

    Return:
        ~space.orbits.orbit.Orbit: Position of the sun in MOD frame

    Example:
        >>> from space.utils.date import Date
        >>> sun_vector(Date(2006, 4, 2))
        Orbit =
          date = 2006-04-02T00:00:00 UTC
          form = Cartesian
          frame = MOD
          propag = SunPropagator
          coord =
            x = 146186235644.0
            y = 28789144480.5
            z = 12481136552.3
            vx = 0.0
            vy = 0.0
            vz = 0.0
    """

    t_ut1 = date.change_scale('UT1').julian_century

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

    return Orbit(date, pv, 'cartesian', 'MOD', SunPropagator)


class SunPropagator:
    """Dummy propagator for Sun position
    """

    def __init__(self, *args, **kwargs):
        pass

    def propagate(self, date):
        """Direct call to :py:func:`~space.env.sun.sun_vector`
        """
        return sun_vector(date)
