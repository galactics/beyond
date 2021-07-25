#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import raises, mark
from unittest.mock import patch
from pickle import dumps, loads
from datetime import datetime, timedelta, timezone

import numpy as np

from beyond.dates.eop import Eop
from beyond.dates.date import Date, DateError, UnknownScaleError, DateRange


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

    # Datetime object
    t = Date(datetime(2015, 12, 6, 12, 20))
    assert t.d == 57362
    assert t.s == 44400

    # Timezone handling (this is supposend to be the same time as the one just above)
    tz = timezone(timedelta(hours=2))
    t = Date(datetime(2015, 12, 6, 14, 20, tzinfo=tz))
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
    assert t.datetime == datetime(2016, 1, 1)

    t = Date(57388)
    assert t.d == 57388
    assert t.s == 0.

    t = Date(57388.5)
    assert t.d == 57388
    assert t.s == 43200

    # Wrong number of arguments
    with raises(TypeError):
        t = Date((2015, 12, 6))

    with raises(TypeError):
        t = Date(2015, 12, 6, 16, 52, 37, 2156, 'utc')

    # Scale
    t = Date(2015, 12, 6, 16, 52, 37, 2156, scale='TAI')

    # Unknown scale
    with raises(UnknownScaleError):
        t = Date(2015, 12, 6, 16, 52, 37, 2156, scale='unknown')

    t = Date.now()
    assert t.d > 57373

    with raises(TypeError):
        t.d = 5
        t.s = 32.


def test_operations():
    t1 = Date(2015, 12, 6)

    t2 = t1 + timedelta(hours=2)
    assert t2.d == t1.d
    assert t2.s == t1.s + 2 * 3600

    with raises(TypeError):
        t2 = t1 + 1

    t2 = t1 - timedelta(hours=12)
    assert t2.d == t1.d - 1
    assert t2.s == 43200.

    t2 = t1 - datetime(2015, 12, 4)
    assert type(t2) is timedelta
    assert t2.days == 2

    t2 = t1 - Date(2015, 12, 4)
    assert type(t2) is timedelta
    assert t2.days == 2

    with raises(TypeError):
        t2 = t1 - 2.5

    # Test if Date is hashable
    d = {
        t1: "test",
        t2: "test2"
    }
    t1bis = t1.change_scale('UT1')
    assert d[t1bis] == "test"


def test_change_scale():

    with patch('beyond.dates.date.EopDb.get') as m:

        m.return_value = Eop(x=0, y=0, dx=0, dy=0, dpsi=0, deps=0, lod=0, ut1_utc=0.1242558, tai_utc=36.0)

        t = Date(2015, 12, 6)  # UTC object
        assert str(t.scale) == "UTC"

        t2 = t.change_scale('TT')
        assert str(t2) == "2015-12-06T00:01:08.184000 TT"

        t3 = t.change_scale('GPS')
        assert str(t3) == "2015-12-06T00:00:17 GPS"

        t4 = t.change_scale('UT1')
        assert str(t4) == "2015-12-06T00:00:00.124256 UT1"

        t5 = t.change_scale('TDB')
        assert str(t5) == "2015-12-06T00:01:08.183225 TDB"

        assert str(t5.change_scale('UTC')) == "2015-12-06T00:00:00 UTC"

        with raises(ValueError):
            t.change_scale('unknown')


def test_barycenter():
    with patch('beyond.dates.date.EopDb.get') as m:
        m.return_value = Eop(x=0, y=0, dx=0, dy=0, dpsi=0, deps=0, lod=0, ut1_utc=-0.463326, tai_utc=32.0)

        t = Date(2004, 5, 14, 16, 43)  # UTC

        t2 = t.change_scale('TT')
        assert str(t2) == "2004-05-14T16:44:04.184000 TT"

        t3 = t2.change_scale('TDB')
        assert str(t3) == "2004-05-14T16:44:04.185254 TDB"

        # This value is the one in the example of Vallado, but it implies
        # implementing the complete analytical formula (100+ terms)
        # assert str(t3) == "2004-05-14T16:44:04.185640 TDB"


def test_julian():

    with patch('beyond.dates.date.EopDb.get') as m:
        m.return_value = Eop(x=0, y=0, dx=0, dy=0, dpsi=0, deps=0, lod=0, ut1_utc=0.10362957986110499, tai_utc=36.0)

        t = Date(2015, 12, 18, 22, 25)
        assert t.mjd == 57374.93402777778
        assert t.jd == 2457375.434027778
        assert t.change_scale('TT').julian_century == 0.1596286055289367


def test_comparison():

    with patch('beyond.dates.date.EopDb.get') as m:
        m.return_value = Eop(x=0, y=0, dx=0, dy=0, dpsi=0, deps=0, lod=0, ut1_utc=0.10362957986110499, tai_utc=36.0)

        # Same scale
        t1 = Date(2016, 11, 14)
        t2 = Date(2016, 11, 14, 12)
        assert t2 > t1

        # Different scale
        t1 = Date(2016, 11, 14)     # 00:00:36 in TAI
        t2 = Date(2016, 11, 14, scale='TAI')

        assert t2 < t1
        assert t1 > t2

        t1 = Date(2016, 11, 14)
        t2 = Date(2016, 11, 14, 0, 0, 36, scale='TAI')
        assert t1 == t2
        assert t1 >= t2
        assert t1 <= t2


