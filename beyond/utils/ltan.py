"""Utilities to compute the Local Time at Ascending Node (LTAN)

Both True and Mean LTAN are available, the difference between them being
the `equation of time <https://en.wikipedia.org/wiki/Equation_of_time>`__
"""

import numpy as np

from ..env.solarsystem import get_body
from ..frames.iau1980 import _sideral


def _mean_sun_raan(date):
    """Mean Sun RAAN in EME2000"""
    # Not so sure about the UT1 thing
    return (
        np.radians(_sideral(date))
        + np.pi
        - 2 * np.pi * date.change_scale("UT1").s / 86400
    )


def _true_sun_raan(date):
    """True Sun RAAN"""
    return get_body("Sun").propagate(date).copy(frame="EME2000", form="spherical").theta


def orb2ltan(orb, type="mean"):  # pragma: no cover
    """Compute the Local Time at Ascending Node (LTAN) for a given orbit

    Args:
        orb (Orbit): Orbit
        type (str) : either "mean" or "true"
    Return:
        float : LTAN in seconds
    """
    return raan2ltan(orb.date, orb.copy(frame="EME2000", form="keplerian").raan, type)


def raan2ltan(date, raan, type="mean"):
    """Conversion to Local Time at Ascending Node (LTAN)

    Args:
        date (Date) : Date of the conversion
        raan (float) : RAAN in radians, in EME2000
        type (str) : either "mean" or "true"
    Return:
        float : LTAN in seconds
    """

    if type == "mean":
        sun_raan = _mean_sun_raan(date)
    elif type == "true":
        sun_raan = _true_sun_raan(date)
    else:  # pragma: no cover
        raise ValueError(f"Unknwon Local Time type : {type}")

    return (43200 + (raan - sun_raan) * 43200 / np.pi) % 86400


def ltan2raan(date, ltan, type="mean"):
    """Conversion to Longitude

    Args:
        date (Date) : Date of the conversion
        ltan (float) : LTAN in seconds
        type (str) : either "mean" or "true"
    Return:
        float : RAAN in radians in EME2000
    """

    solar_angle = (ltan - 43200) * np.pi / 43200

    if type == "mean":
        sun_raan = _mean_sun_raan(date)
    elif type == "true":
        sun_raan = _true_sun_raan(date)
    else:  # pragma: no cover
        raise ValueError(f"Unknwon Local Time type : {type}")

    return (solar_angle + sun_raan) % (2 * np.pi)
