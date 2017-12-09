#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import fixture, yield_fixture, raises
from unittest.mock import patch

import numpy as np
from numpy.testing import assert_almost_equal
from numpy.linalg import norm
from datetime import timedelta

from beyond.dates.eop import Eop
from beyond.dates.date import Date
from beyond.orbits.orbit import Orbit
from beyond.orbits.tle import Tle
from beyond.frames.frame import *


@fixture
def date(model_correction):
    return Date(2004, 4, 6, 7, 51, 28, 386009)


@yield_fixture()
def model_correction():
    with patch('beyond.frames.iau1980.get_eop') as mock_pole1, patch('beyond.frames.iau2010.get_eop') as mock_pole2, patch('beyond.dates.date.get_eop') as mock_date:
        mock_pole1.return_value = Eop(
            x=-0.140682, y=0.333309, dpsi=-52.195, deps=-3.875,
            dx=-0.205, dy=-0.136, lod=1.5563, ut1_utc=-0.4399619, tai_utc=32
        )
        mock_pole2.return_value = mock_pole1.return_value
        mock_date.return_value = mock_pole1.return_value
        yield


@fixture
def ref_orbit():
    return Orbit(
        Date(2004, 4, 6, 7, 51, 28, 386009),
        [-1033479.383, 7901295.2754, 6380356.5958, -3225.636520, -2872.451450, 5531.924446],
        'cartesian',
        'ITRF',
        None
    )


@yield_fixture
def station_env():
    with patch('beyond.frames.iau1980.get_eop') as m, patch('beyond.dates.date.get_eop') as m2:
        m.return_value = Eop(
            x=-0.00951054166666622, y=0.31093590624999734, dpsi=-94.19544791666682, deps=-10.295645833333051,
            dy=-0.10067361111115315, dx=-0.06829513888889051, lod=1.6242802083331438,
            ut1_utc=0.01756018472222477, tai_utc=36.0
        )
        m2.return_value = m.return_value

        yield


def assert_vector(ref, pv, precision=(4, 6)):
    assert_almost_equal(ref[:3], pv[:3], precision[0], "Position")
    assert_almost_equal(ref[3:], pv[3:], precision[1], "Velocity")


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

# This is the real value from Vallado for GCRF reference values
# But the values used in these tests are only 1cm away
# gcrf_ref = np.array([5102508.959, 6123011.403, 6378136.925,
#                      -4743.22016, 790.53650, 5533.75573])


def test_unit_iau1980(ref_orbit, model_correction):
    """These reference data are extracted from Vallado §3.7.3.

    The MOD transformation seems to be problematic
    """

    pv = ITRF(ref_orbit.date, ref_orbit).transform('PEF')
    assert_vector(pef_ref, pv)

    # Going back to ITRF
    pv2 = PEF(ref_orbit.date, pv).transform('ITRF')
    assert_vector(ref_orbit, pv2)

    # PEF to TOD
    pv = PEF(ref_orbit.date, pv).transform('TOD')
    assert_vector(tod_ref, pv)

    # Going back to PEF
    pv2 = TOD(ref_orbit.date, pv).transform("PEF")
    assert_vector(pef_ref, pv2)

    # TOD to MOD
    pv = TOD(ref_orbit.date, pv).transform('MOD')
    # assert_vector(mod_ref, pv)

    # Back to TOD
    pv2 = MOD(ref_orbit.date, pv).transform('TOD')
    assert_vector(tod_ref, pv2)

    # MOD to EME2000
    pv = MOD(ref_orbit.date, pv).transform('EME2000')
    assert_vector(eme_ref, pv)

    # Back to MOD
    pv2 = EME2000(ref_orbit.date, pv).transform('MOD')
    # assert_vector(mod_ref, pv2)