def test_leap_second():

    with patch('beyond.dates.date.EopDb.get') as m:
        m.return_value = Eop(x=0, y=0, dx=0, dy=0, dpsi=0, deps=0, lod=0, ut1_utc=0., tai_utc=36.0)

        t1 = Date(2016, 12, 31, 23, 59, 59)

    with patch('beyond.dates.date.EopDb.get') as m:
        m.return_value = Eop(x=0, y=0, dx=0, dy=0, dpsi=0, deps=0, lod=0, ut1_utc=0., tai_utc=37.0)
        t2 = Date(2017, 1, 1, 0, 0, 0)

    t3 = Date(2017, 1, 1, 0, 0, 36, scale='TAI')

    assert t1 == Date(2017, 1, 1, 0, 0, 35, scale='TAI')
    assert t2 == Date(2017, 1, 1, 0, 0, 37, scale='TAI')

    assert t2 - t1 == timedelta(seconds=2)
    assert t3 - t1 == timedelta(seconds=1)


def test_range():

    start = Date(2016, 11, 16, 22, 38)
    stop = timedelta(hours=1)
    step = timedelta(seconds=30)

    # classic range
    l1 = list(Date.range(start, stop, step))
    assert len(l1) == stop // step

    # Inclusive range
    l2 = list(Date.range(start, stop, step, inclusive=True))
    assert len(l2) == stop // step + 1

    # stop as a Date object
    stop = Date(2016, 11, 16, 22, 40)
    l3 = Date.range(start, stop, step)

    # Inverse order
    start = Date(2016, 11, 16, 22, 40)
    stop = - timedelta(minutes=2)
    step = - timedelta(seconds=30)

    l4 = list(Date.range(start, stop, step))
    assert len(l4) == stop // step

    # Error when the date range (start/stop) is not coherent with the step
    with raises(ValueError):
        list(Date.range(start, stop, -step))

    # Error when the step is null.
    with raises(ValueError):
        list(Date.range(start, stop, timedelta(0)))


def test_pickle():

    date1 = Date(2018, 5, 8, 15, 55, 52, 232)

    txt = dumps(date1)
    date2 = loads(txt)

    assert date1 == date2
    assert date1.scale.name == date2.scale.name

    assert date1.eop.x == date2.eop.x
    assert date1.eop.y == date2.eop.y
    assert date1.eop.dx == date2.eop.dx
    assert date1.eop.dy == date2.eop.dy
    assert date1.eop.deps == date2.eop.deps
    assert date1.eop.dpsi == date2.eop.dpsi
    assert date1.eop.lod == date2.eop.lod
    assert date1.eop.ut1_utc == date2.eop.ut1_utc
    assert date1.eop.tai_utc == date2.eop.tai_utc

    assert date1.change_scale('UT1') == date2.change_scale('UT1')


@mark.mpl
def test_plot():
    # This test is ran only if matplotlib is installed

    import matplotlib.pyplot as plt

    fig = plt.figure()
    dates = list(Date.range(Date.now(), timedelta(1), timedelta(minutes=10)))
    plt.plot(dates, np.random.rand(len(dates)))
    plt.draw()  # draws the figure, but does not show it
    plt.close(fig)  # Delete the figure


def test_daterange():

    start = Date(2016, 11, 16, 22, 38)
    stop = timedelta(hours=1)
    step = timedelta(seconds=30)

    # classic range
    l1 = Date.range(start, stop, step)
    assert len(l1) == stop // step
    assert len(l1) == len(list(l1))

    # Inclusive range
    l2 = Date.range(start, stop, step, inclusive=True)
    assert len(l2) == stop // step + 1
    assert len(l2) == len(list(l2))

    r = Date.range(start, stop, step)
    rlist = list(r)
    assert len(r) == len(rlist)
    assert isinstance(r, DateRange)
    assert rlist[0] == r.start
    assert rlist[-1] == r.stop - r.step

    r = Date.range(start, stop, step, inclusive=True)
    rlist = list(r)
    assert len(r) == len(rlist)
    assert isinstance(r, DateRange)
    assert rlist[0] == r.start
    assert rlist[-1] == r.stop

    # Addition of ranges
    # r1 = Date.range(start, stop, step)
    # r2 = Date.range(start + stop, stop, step * 2)

    # r = r1 + r2
    # assert isinstance(r, DateRange)
    # assert r.start == start
    # assert r.stop == start + 2*stop
    # assert r.steps == {step, step*2}

    # l = r
    # assert len(l) == stop // step + stop // (step * 2)

    # stop as a Date object
    stop = Date(2016, 11, 16, 22, 40)
    l3 = Date.range(start, stop, step)

    # Inverse order
    start = Date(2016, 11, 16, 22, 40)
    stop = - timedelta(minutes=2)
    step = - timedelta(seconds=30)

    l4 = Date.range(start, stop, step)
    assert len(l4) == stop // step

    # Error when the date range (start/stop) is not coherent with the step
    with raises(ValueError):
        Date.range(start, stop, -step)

    # Error when the step is null.
    with raises(ValueError):
        Date.range(start, stop, timedelta(0))


def test_daterange2():

    start = Date(2021, 2, 9, 22, 35)
    stop = timedelta(hours=1, seconds=37)
    step = timedelta(seconds=17)

    r = Date.range(start, stop, step)
    l = list(r)

    assert np.ceil((r.stop - r.start) / r.step) == len(l)
    assert len(r) == len(l)
    assert l[0] == r.start
    assert l[-1] < r.stop

    r = Date.range(start, stop, step, inclusive=True)
    l = list(r)

    assert len(r) == len(l)
    assert l[0] == r.start
    assert l[-1] < r.stop