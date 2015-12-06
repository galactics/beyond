#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import raises
import datetime

from space.utils.dates import Date


def test_creation():

    t = Date(2015, 12, 5)
    assert t.d == 57361
    assert t.s == 0

    t = Date(2015, 12, 5, 12)
    assert t.d == 57361
    assert t.s == 43200

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
        t = Date(2015, 12, 6, 16, 52, 37, 2156, scale='GPS')


def test_change_scale():

    t = Date(2015, 12, 6)  # UTC object
    t2 = t.change_scale('TAI')
    assert str(t2) == "2015-12-06T00:00:36 TAI"