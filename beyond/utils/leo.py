"""Utilities for Low Earth Orbit design
"""

import numpy as np
import logging

from ..constants import Earth

log = logging.getLogger(__name__)


def sso(*, a=None, e=None, i=None):
    """Compute keplerian elements for a Sun-Synchronous Orbit

    Given two elements among a, e and i, compute the remaining one.

    Example:
        .. code-block:: python

            e = sso(a=a, i=i)
            i = sso(a=a, e=e)
            a = sso(e=e, i=i)

    Args:
        a (float) : Semi major axis, in meters
        e (float) : Eccentricity
        i (float) : Inclination in radians
    """

    ω_e = 2 * np.pi / 365.256363004 / 86400
    cst = np.sqrt(Earth.mu) * Earth.r ** 2 * Earth.J2

    if i is None and a is not None and e is not None:
        return np.arccos(-2 / 3 * ω_e * (a ** (7 / 2) * (1 - e ** 2) ** 2) / cst)
    elif a is None and e is not None and i is not None:
        return (-3 / 2 * cst * np.cos(i) / (ω_e * (1 - e ** 2) ** 2)) ** (2 / 7)
    elif e is None and a is not None and i is not None:
        return np.sqrt(1 - np.sqrt(-3 / 2 * cst * np.cos(i) / (ω_e * a ** (7 / 2))))
    else:
        raise ValueError("Unknown computation mode")


def frozen(a, i):
    """Compute the e and ω for a frozen orbit

    Args:
        a (float): Semi major axis in meters
        i (float): Inclination in radians
    Return:
        Tuple[float, float]: eccentricity (e) and argument of perigee (ω, in radians)
    """

    return -Earth.r * np.sin(i) * Earth.J3 / (2 * Earth.J2 * a), np.pi / 2


def sso_frozen(a):
    """Iterate to find a SSO frozen orbit

    Args:
        a (float): Semi major axis in meters
    Return:
        Tuple[float, float, float]:
            eccentricity (e), inclination (i, in radians)
            and argument of perigee (ω, in radians)
    """

    log.debug("Iterating over sso+frozen orbit parameters")
    MAX_ITER = 10
    k = e = last = 0
    while k < MAX_ITER:
        i = sso(a=a, e=e)
        e, ω = frozen(a, i)
        log.debug(f"{k}  {e:.6e}  {np.degrees(i):10.6f}  {last-e:.6e}")
        if abs(last - e) < 1e-12:
            break
        last = e
        k += 1
    else:
        raise ValueError("Impossible to find a sso/frozen orbit")

    return e, i, ω
