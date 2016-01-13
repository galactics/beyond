#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import fixture, yield_fixture
from unittest.mock import patch

import numpy as np
from space.frames.poleandtimes import ScalesDiff

from space.utils.date import Date
from space.orbits.orbit import Orbit
from space.frames.frame import *


@yield_fixture
def time():
    with patch('space.frames.poleandtimes.TimeScales.get') as mock_ts:
        mock_ts.return_value = ScalesDiff(-32.4399519, -0.4399619, 32)
        yield


@yield_fixture()
def pole_position(time):
    with patch('space.frames.poleandtimes.PolePosition.get') as mock_pole:
        mock_pole.return_value = {
            'X': -0.140682,
            'Y': 0.333309,
            'dpsi': -52.195,
            'deps': -3.875,
            'LOD': 1.5563,
        }
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


def state_vector_testing(ref, pv):
    np.testing.assert_almost_equal(ref[:3], pv[:3], 4)  # Position
    np.testing.assert_almost_equal(ref[3:], pv[3:], 6)  # Velocity


def test_unit_change(ref_orbit, pole_position):
    """These reference data are extracted from Vallado §3.7.3.
    """
    pef_ref = np.array([-1033475.03131, 7901305.5856, 6380344.5328,
                        -3225.632747, -2872.442511, 5531.931288])
    tod_ref = np.array([5094514.7804, 6127366.4612, 6380344.5328,
                        -4746.088567, 786.077222, 5531.931288])
    mod_ref = np.array([5094028.3745, 6127870.8164, 6380248.5164,
                        -4746.263052, 786.014045, 5531.790562])
    gcrf_ref = np.array([5102508.958, 6123011.401, 6378136.928,
                         -4743.22016, 790.53650, 5533.75528])

    pv = ITRF(ref_orbit.date, ref_orbit).transform('PEF')
    state_vector_testing(pef_ref, pv)

    # Going back to ITRF
    pv2 = PEF(pv.date, pv).transform('ITRF')
    state_vector_testing(ref_orbit, pv2)

    # PEF to TOD
    pv = PEF(pv.date, pv).transform('TOD')
    state_vector_testing(tod_ref, pv)

    # Going back to PEF
    pv2 = TOD(pv.date, pv).transform("PEF")
    state_vector_testing(pef_ref, pv2)

    # TOD to MOD
    pv = TOD(pv.date, pv).transform('MOD')
    state_vector_testing(mod_ref, pv)

    # MOD to GCRF
    pv = MOD(pv.date, pv).transform('GCRF')
    state_vector_testing(gcrf_ref, pv)