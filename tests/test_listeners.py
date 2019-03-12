
from pytest import raises, mark

from beyond.orbits import Ephem
from beyond.dates import Date, timedelta
from beyond.orbits.listeners import *

"""Here the reference in term of time is given by the TLE propagation.
The ephemeris interpolation generate a little time difference, which is
why we use an 'epsilon'.
"""


def iter_listeners(orb, listeners, mode):

    start = Date(2018, 4, 5, 16, 50)
    stop = timedelta(minutes=100)
    step = timedelta(minutes=3)

    kwargs = {}
    if mode == 'range-nostep':
        kwargs['start'] = start
        kwargs['stop'] = stop
        if not isinstance(orb, Ephem):
            kwargs['step'] = step
    elif mode == 'range':
        kwargs['start'] = start
        kwargs['stop'] = stop
        kwargs['step'] = step
    else:
        kwargs['dates'] = Date.range(start, stop, step)

    for orb in orb.iter(listeners=listeners, **kwargs):
        if orb.event:
            yield orb

modes = ['range', 'dates', 'range-nostep']


@mark.parametrize('mode', modes)
def test_light(orbit, mode):

    listeners = [LightListener(), LightListener('penumbra')]
    events = iter_listeners(orbit, listeners, mode)

    # Maybe the difference of date precision between 'exit' and 'entry' while computing from
    # a Ephem can be explained by the fact that the 'entry' events are further from
    # a point of the ephemeris than the 'exit' ones.

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 5, 57, 760757)).total_seconds() <= 8e-6
    assert p.event.info == "Umbra exit"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 6, 6, 20177)).total_seconds() <= 8e-6
    assert p.event.info == "Penumbra exit"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 18, 2, 37, 568025)).total_seconds() <= 16e-6
    assert p.event.info == "Penumbra entry"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 18, 2, 45, 814490)).total_seconds() <= 16e-6
    assert p.event.info == "Umbra entry"

    with raises(StopIteration):
        next(events)


@mark.parametrize('mode', modes)
def test_node(orbit, mode):

    events = iter_listeners(orbit, NodeListener(), mode)

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 33, 59, 488549)).total_seconds() <= 20e-6
    assert p.event.info == "Asc Node"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 18, 20, 15, 389928)).total_seconds() <= 17e-6
    assert p.event.info == "Desc Node"

    with raises(StopIteration):
        next(events)


@mark.parametrize('mode', modes)
def test_apside(orbit, mode):

    events = iter_listeners(orbit, ApsideListener(), mode)

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 16, 58, 54, 546919)).total_seconds() <= 36e-6
    assert p.event.info == "Apoapsis"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 54, 54, 87860)).total_seconds() <= 13e-6
    assert p.event.info == "Periapsis"

    with raises(StopIteration):
        next(events)


@mark.parametrize('mode', modes)
def test_station_signal(station, orbit, mode):

    listeners = stations_listeners(station)
    events = iter_listeners(orbit, listeners, mode)

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 51, 6, 475978)).total_seconds() <= 502e-6
    assert p.event.info == "AOS"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 56, 5, 542270)).total_seconds() <= 715e-6
    assert p.event.info == "MAX"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 18, 1, 4, 828355)).total_seconds() <= 859e-6
    assert p.event.info == "LOS"


@mark.parametrize('mode', modes)
def test_terminator(orbit, mode):

    events = iter_listeners(orbit, TerminatorListener(), mode)

    p = next(events)

    assert abs(p.date - Date(2018, 4, 5, 17, 11, 13, 908911)).total_seconds() <= 2e-5
    assert p.event.info == "Day Terminator"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 57, 33, 123730)).total_seconds() <= 2.5e-5
    assert p.event.info == "Night Terminator"


@mark.parametrize('mode', modes)
def test_zero_doppler(station, orbit, mode):

    events = iter_listeners(orbit, ZeroDopplerListener(station), mode)
    p = next(events)

    assert abs(p.date - Date(2018, 4, 5, 17, 7, 29, 581221)).total_seconds() <= 2e-5
    assert p.event.info == "Zero Doppler"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 56, 5, 511934)).total_seconds() <= 3.5e-5
    assert p.event.info == "Zero Doppler"

    # Test for ZeroDoppler triggered only when in sight of the station
    events = list(iter_listeners(orbit, ZeroDopplerListener(station, sight=True), mode))
    assert len(events) == 1
