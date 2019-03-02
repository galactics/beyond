#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import raises
import numpy as np

from beyond.dates.date import Date
from beyond.orbits.tle import Tle

ref = """0 ISS (ZARYA)
1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"""


def test_read():

    tle = Tle(ref)

    assert tle.name == "ISS (ZARYA)"
    assert tle.norad_id == 25544
    assert tle.cospar_id == "1998-067A"
    assert tle.epoch == Date(2008, 9, 20, 12, 25, 40, 104192)
    assert tle.ndot == -2.182e-5 * 2
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

    orbs = list(Tle.from_string("# comment\n" + ref))
    assert len(orbs) == 1
    assert (orbs[0].orbit() == tle.orbit()).all()

    tle3 = Tle("Name\n" + "\n".join(ref.splitlines()[1:]))
    assert (tle3.orbit() == tle.orbit()).all()

    with raises(ValueError) as eee:
        l = ref.splitlines()
        l[1] = "3" + l[1][1:]
        Tle("\n".join(l))

    assert str(eee.value) == "Line number check failed"


def test_convert_to_orbit():

    tle = Tle(ref)
    orb = tle.orbit()

    assert repr(orb.frame) == "<Frame 'TEME'>"
    assert repr(orb.form) == "<Form 'tle'>"
    assert repr(orb.date) == "<Date '2008-09-20T12:25:40.104192 UTC'>"
    assert orb['i'] == np.deg2rad(51.6416)
    assert orb['Ω'] == np.deg2rad(247.4627)
    assert orb['e'] == 6.703e-4
    assert orb['ω'] == np.deg2rad(130.5360)
    assert orb['M'] == np.deg2rad(325.0288)
    assert orb['n'] == 15.72125391 * 2 * np.pi / 86400.


def test_to_and_from():

    tle = Tle(ref)
    orb = tle.orbit()

    tle2 = Tle.from_orbit(orb, name=tle.name, norad_id=tle.norad_id, cospar_id=tle.cospar_id)
    tle3 = Tle.from_orbit(orb, name=tle.name, norad_id=tle.norad_id)

    assert tle3.cospar_id == "2000-001A"

    tle, tle2 = tle.text.splitlines(), tle2.text.splitlines()
    for i in range(2):
        # We don't test the last two fields of the TLE because when we reconstruct one from scracth
        # we can't have any information about the element set number. And because of that, the
        # checksum is also different
        assert tle[i][:63] == tle2[i][:63]
