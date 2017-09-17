
from unittest.mock import patch

import numpy as np

from beyond.utils.date import Date
from beyond.env.poleandtimes import ScalesDiff
from beyond.env.solarsystem import get_body, SunPropagator, EarthPropagator, MoonPropagator


def test_moon():
    with patch('beyond.utils.date.get_timescales') as mock_ts:
        mock_ts.return_value = ScalesDiff(-0.0889898, 28.0)
        moon = get_body('Moon')
        moon_orb = moon.propagate(Date(1994, 4, 28))

    assert str(moon_orb.form) == 'Cartesian'
    assert str(moon_orb.frame) == 'EME2000'
    assert isinstance(moon_orb.propagator, MoonPropagator)
    np.testing.assert_array_equal(
        moon_orb,
        np.array([
            -134181155.8063418, -311598172.21627569, -126699062.57176001, 0.0, 0.0, 0.0
        ])
    )


def test_sun():

    with patch('beyond.utils.date.get_timescales') as mock_ts:
        mock_ts.return_value = ScalesDiff(0.2653703, 33.0)
        sun = get_body('Sun')
        sun_orb = sun.propagate(Date(2006, 4, 2))

    assert str(sun_orb.form) == 'Cartesian'
    assert str(sun_orb.frame) == 'MOD'
    assert isinstance(sun_orb.propagator, SunPropagator)

    np.testing.assert_array_equal(
        sun_orb,
        np.array([
            146186235643.53641, 28789144480.499767, 12481136552.345926, 0.0, 0.0, 0.0
        ])
    )
    # coord =
    #   x = 146186235644.0
    #   y = 28789144480.5
    #   z = 12481136552.3
    #   vx = 0.0
    #   vy = 0.0
    #   vz = 0.0


def test_multi():

    sun, earth, moon = get_body("Sun", "Earth", "Moon")

    sun_orb = sun.propagate(Date.now())
    earth_orb = earth.propagate(Date.now())
    moon_orb = moon.propagate(Date.now())

    assert isinstance(sun_orb.propagator, SunPropagator)
    assert isinstance(earth_orb.propagator, EarthPropagator)
    assert isinstance(moon_orb.propagator, MoonPropagator)
