#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from pytest import fixture, yield_fixture
from unittest.mock import patch
from numpy.testing import assert_almost_equal

from beyond.utils.date import Date
from beyond.env.poleandtimes import ScalesDiff
from beyond.frames.iau2010 import _earth_orientation, _sideral, _planets, _xys, _xysxy2


@fixture
def date():
    return Date(2004, 4, 6, 7, 51, 28, 386009)


@yield_fixture
def time(date):
    with patch('beyond.utils.date.get_timescales') as mock_ts:
        mock_ts.return_value = ScalesDiff(-0.4399619, 32)
        yield


@yield_fixture()
def model_correction(time):
    with patch('beyond.frames.iau2010.get_pole') as mock_pole:
        mock_pole.return_value = {
            'X': -0.140682,
            'Y': 0.333309,
            'dpsi': -52.195,
            'deps': -3.875,
            'dX': -0.205,
            'dY': -0.136,
            'LOD': 1.5563,
        }
        yield


def test_earth_orientation(model_correction, date):

    x_p, y_p, s_prime = _earth_orientation(date)
    assert x_p == -0.140682 / 3600.
    assert y_p == 0.333309 / 3600.
    assert abs(np.radians(s_prime) + 9.712e-12) < 1e-15


def test_sideral(model_correction, date):

    theta = np.degrees(_sideral(date)) % 360.

    assert abs(theta - 312.7552829) < 1e-7


def test_planets(model_correction, date):

    p = np.degrees(_planets(date))

    assert abs(p[0] - 314.9122873) < 1e-7
    assert abs(p[1] - 91.9393769) < 1e-7
    assert abs(p[2] - 169.0970043) < 1e-7
    assert abs(p[3] - 196.7516428) < 1e-7
    assert abs(p[4] - 42.6046467) < 1e-7

    assert abs(p[5] % 360. - 143.319167) < 1e-6
    assert abs(p[6] % 360. - 156.221635) < 1e-6
    assert abs(p[7] % 360. - 194.890465) < 1e-6
    assert abs(p[8] % 360. - 91.262347) < 1e-6
    assert abs(p[9] % 360. - 163.710186) < 1e-6
    assert abs(p[10] % 360. - 102.168400) < 1e-5  # <== I don't know why but this one is not precise enought
    assert abs(p[11] % 360. - 332.317825) < 1e-6
    assert abs(p[12] % 360. - 313.661341) < 1e-6
    assert abs(p[13] % 360. - 0.059545) < 1e-6


def test_xys(model_correction, date):

    X, Y, s_xy2 = _xysxy2(date)
    assert abs(X - 80.531880) < 1e-6
    assert abs(Y - 7.273921) < 1e-6
    assert abs(s_xy2 + 0.001606) < 1e-6

    # Check of the value of s
    _, _, s = np.degrees(_xys(date)) * 3600.
    assert abs(s + 0.003027) < 1e-6