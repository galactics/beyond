
import numpy as np
from pytest import raises, mark, fixture

from beyond.orbits import Ephem
from beyond.io.tle import Tle
from beyond.dates import Date, timedelta
from beyond.propagators.listeners import *


def iter_listeners(orb, listeners, mode, **kwargs):

    start = kwargs.get("start", Date(2018, 4, 5, 16, 50))
    stop = kwargs.get("stop", timedelta(minutes=100))
    step = kwargs.get("step", timedelta(minutes=3))

    subkwargs = {}
    if mode == 'range-nostep':
        subkwargs['start'] = start
        subkwargs['stop'] = stop
        if not isinstance(orb, Ephem):
            subkwargs['step'] = step
    elif mode == 'range':
        subkwargs['start'] = start
        subkwargs['stop'] = stop
        subkwargs['step'] = step
    else:
        subkwargs['dates'] = Date.range(start, stop, step)

    for orb in orb.iter(listeners=listeners, **subkwargs):
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
    assert abs(p.date - Date(2018, 4, 5, 16, 58, 54, 546919)).total_seconds() <= 37e-6
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
    assert abs(p.date - Date(2018, 4, 5, 17, 51, 6, 460368)).total_seconds() <= 502e-6
    assert p.event.info == "AOS"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 56, 5, 372888)).total_seconds() <= 715e-6
    assert p.event.info == "MAX"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 18, 1, 4, 843966)).total_seconds() <= 859e-6
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
def test_radial_velocity(station, orbit, mode):

    events = iter_listeners(orbit, RadialVelocityListener(station), mode)
    p = next(events)

    assert abs(p.date - Date(2018, 4, 5, 17, 7, 28, 784242)).total_seconds() <= 2e-5
    assert p.event.info == "Radial Velocity"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 56, 5, 262811)).total_seconds() <= 3.5e-5
    assert p.event.info == "Radial Velocity"

    # Test for RadialVelocity triggered only when in sight of the station
    events = list(iter_listeners(orbit, RadialVelocityListener(station, sight=True), mode))
    assert len(events) == 1


@mark.parametrize('mode', modes)
def test_true_anomaly(molniya, mode):

    if isinstance(molniya, Ephem):
        stop = molniya[0].infos.period
    else:
        stop = molniya.infos.period

    step = timedelta(minutes=10)

    events = iter_listeners(molniya, AnomalyListener(np.pi), mode, stop=stop, step=step)
    p = next(events)
    assert abs(p.date - Date(2018,  4, 5, 18, 14, 7, 743079)).total_seconds() < 3.7e-5
    assert p.event.info == "True Anomaly = 180.00"
    with raises(StopIteration):
        p = next(events)

    events = iter_listeners(molniya, AnomalyListener(3 * np.pi / 2), mode, stop=stop, step=step)
    p = next(events)
    assert abs(p.date - Date(2018,  4, 5, 21, 33, 10, 712900)).total_seconds() < 3.7e-5
    assert p.event.info == "True Anomaly = 270.00"
    with raises(StopIteration):
        p = next(events)

    events = iter_listeners(molniya, AnomalyListener(0), mode, stop=stop, step=step)
    p = next(events)
    assert abs(p.date - Date(2018,  4, 5, 22, 0, 2, 409409)).total_seconds() < 8e-6
    assert p.event.info == "True Anomaly = 0.00"
    with raises(StopIteration):
        next(events)

    events = iter_listeners(molniya, AnomalyListener(np.pi / 2), mode, stop=stop, step=step)
    p = next(events)
    assert abs(p.date - Date(2018,  4, 5, 22, 26, 54, 209357)).total_seconds() < 3.7e-5
    assert p.event.info == "True Anomaly = 90.00"
    with raises(StopIteration):
        p = next(events)


