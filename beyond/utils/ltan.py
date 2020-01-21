"""Utilities to compute the Local Time at Ascending Node (LTAN)

Both True and Mean LTAN are available, the difference between them being
the `equation of time <https://en.wikipedia.org/wiki/Equation_of_time>`__
"""

import numpy as np

from ..env.solarsystem import get_body
from ..frames.iau1980 import _sideral


def orb2ltan(orb, type="mean"):
    """Compute the Local Time at Ascending Node (LTAN) for a given orbit

    Args:
        orb (Orbit): Orbit
        type (str) : either "mean" or "true"
    Return
        float : LTAN in hours
    """

    # if type == "old_mean":
    #     # This gives MLTAN only if orb is at Ascending Node
    #     theta = orb.copy(form="spherical", frame="ITRF").theta
    #     return (24 * (theta / (2 * np.pi) + orb.date.s / 86400)) % 24

    return raan2ltan(orb.date, orb.copy(frame="EME2000", form="keplerian").raan, type)


def _mean_sun_raan(date):
    """Mean Sun RAAN in EME2000
    """
    # Not so sure about the UT1 thing
    return (
        np.radians(_sideral(date))
        + np.pi
        - 2 * np.pi * date.change_scale("UT1").s / 86400
    )


def raan2ltan(date, raan, type="mean"):
    """Conversion to True Local Time at Ascending Node (LTAN)

    Args:
        date (Date) : Date of the conversion
        raan (float) : RAAN in radians, in EME2000
        type (str) : either "mean" or "true"
    Return:
        float : LTAN in hours
    """

    if type == "mean":
        mean_solar_angle = raan - _mean_sun_raan(date)
        ltan = (12 + mean_solar_angle * 12 / np.pi) % 24
    elif type == "true":
        theta_sun = (
            get_body("Sun")
            .propagate(date)
            .copy(frame="EME2000", form="spherical")
            .theta
        )
        ltan = ((24 * (raan - theta_sun) / (2 * np.pi)) + 12) % 24
    else:  # pragma: no cover
        raise ValueError("Unknwon Local Time type : {}".format(type))

    return ltan


def ltan2raan(date, ltan, type="mean"):
    """Conversion to Longitude

    Args:
        date (Date) : Date of the conversion
        ltan (float) : LTAN in hours
        type (str) : either "mean" or "true"
    Return:
        float : RAAN in radians in EME2000
    """

    if type == "mean":
        mean_solar_angle = (ltan - 12) * np.pi / 12
        raan = (mean_solar_angle + _mean_sun_raan(date)) % (2 * np.pi)
    elif type == "true":
        sun = get_body("Sun").propagate(date).copy(frame="EME2000", form="spherical")
        hour_angle = np.pi * (ltan - 12) / 12
        raan = (sun.theta + hour_angle) % (2 * np.pi)
    else:  # pragma: no cover
        raise ValueError("Unknwon Local Time type : {}".format(type))

    return raan
