#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import raises
import numpy as np

from space.utils.date import Date
from space.orbits.tle import Tle

ref = """ISS (ZARYA)
1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"""


def test_read():

    tle = Tle(ref)

    assert tle.name == "ISS (ZARYA)"
    assert tle.norad_id == 25544
    assert tle.cospar_id == "1998-067A"
    assert tle.epoch == Date(2008, 9, 20, 12, 25, 40, 104192)
    assert tle.ndot == -2.182e-5
    assert tle.ndotdot == 0.
    assert tle.bstar == -0.11606e-4
    assert tle.i == np.deg2rad(51.6416)
    assert tle.Ω == np.deg2rad(247.4627)
    assert tle.e == 6.703e-4
    assert tle.ω == np.deg2rad(130.5360)
    assert tle.M == np.deg2rad(325.0288)
    assert tle.n == 15.72125391 * 2 * np.pi / 86400.

    tle = Tle(ref.splitlines()[1:])

    assert tle.name == ""

    with raises(ValueError):
        ref2 = ref[:-1] + "8"
        Tle(ref2)


def test_convert_to_orbit():

    tle = Tle(ref)
    orb = tle.orbit()

    assert str(orb.frame) == "TEME"
    assert str(orb.form) == "TLE"
    assert str(orb.date) == "2008-09-20T12:25:40.104192 UTC"
    assert orb['i'] == np.deg2rad(51.6416)
    assert orb['Ω'] == np.deg2rad(247.4627)
    assert orb['e'] == 6.703e-4
    assert orb['ω'] == np.deg2rad(130.5360)
    assert orb['M'] == np.deg2rad(325.0288)
    assert orb['n'] == 15.72125391 * 2 * np.pi / 86400.
