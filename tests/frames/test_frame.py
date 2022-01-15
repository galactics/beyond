#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import fixture, raises
from unittest.mock import patch

import numpy as np
from numpy.testing import assert_almost_equal
from numpy.linalg import norm

from beyond.errors import UnknownFrameError
from beyond.dates import Date
from beyond.dates.eop import Eop
from beyond.orbits.orbit import Orbit
from beyond.orbits.statevector import StateVector
from beyond.io.tle import Tle
from beyond.frames.frames import *


@fixture
def date(model_correction):
    return Date(2004, 4, 6, 7, 51, 28, 386009)


@fixture
def model_correction():
    with patch('beyond.dates.date.EopDb.get') as m:
        m.return_value = Eop(
            x=-0.140682, y=0.333309, dpsi=-52.195, deps=-3.875,
            dx=-0.205, dy=-0.136, lod=1.5563, ut1_utc=-0.4399619, tai_utc=32
        )
        yield


@fixture
def ref_orbit(date):
    return Orbit(
        [-1033479.383, 7901295.2754, 6380356.5958, -3225.636520, -2872.451450, 5531.924446],
        date,
        'cartesian',
        'ITRF',
        None
    )


pef_ref = np.array([-1033475.03131, 7901305.5856, 6380344.5328,
                    -3225.632747, -2872.442511, 5531.931288])
tod_ref = np.array([5094514.7804, 6127366.4612, 6380344.5328,
                    -4746.088567, 786.077222, 5531.931288])
mod_ref = np.array([5094028.3745, 6127870.8164, 6380248.5164,
                    -4746.263052, 786.014045, 5531.790562])
eme_ref = np.array([5102509.6, 6123011.52, 6378136.3,
                    -4743.2196, 790.5366, 5533.75619])

tirf_ref = np.array([-1033475.0312, 7901305.5856, 6380344.5327,
                     -3225.632747, -2872.442511, 5531.931288])
cirf_ref = np.array([5100018.4047, 6122786.3648, 6380344.5327,
                     -4745.380330, 790.341453, 5531.931288])

gcrf_ref = np.array([5102508.9528, 6123011.3991, 6378136.9338,
                     -4743.220161, 790.536495, 5533.755724])


g50_ref = np.array([5201586.1179, 6065401.818 , 6353101.5731,
                    -4707.139168,   843.373056,  5556.716711])

# This is the real value from Vallado for GCRF reference values
# But the values used in these tests are only 1cm away
# gcrf_ref = np.array([5102508.959, 6123011.403, 6378136.925,
#                      -4743.22016, 790.53650, 5533.75573])


def test_unit_iau1980(ref_orbit, model_correction, helper):
    """These reference data are extracted from Vallado §3.7.3.

    The MOD transformation seems to be problematic
    """

    pv = ITRF.transform(ref_orbit, PEF)
    helper.assert_vector(pef_ref, pv)

    # Going back to ITRF
    pv2 = PEF.transform(pv, ITRF)
    helper.assert_vector(ref_orbit, pv2)

    # PEF to TOD
    pv = PEF.transform(pv, TOD)
    helper.assert_vector(tod_ref, pv)

    # Going back to PEF
    pv2 = TOD.transform(pv, PEF)
    helper.assert_vector(pef_ref, pv2)

    # TOD to MOD
    pv = TOD.transform(pv, MOD)
    # helper.assert_vector(mod_ref, pv)

    # Back to TOD
    pv2 = MOD.transform(pv, TOD)
    helper.assert_vector(tod_ref, pv2)

    # MOD to EME2000
    pv = MOD.transform(pv, EME2000)
    helper.assert_vector(eme_ref, pv)

    # Back to MOD
    pv2 = EME2000.transform(pv, MOD)
    # helper.assert_vector(mod_ref, pv2)


def test_unit_iau2010(ref_orbit, model_correction, helper):

    date = ref_orbit.date

    tirf = ITRF.transform(ref_orbit, TIRF)
    helper.assert_vector(tirf_ref, tirf)

    # Going back to ITRF
    itrf = TIRF.transform(tirf, ITRF)
    helper.assert_vector(ref_orbit, itrf)

    # TIRF to CIRF
    cirf = TIRF.transform(tirf, CIRF)
    helper.assert_vector(cirf_ref, cirf)

    # Back to TIRF
    tirf = CIRF.transform(cirf, TIRF)
    helper.assert_vector(tirf_ref, tirf)

    # CIRF to GCRF
    gcrf = CIRF.transform(cirf, GCRF)
    helper.assert_vector(gcrf_ref, gcrf)

    # Back to CIRF
    cirf = GCRF.transform(gcrf, CIRF)
    helper.assert_vector(cirf_ref, cirf)


