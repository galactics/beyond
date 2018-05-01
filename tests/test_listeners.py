
from pytest import fixture, raises

from beyond.dates import Date, timedelta
from beyond.orbits import Tle
from beyond.orbits.listeners import *


@fixture(scope='session', params=["orb", "ephem"])
def orbit(request):

    orb = Tle("""ISS (ZARYA)
1 25544U 98067A   18124.55610684  .00001524  00000-0  30197-4 0  9997
2 25544  51.6421 236.2139 0003381  47.8509  47.6767 15.54198229111731""").orbit()

    if request.param == "orb":
        return orb
    else:
        start = Date(2018, 4, 5, 16, 50)
        stop = timedelta(minutes=103)
        step = timedelta(minutes=0.25)

        return orb.ephem(start, stop, step)


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
    assert abs(p.date - Date(2018, 4, 5, 17, 5, 57, 756975)).microseconds <= 22
    assert p.event.info == "Umbra out"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 6, 6, 100362)).microseconds <= 30
    assert p.event.info == "Penumbra out"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 18, 2, 37, 487921)).microseconds <= 20
    assert p.event.info == "Penumbra in"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 18, 2, 45, 818272)).microseconds <= 70
    assert p.event.info == "Umbra in"

    with raises(StopIteration):
        next(events)


def test_node(orbit):

    events = iter_listeners(orbit, NodeListener())

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 34, 1, 330583)).microseconds <= 20
    assert p.event.info == "Asc Node"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 18, 20, 17, 235221)).microseconds <= 15
    assert p.event.info == "Desc Node"

    with raises(StopIteration):
        next(events)


def test_apside(orbit):

    events = iter_listeners(orbit, ApsideListener())

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 16, 58, 54, 546919)).microseconds <= 32
    assert p.event.info == "Apoapsis"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 54, 54, 87860)).microseconds <= 13
    assert p.event.info == "Periapsis"

    with raises(StopIteration):
        next(events)


def test_station_signal(station, orbit):

    listeners = stations_listeners(station)
    events = iter_listeners(orbit, listeners)

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 51, 6, 475978)).microseconds <= 502
    assert p.event.info == "AOS"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 17, 56, 5, 542270)).microseconds <= 715
    assert p.event.info == "MAX"

    p = next(events)
    assert abs(p.date - Date(2018, 4, 5, 18, 1, 4, 828355)).microseconds <= 859
    assert p.event.info == "LOS"