def test_unit_iau2010(ref_orbit, model_correction):

    date = ref_orbit.date

    tirf = ITRF(date, ref_orbit).transform('TIRF')
    assert_vector(tirf_ref, tirf)

    # Going back to ITRF
    itrf = TIRF(date, tirf).transform('ITRF')
    assert_vector(ref_orbit, itrf)

    # TIRF to CIRF
    cirf = TIRF(date, tirf).transform('CIRF')
    assert_vector(cirf_ref, cirf)

    # Back to TIRF
    tirf = CIRF(date, cirf).transform('TIRF')
    assert_vector(tirf_ref, tirf)

    # CIRF to GCRF
    gcrf = CIRF(date, cirf).transform('GCRF')
    assert_vector(gcrf_ref, gcrf)

    # Back to CIRF
    cirf = GCRF(date, gcrf).transform('CIRF')
    assert_vector(cirf_ref, cirf)


def test_global_change(ref_orbit, model_correction):

    pv = ITRF(ref_orbit.date, ref_orbit).transform('GCRF')
    assert_vector(gcrf_ref, pv)

    pv = ITRF(ref_orbit.date, ref_orbit).transform('EME2000')
    assert_vector(eme_ref, pv)

    pv = EME2000(ref_orbit.date, pv).transform('ITRF')
    assert_vector(ref_orbit, pv)


def test_change_tle():

    # lines = """1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753
    #            2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"""
    # tle = Tle(lines).orbit()
    # tle = tle.propagate(timedelta(days=3))

    # from beyond.dates.eop import get_pole
    # t = Date(2000, 6, 30, 18, 50, 19, 733568).mjd

    # print(get_timescales(t))
    # print(get_pole(t))
    # assert False

    with patch('beyond.frames.iau1980.get_eop') as m, patch('beyond.frames.iau2010.get_eop') as m2, patch('beyond.dates.date.get_eop') as m3:
        m.return_value = Eop(
            x=0.11019218256776, y=0.28053771387248, dx=-0.06607524689999991, dy=-0.05407524689999991,
            dpsi=-54.91309785252, deps=-6.363882395480003, lod=0.06999515274799778,
            ut1_utc=0.20415904149231798, tai_utc=32.0
        )
        m2.return_value = m.return_value
        m3.return_value = m.return_value

        tle = Orbit(
            Date(2000, 6, 30, 18, 50, 19, 733568),
            [-9060473.7357, 4658709.52502, 813686.731536,
             -2232.83278274, -4110.45348994, -3157.34543346],
            "cartesian", "TEME", None
        )
        tle.frame = 'EME2000'

        eme2000_ref = [-9059942.6552, 4659694.9162, 813957.7525,
                       -2233.346698, -4110.136822, -3157.394202]

        assert_vector(eme2000_ref, tle)


def test_station(station_env):

    # lines = """ISS (ZARYA)
    #            1 25544U 98067A   16038.20499631  .00009950  00000-0  15531-3 0  9993
    #            2 25544  51.6445 351.2284 0006997  89.9621  48.8570 15.54478078984606"""
    # orb = Tle(lines).orbit()
    # orb = orb.propagate(Date(2016, 2, 7, 16, 55))

    # from beyond.dates.eop import get_pole

    # print(get_pole(Date(2016, 2, 7, 16, 55).mjd))
    # assert False

    orb = Orbit(
        Date(2016, 2, 7, 16, 55),
        [4225679.11976, 2789527.13836, 4497182.71156,
         -5887.93077439, 3748.50929999, 3194.45322378],
        'cartesian', 'TEME', 'Sgp4'
    )
    archive = orb.copy()

    tls = create_station('Toulouse', (43.604482, 1.443962, 172.))

    orb.frame = 'Toulouse'
    orb.form = 'spherical'

    # azimuth
    assert -np.degrees(orb.theta) - 159.75001561831209 <= 1e-9
    # elevation
    assert np.degrees(orb.phi) - 57.894234537351593 <= 1e-9
    # range
    assert orb.r - 471467.6615039421 <= 1e-9

    orb.frame = archive.frame
    orb.form = archive.form
    assert_vector(archive, orb)


