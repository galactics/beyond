#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from pytest import raises, fixture
import numpy as np

from beyond.dates.date import Date
from beyond.io.tle import Tle, TleParseError

ref = [
    """ISS (ZARYA)
1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537""",
    """UNKNOWN
1 81014U          19071.50347758  .00025823  00000-0  22146-2 0  9998
2 81014  51.3262 117.7468 2910898 126.0686 264.6106  9.45290855184707""",
    """1 00014U          19071.50347758  .00025823  00000-0  22146-2 0  9999
2 00014  51.3262 117.7468 2910898 126.0686 264.6106  9.45290855184708"""
]


@fixture
def tle_txt():
    return ref[0]


@fixture(params=range(len(ref)))
def both(request):
    return ref[request.param]


def test_read(tle_txt):

    tle = Tle(tle_txt)

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

    tle = Tle(tle_txt.splitlines()[1:])

    assert tle.name == ""

    with raises(TleParseError):
        ref2 = tle_txt[:-1] + "8"
        Tle(ref2)

    orbs = list(Tle.from_string("# comment\n" + tle_txt))
    assert len(orbs) == 1
    assert (orbs[0].orbit() == tle.orbit()).all()

    tle3 = Tle("Name\n" + "\n".join(tle_txt.splitlines()[1:]))
    assert (tle3.orbit() == tle.orbit()).all()

    with raises(TleParseError) as eee:
        l = tle_txt.splitlines()
        l[1] = "3" + l[1][1:]
        Tle("\n".join(l))

    assert str(eee.value).startswith("Line number check failed")


def test_convert_to_orbit(tle_txt):

    tle = Tle(tle_txt)
    orb = tle.orbit()

    assert orb.frame.name == "TEME"
    assert repr(orb.form).startswith("<Form 'tle'")
    assert repr(orb.date) == "<Date '2008-09-20T12:25:40.104192 UTC'>"
    assert orb['i'] == np.deg2rad(51.6416)
    assert orb['Ω'] == np.deg2rad(247.4627)
    assert orb['e'] == 6.703e-4
    assert orb['ω'] == np.deg2rad(130.5360)
    assert orb['M'] == np.deg2rad(325.0288)
    assert orb['n'] == 15.72125391 * 2 * np.pi / 86400.


def test_to_and_from(both):

    tle = Tle(both)
    assert str(tle) == both

    orb = tle.orbit()
    orb2 = orb.copy()
    del orb2._data["cospar_id"]

    tle2 = Tle.from_orbit(orb, name=tle.name, norad_id=tle.norad_id, cospar_id=tle.cospar_id)
    tle3 = Tle.from_orbit(orb2, name=tle.name, norad_id=tle.norad_id)

    assert tle2.cospar_id == tle.cospar_id
    assert tle3.cospar_id == ""

    tle, tle2 = tle.text.splitlines(), tle2.text.splitlines()
    for i in range(2):
        # We don't test the last two fields of the TLE because when we reconstruct one from scracth
        # we can't have any information about the element set number. And because of that, the
        # checksum is also different
        assert tle[i][:63] == tle2[i][:63]


def test_generator(caplog):

    text = "\n".join(ref) + "\n1   \n2   "

    with raises(TleParseError):
        for tle in Tle.from_string(text, error="raise"):
            continue

    for tle in Tle.from_string(text):
        continue

    assert len(caplog.records) == 1
    assert caplog.record_tuples[0][0] == 'beyond.io.tle'
    assert caplog.record_tuples[0][1] == logging.WARNING
    assert caplog.record_tuples[0][2].startswith("Invalid TLE size on line 1. Expected 69, got 1.")

    caplog.clear()

    for tle in Tle.from_string(text, error="ignore"):
        continue

    assert len(caplog.records) == 0