@mark.parametrize('mode', modes)
def test_mean_anomaly(molniya, mode):

    if isinstance(molniya, Ephem):
        stop = molniya[0].infos.period
    else:
        stop = molniya.infos.period
    step = timedelta(minutes=10)

    events = iter_listeners(molniya, AnomalyListener(np.pi, "mean"), mode, stop=stop, step=step)
    p = next(events)
    assert abs(p.date - Date(2018,  4, 5, 18, 14, 7, 743079)).total_seconds() < 3.7e-5
    assert p.event.info == "Mean Anomaly = 180.00"
    with raises(StopIteration):
        p = next(events)

    events = iter_listeners(molniya, AnomalyListener(3 * np.pi / 2, "mean"), mode, stop=stop, step=step)
    p = next(events)
    assert abs(p.date - Date(2018,  4, 5, 20, 7, 5, 494487)).total_seconds() < 3.7e-5
    assert p.event.info == "Mean Anomaly = 270.00"
    with raises(StopIteration):
        p = next(events)

    events = iter_listeners(molniya, AnomalyListener(0, "mean"), mode, stop=stop, step=step)
    p = next(events)
    assert abs(p.date - Date(2018,  4, 5, 22, 0, 2, 409409)).total_seconds() < 8e-6
    assert p.event.info == "Mean Anomaly = 0.00"
    with raises(StopIteration):
        next(events)

    events = iter_listeners(molniya, AnomalyListener(np.pi / 2, "mean"), mode, stop=stop, step=step)
    p = next(events)
    assert abs(p.date - Date(2018,  4, 5, 23, 52, 59, 555389)).total_seconds() < 3.7e-5
    assert p.event.info == "Mean Anomaly = 90.00"
    with raises(StopIteration):
        p = next(events)


@mark.parametrize('mode', modes)
def test_aol(orbit, mode):

    events = iter_listeners(orbit, AnomalyListener(3 * np.pi / 2, "aol"), mode)
    p = next(events)
    assert abs(p.date - Date(2018,  4, 5, 17, 10, 49, 816867)).total_seconds() < 1.8e-5
    assert p.event.info == "Argument of Latitude = 270.00"

    with raises(StopIteration):
        next(events)

    events = iter_listeners(orbit, AnomalyListener(0, "aol"), mode)
    p = next(events)
    assert abs(p.date - Date(2018,  4, 5, 17, 33, 59, 488529)).total_seconds() < 3.7e-5
    assert p.event.info == "Argument of Latitude = 0.00"

    with raises(StopIteration):
        next(events)

    events = iter_listeners(orbit, AnomalyListener(np.pi / 2, "aol"), mode)
    p = next(events)
    assert abs(p.date - Date(2018,  4, 5, 17, 57, 7, 129464)).total_seconds() < 1.8e-5
    assert p.event.info == "Argument of Latitude = 90.00"

    with raises(StopIteration):
        next(events)

    events = iter_listeners(orbit, AnomalyListener(np.pi, "aol"), mode)
    p = next(events)
    assert abs(p.date - Date(2018,  4, 5, 18, 20, 15, 389911)).total_seconds() < 1.8e-5
    assert p.event.info == "Argument of Latitude = 180.00"

    with raises(StopIteration):
        next(events)


def test_find_event(orbit):

    kwargs = {
        "start": Date(2018, 4, 5, 16, 50),
        "stop": timedelta(minutes=200),
        "step": timedelta(minutes=3),
        "listeners": AnomalyListener(3 * np.pi / 2, "aol")
    }

    orb_iterator = orbit.iter(**kwargs)

    p = find_event(orb_iterator, "Argument of Latitude = 270.00")

    assert abs(p.date - Date(2018,  4, 5, 17, 10, 49, 816867)).total_seconds() < 1.8e-5
    assert p.event.info == "Argument of Latitude = 270.00"


def test_find_event_offset(orbit):

    kwargs = {
        "start": Date(2018, 4, 5, 16, 50),
        "stop": timedelta(minutes=200),
        "step": timedelta(minutes=3),
        "listeners": AnomalyListener(3 * np.pi / 2, "aol")
    }

    orb_iterator = orbit.iter(**kwargs)
    p = find_event(orb_iterator, "Argument of Latitude = 270.00", offset=1)

    assert abs(p.date - Date(2018,  4, 5, 18, 43, 25, 683360)).total_seconds() < 1.8e-5
    assert p.event.info == "Argument of Latitude = 270.00"


