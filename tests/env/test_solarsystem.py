
from pytest import raises
from unittest.mock import patch

import numpy as np

from beyond.errors import UnknownBodyError
from beyond.dates.date import Date
from beyond.dates.eop import Eop
from beyond.env.solarsystem import get_body, SunPropagator, EarthPropagator, MoonPropagator


def test_moon(helper):
    with patch('beyond.dates.date.EopDb.get') as m:
        m.return_value = Eop(x=0, y=0, dx=0, dy=0, deps=0, dpsi=0, lod=0, ut1_utc=-0.0889898, tai_utc=28.0)
        moon = get_body('Moon')
        moon_orb = moon.propagate(Date(1994, 4, 28))

    assert str(moon_orb.form) == 'cartesian'
    assert str(moon_orb.frame) == 'EME2000'
    assert isinstance(moon_orb.propagator, MoonPropagator)
    assert moon_orb.date.scale.name == "TDB"
    assert abs(32.185528758994394138426287099719 + moon_orb.date._offset) <= np.finfo(float).eps
    helper.assert_vector(
        moon_orb,
        np.array([
            -134181155.8063418, -311598172.21627569, -126699062.57176001, 976.8878152910264, -438.8323937765414, -87.42035305682552
        ])
    )


def test_sun(helper):

    with patch('beyond.dates.date.EopDb.get') as m:
        m.return_value = Eop(x=0, y=0, dx=0, dy=0, deps=0, dpsi=0, lod=0, ut1_utc=0.2653703, tai_utc=33.0)
        sun = get_body('Sun')
        sun_orb = sun.propagate(Date(2006, 4, 2))

    assert str(sun_orb.form) == 'cartesian'
    assert str(sun_orb.frame) == 'MOD'
    assert isinstance(sun_orb.propagator, SunPropagator)
    assert sun_orb.date.scale.name == "UT1"
    assert abs(32.734629699999999274950823746622 - sun_orb.date._offset) <= np.finfo(float).eps

    helper.assert_vector(
        sun_orb.base,
        np.array([
            146186235643.53641, 28789144480.499767, 12481136552.345926 , -5757.901470756284 , 26793.699110930935 , 11616.03628136728
        ])
    )


def test_unknown():

    with raises(UnknownBodyError):
        get_body("Mars")