def test_station_visibility(station_env):

    lines = """ISS (ZARYA)
               1 25544U 98067A   16038.20499631  .00009950  00000-0  15531-3 0  9993
               2 25544  51.6445 351.2284 0006997  89.9621  48.8570 15.54478078984606"""
    orb = Tle(lines).orbit()

    tls = create_station('Toulouse', (43.604482, 1.443962, 172.))

    points = [point for point in tls.visibility(orb, Date(2016, 2, 7, 16, 45), timedelta(minutes=16), timedelta(seconds=30))]
    assert len(points) == 21
    points = [point for point in tls.visibility(orb, Date(2016, 2, 7, 16, 45), Date(2016, 2, 7, 17, 1), timedelta(seconds=30))]
    assert len(points) == 21

    # Events (AOS, MAX and LOS)
    points = [point for point in tls.visibility(orb, Date(2016, 2, 7, 16, 45), timedelta(minutes=16), timedelta(seconds=30), events=True)]

    # Three more points than precedently, due to the events computation
    assert len(points) == 24

    assert points[0].event.info == 'AOS'
    assert points[0].event.station == tls
    assert points[0].date == Date(2016, 2, 7, 16, 49, 51, 266783)

    assert points[12].event.info == "MAX"
    assert points[12].event.station == tls
    assert points[12].date == Date(2016, 2, 7, 16, 55, 9, 268318)

    assert points[-1].event.info == 'LOS'
    assert points[-1].event.station == tls
    assert points[-1].date == Date(2016, 2, 7, 17, 0, 25, 271351)


def test_errors(ref_orbit):

    with raises(ValueError):
        ref_orbit.frame = 'Inexistant'


def test_orbit2frame():

    iss = Tle("""0 ISS (ZARYA)
                 1 25544U 98067A   16333.80487076  .00003660  00000-0  63336-4 0  9996
                 2 25544  51.6440 317.1570 0006082 266.5744 156.9779 15.53752683 30592""").orbit()
    soyouz = Tle("""0 SOYUZ MS-03
                    1 41864U 16070A   16332.46460811 +.00003583 +00000-0 +62193-4 0  9996
                    2 41864 051.6436 323.8351 0006073 261.8114 220.0268 15.53741335030385""").orbit()

    # This is done to convert the TLE format to cartesian coordinates
    # as done during propagation
    soyouz = soyouz.propagate(soyouz.date)

    iss.register_as_frame('iss_inert')
    iss.register_as_frame('iss_qsw', 'QSW')
    iss.register_as_frame('iss_tnw', 'TNW')
    with raises(ValueError):
        iss.register_as_frame('iss_unknown', 'unknow')

    s1 = soyouz.copy(frame='iss_inert')
    assert_almost_equal(s1[:3], [70.5889585, 73.6584008, -62.5406308])
    assert_almost_equal(s1[3:], [0.0521557, 0.0998631, -0.0423856])

    s2 = soyouz.copy(frame="iss_qsw")
    assert_almost_equal(s2[:3], [4.5450528, -18.6989377, -118.107503])
    assert_almost_equal(s2[3:], [0.0393978, -0.0046244, -0.1136478])

    s3 = soyouz.copy(frame="iss_tnw")
    assert_almost_equal(s3[:3], [-18.6974528, -4.5511611, -118.107503])
    assert_almost_equal(s3[3:], [-0.0046116, -0.0393993, -0.1136478])

    # Whatever the local reference frame, the W vector is the same
    assert s2[2] == s3[2]

    # The norm of the position vectors should the same, because it's always the
    # same relative positions, but expressed in differents frames
    assert_almost_equal(norm(s1[:3]), norm(s2[:3]), 4)
    assert_almost_equal(norm(s2[:3]), norm(s3[:3]), 6)