def test_find_event_two_calls(orbit):

    # Multiple calls to find_event should not be problematic
    # In this case, the second call to find_event should return
    # an Orbit object which date is at 18:43:25, but instead
    # gives the first result at 17:10:49.
    # By looking at what the iterator does, it seems that the
    # events_iterator yields two Orbit at the same date, then
    # a third at the expected date of 18:43:25
    # This problem disappears if the iterator is flattened
    # with ``orb_iterator = list(orbit.iter(**kwargs))``

    # It does not make sense that this test does not pass, but the next
    # (test_find_event_two_calls_bis) does. It drives me MAAAAD !

    kwargs = {
        "start": Date(2018, 4, 5, 16, 50),
        "stop": timedelta(minutes=200),
        "step": timedelta(minutes=3),
        "listeners": AnomalyListener(3 * np.pi / 2, "aol")
    }

    orb_iterator = orbit.iter(**kwargs)

    p = find_event(orb_iterator, "Argument of Latitude = 270.00")

    assert abs(p.date - Date(2018, 4, 5, 17, 10, 49, 816867)).total_seconds() < 1.8e-5
    assert p.event.info == "Argument of Latitude = 270.00"

    orb_iterator = orbit.iter(**kwargs)
    p = find_event(orb_iterator, "Argument of Latitude = 270.00", offset=1)

    assert abs(p.date - Date(2018,  4, 5, 18, 43, 25, 683360)).total_seconds() < 1.8e-5
    assert p.event.info == "Argument of Latitude = 270.00"

    orb_iterator = orbit.iter(**kwargs)
    with raises(RuntimeError):
        find_event(orb_iterator, "Argument of Latitude = 270.00", offset=2)


def test_find_event_two_calls_bis(orbit):

    # This case, where we search for the 90 deg Argument of Latitude
    # does not crash unexpectedly.

    kwargs = {
        "start": Date(2018, 4, 5, 16, 50),
        "stop": timedelta(minutes=200),
        "step": timedelta(minutes=3),
        "listeners": AnomalyListener(np.pi / 2, "aol")
    }

    orb_iterator = orbit.iter(**kwargs)

    p1 = find_event(orb_iterator, "Argument of Latitude = 90.00")

    assert abs(p1.date - Date(2018, 4, 5, 17, 57, 7, 129464)).total_seconds() < 1.8e-5
    assert p1.event.info == "Argument of Latitude = 90.00"

    orb_iterator2 = orbit.iter(**kwargs)
    p2 = find_event(orb_iterator2, "Argument of Latitude = 90.00", offset=1)

    assert abs(p2.date - Date(2018, 4, 5, 19, 29, 42, 991221)).total_seconds() < 1.8e-5
    assert p2.event.info == "Argument of Latitude = 90.00"

    orb_iterator3 = orbit.iter(**kwargs)
    with raises(RuntimeError):
        find_event(orb_iterator3, "Argument of Latitude = 90.00", offset=2)


def test_event_iterator(orbit):

    kwargs = {
        "start": Date(2018, 4, 5, 16, 50),
        "stop": timedelta(minutes=100),
        "step": timedelta(minutes=3),
        "listeners": [
            AnomalyListener(3 * np.pi / 2, "aol"),
            AnomalyListener(np.pi / 2, "aol"),
            ApsideListener(),
        ]
    }

    # iterate over the orbit, but filter only the AoL events, leaving
    # apsides events out
    orb_iterator = orbit.iter(**kwargs)
    events = [
        "Argument of Latitude = 270.00",
        "Argument of Latitude = 90.00",
    ]

    iterator = events_iterator(orb_iterator, *events)

    p = next(iterator)
    assert abs(p.date - Date(2018,  4, 5, 17, 10, 49, 816867)).total_seconds() < 1.8e-5
    assert p.event.info == "Argument of Latitude = 270.00"

    p = next(iterator)
    assert abs(p.date - Date(2018,  4, 5, 17, 57, 7, 129464)).total_seconds() < 1.8e-5
    assert p.event.info == "Argument of Latitude = 90.00"

    # No more events to filter in the iterator 
    with raises(StopIteration):
        p = next(iterator)


    # Same iterator construction, but this time we filter only apsudes events
    iterator = events_iterator(orbit.iter(**kwargs), "Apoapsis")

    p = next(iterator)
    assert abs(p.date - Date(2018,  4, 5, 16, 58, 54, 546919)).total_seconds() < 4e-5
    assert p.event.info == "Apoapsis"

    # No more events to filter in the iterator 
    with raises(StopIteration):
        p = next(iterator)