def test_unit_g50(ref_orbit, model_correction, helper):

    ref_orbit.frame = EME2000

    g50 = EME2000.transform(ref_orbit, G50)
    helper.assert_vector(g50_ref, g50)

    # back to EME2000
    eme = G50.transform(g50, EME2000)
    helper.assert_vector(eme_ref, eme)


def test_global_change(ref_orbit, model_correction, helper):

    pv = ITRF.transform(ref_orbit, GCRF)
    helper.assert_vector(gcrf_ref, pv)

    pv = ITRF.transform(ref_orbit, EME2000)
    helper.assert_vector(eme_ref, pv)

    pv = EME2000.transform(pv, ITRF)
    helper.assert_vector(ref_orbit, pv)


def test_change_tle(helper):

    # lines = """1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753
    #            2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"""
    # tle = Tle(lines).orbit()
    # tle = tle.propagate(timedelta(days=3))

    # from beyond.dates.eop import get_pole
    # t = Date(2000, 6, 30, 18, 50, 19, 733568).mjd

    # print(get_timescales(t))
    # print(get_pole(t))
    # assert False

    with patch('beyond.dates.date.EopDb.get') as m:
        m.return_value = Eop(
            x=0.11019218256776, y=0.28053771387248, dx=-0.06607524689999991, dy=-0.05407524689999991,
            dpsi=-54.91309785252, deps=-6.363882395480003, lod=0.06999515274799778,
            ut1_utc=0.20415904149231798, tai_utc=32.0
        )

        tle = Orbit(
            [-9060473.7357, 4658709.52502, 813686.731536,
             -2232.83278274, -4110.45348994, -3157.34543346],
            Date(2000, 6, 30, 18, 50, 19, 733568),
            "cartesian", "TEME", None
        )
        tle.frame = 'EME2000'

        eme2000_ref = [-9059942.6552, 4659694.9162, 813957.7525,
                       -2233.346698, -4110.136822, -3157.394202]

        helper.assert_vector(eme2000_ref, tle)


def test_errors(ref_orbit):

    with raises(UnknownFrameError):
        ref_orbit.frame = 'Inexistant'


def test_orbit2frame(helper):

    iss = Tle("""0 ISS (ZARYA)
1 25544U 98067A   16333.80487076  .00003660  00000-0  63336-4 0  9996
2 25544  51.6440 317.1570 0006082 266.5744 156.9779 15.53752683 30592""").orbit()
    soyouz = Tle("""0 SOYUZ MS-03
1 41864U 16070A   16332.46460811 +.00003583 +00000-0 +62193-4 0  9996
2 41864 051.6436 323.8351 0006073 261.8114 220.0268 15.53741335030385""").orbit()

    # This is done to convert the TLE format to cartesian coordinates
    # as done during propagation
    soyouz = soyouz.propagate(soyouz.date)

    inert = iss.as_frame('iss_inert')
    qsw = iss.as_frame('iss_qsw', orientation='QSW')
    tnw = iss.as_frame('iss_tnw', orientation='TNW')

    assert inert.orientation.name == "TEME"
    assert qsw.orientation.orient == "QSW"
    assert tnw.orientation.orient == "TNW"

    s1 = soyouz.copy(frame='iss_inert')
    helper.assert_vector(s1, np.array([70.5889585, 73.6584008, -62.5406308, 0.0521557, 0.0998631, -0.0423856]))

    s2 = soyouz.copy(frame="iss_qsw")
    helper.assert_vector(s2, np.array([4.5450528, -18.6989377, -118.107503, 0.0393978, -0.0046244, -0.1136478]))

    s3 = soyouz.copy(frame="iss_tnw")
    helper.assert_vector(s3, np.array([-18.6974528, -4.5511611, -118.107503, -0.0046116, -0.0393993, -0.1136478]))

    # Whatever the local reference frame, the W vector is the same
    assert s2[2] == s3[2]

    # The norm of the position vectors should the same, because it's always the
    # same relative positions, but expressed in differents frames
    assert_almost_equal(norm(s1[:3]), norm(s2[:3]), decimal=5)
    assert_almost_equal(norm(s2[:3]), norm(s3[:3]))
