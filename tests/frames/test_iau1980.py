#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from pytest import fixture
from unittest.mock import patch
from numpy.testing import assert_almost_equal

from beyond.dates.date import Date
from beyond.dates.eop import Eop
from beyond.frames.iau1980 import _earth_orientation, _precesion, _nutation, _sideral, rate


@fixture
def date(model_correction):
    return Date(2004, 4, 6, 7, 51, 28, 386009)


@fixture
def model_correction():
    with patch('beyond.dates.date.EopDb.get') as m:
        m.return_value = Eop(
            x=-0.140682, y=0.333309, dpsi=-52.195, deps=-3.875, dx=-0.205,
            dy=-0.136, lod=1.5563, ut1_utc=-0.4399619, tai_utc=32
        )
        yield


def test_earth_orientation(date):
    x, y = _earth_orientation(date)
    assert x == -3.9078333333333335e-05
    assert y == 9.258583333333334e-05


def test_precesion(date):
    zeta, theta, z = _precesion(date)

    assert_almost_equal(zeta, 0.0273055)
    assert_almost_equal(theta, 0.0237306)
    assert_almost_equal(z, 0.0273059)


def test_nutation(date):
    epsilon_bar, delta_psi, delta_eps = _nutation(date, eop_correction=False)

    assert_almost_equal(epsilon_bar, 23.4387368)
    assert_almost_equal(delta_psi, -0.0034108)
    assert_almost_equal(delta_eps, 0.0020316)


def test_sideral(date):
    gmst = _sideral(date)
    assert_almost_equal(gmst, 312.8098943)

    gast = _sideral(date, model='apparent', eop_correction=False)
    assert_almost_equal(gast, 312.8067654)


def test_rate(date):
    assert_almost_equal(rate(date), np.array([0, 0, 7.2921150153560662e-05]))
