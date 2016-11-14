
from unittest.mock import patch

import numpy as np

from space.utils.date import Date
from space.env.poleandtimes import ScalesDiff
from space.env.moon import moon_vector
from space.env.sun import sun_vector


def test_moon():
    with patch('space.utils.date.get_timescales') as mock_ts:
        mock_ts.return_value = ScalesDiff(-0.0889898, 28.0)
        moon = moon_vector(Date(1994, 4, 28))

    assert str(moon.form) == 'Cartesian'
    assert str(moon.frame) == 'EME2000'
    assert moon.propagator.__name__ == 'MoonPropagator'
    np.testing.assert_array_equal(
        moon,
        np.array([
            -134181157.31672296, -311598171.54027724, -126699062.43738127, 0.0, 0.0, 0.0
        ])
    )


def test_sun():

    with patch('space.utils.date.get_timescales') as mock_ts:
        mock_ts.return_value = ScalesDiff(0.2653703, 33.0)

        sun = sun_vector(Date(2006, 4, 2))

        assert sun.date == Date(2006, 4, 2)
        assert str(sun.form) == 'Cartesian'
        assert str(sun.frame) == 'MOD'
        assert sun.propagator.__name__ == 'SunPropagator'

        np.testing.assert_array_equal(
            sun,
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
