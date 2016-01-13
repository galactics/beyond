#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import raises
import datetime

from space.utils.date import Date


def test_creation():

    t = Date(2015, 12, 5)
    assert t.d == 57361
    assert t.s == 0

    t = Date(2015, 12, 5, 12)
    assert t.d == 57361
    assert t.s == 43200

    assert str(t) == "2015-12-05T12:00:00 UTC"
    # to trigger the cache mechanism
    assert str(t) == "2015-12-05T12:00:00 UTC"

    # # This would be True if the Date object was a good immutable object
    # b = Date(2015, 12, 5, 12)
    # assert id(a) == id(b)

    # Datetime object
    t = Date(datetime.datetime(2015, 12, 6, 12, 20))
    assert t.d == 57362
    assert t.s == 44400

    # Date object
    t2 = Date(t)
    assert t2.d == t.d
    assert t2.s == t.s

    # Julian day
    t = Date(57388, 0)
    assert t.d == 57388
    assert t.s == 0
    assert t.datetime == datetime.datetime(2016, 1, 1)

    t = Date(57388)
    assert t.d == 57388
    assert t.s == 0.

    t = Date(57388.5)
    assert t.d == 57388
    assert t.s == 43200

    # Wrong number of arguments
    with raises(TypeError):
        t = Date((2015, 12, 6))

    with raises(ValueError):
        t = Date(2015, 12, 6, 16, 52, 37, 2156, 'utc')
    
    # Scale
    t = Date(2015, 12, 6, 16, 52, 37, 2156, scale='TAI')

    # Unknown scale
    with raises(ValueError):
        t = Date(2015, 12, 6, 16, 52, 37, 2156, scale='unknown')

    t = Date.now()
    assert t.d > 57373

    with raises(TypeError):
        t.d = 5
        t.s = 32.


def test_operations():
    t1 = Date(2015, 12, 6)
    t2 = t1 + 1.5
    assert t2.d == t1.d + 1
    assert t2.s == 43200.

    t3 = t1 + 1
    assert t3.d == t1.d + 1
    assert t3.s == t1.s

    t4 = t1 + datetime.timedelta(hours=2)
    assert t4.d == t1.d
    assert t4.s == t1.s + 2 * 3600

    with raises(TypeError):
        t5 = t1 + [1]


def test_change_scale():

    t = Date(2015, 12, 6)  # UTC object
    assert t.scale == "UTC"

    t2 = t.change_scale('TT')
    assert str(t2) == "2015-12-06T00:01:08.184000 TT"

    t3 = t.change_scale('GPS')
    assert str(t3) == "2015-12-06T00:00:17 GPS"

    t4 = t.change_scale('UT1')
    assert str(t4) == "2015-12-06T00:00:00.124247 UT1"

    with raises(ValueError) as e:
        t5 = t.change_scale('unknown')


def test_julian():
    t = Date(2015, 12, 18, 22, 25)
    assert t.jd == 2457375.434027778
    assert t.change_scale('TT').julian_century == 0.1596286055289367