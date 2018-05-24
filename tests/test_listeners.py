
from pytest import raises

from beyond.dates import Date, timedelta
from beyond.orbits.listeners import *


def iter_listeners(orb, listeners):
    start = Date(2018, 4, 5, 16, 50)
    stop = timedelta(minutes=100)
    step = timedelta(minutes=3)

    for orb in orb.iter(start, stop, step, listeners=listeners):
        if orb.event:
            yield orb


def test_light(orbit):

    listeners = [LightListener(), LightListener('penumbra')]
    events = iter_listeners(orbit, listeners)

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 5, 57, 756975)).total_seconds() <= 22e-6
    assert p.event.info == "Umbra out"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 6, 6, 100362)).total_seconds() <= 30e-6
    assert p.event.info == "Penumbra out"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 18, 2, 37, 487921)).total_seconds() <= 20e-6
    assert p.event.info == "Penumbra in"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 18, 2, 45, 818272)).total_seconds() <= 70e-6
    assert p.event.info == "Umbra in"

    with raises(StopIteration):
        next(events)


def test_node(orbit):

    events = iter_listeners(orbit, NodeListener())

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 34, 1, 330583)).total_seconds() <= 20e-6
    assert p.event.info == "Asc Node"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 18, 20, 17, 235221)).total_seconds() <= 15e-6
    assert p.event.info == "Desc Node"

    with raises(StopIteration):
        next(events)


def test_apside(orbit):

    events = iter_listeners(orbit, ApsideListener())

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 16, 58, 54, 546919)).total_seconds() <= 32e-6
    assert p.event.info == "Apoapsis"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 54, 54, 87860)).total_seconds() <= 13e-6
    assert p.event.info == "Periapsis"

    with raises(StopIteration):
        next(events)


def test_station_signal(station, orbit):

    listeners = stations_listeners(station)
    events = iter_listeners(orbit, listeners)

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 51, 6, 475978)).total_seconds() <= 502e-6
    assert p.event.info == "AOS"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 56, 5, 542270)).total_seconds() <= 715e-6
    assert p.event.info == "MAX"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 18, 1, 4, 828355)).total_seconds() <= 859e-6
    assert p.event.info == "LOS"
