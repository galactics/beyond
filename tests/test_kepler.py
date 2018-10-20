
import numpy as np

from pytest import fixture
from unittest.mock import patch

from beyond.dates import Date, timedelta
from beyond.orbits import Tle
from beyond.propagators.kepler import Kepler
from beyond.env.solarsystem import get_body
from beyond.orbits.listeners import LightListener
from beyond.orbits.man import Maneuver


@fixture
def orb():

    orb = Tle("""0 ISS (ZARYA)
1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537""").orbit()

    orb.propagator = Kepler(
        timedelta(seconds=60),
        bodies=get_body('Earth')
    )

    return orb


def test_propagate(orb):

    assert orb.date == Date(2008, 9, 20, 12, 25, 40, 104192)

    orb2 = orb.propagate(orb.date + timedelta(minutes=121, seconds=12))

    assert orb2.date == Date(2008, 9, 20, 14, 26, 52, 104192)
    assert orb2.propagator.orbit is None  # brand new propagator

    orb3 = orb2.propagate(timedelta(minutes=12, seconds=5))

    assert orb3.date == Date(2008, 9, 20, 14, 38, 57, 104192)
    assert orb2.propagator.orbit is not None
    assert orb3.propagator.orbit is None


def test_propagate_euler(orb):

    orb.propagator.method = "euler"

    assert orb.date == Date(2008, 9, 20, 12, 25, 40, 104192)

    orb2 = orb.propagate(orb.date + timedelta(minutes=121, seconds=12))

    assert orb2.date == Date(2008, 9, 20, 14, 26, 52, 104192)
    assert orb2.propagator.orbit is None  # brand new propagator

    orb3 = orb2.propagate(timedelta(minutes=12, seconds=5))

    assert orb3.date == Date(2008, 9, 20, 14, 38, 57, 104192)
    assert orb2.propagator.orbit is not None
    assert orb3.propagator.orbit is None


def test_iter(orb):

    data = []
    for p in orb.iter(stop=timedelta(minutes=120)):
        data.append(p)

    assert len(data) == 121
    assert min(data, key=lambda x: x.date).date == orb.date
    assert max(data, key=lambda x: x.date).date == orb.date + timedelta(minutes=120)

    data2 = []
    for p in orb.iter(stop=timedelta(minutes=120)):
        data2.append(p)

    assert data[0].date == data2[0].date
    assert all(data[0] == data2[0])
    assert data[0] is not data2[0]


def test_listener(orb):

    with patch('beyond.propagators.kepler.Kepler._method', wraps=orb.propagator._method) as mock:
        data = []
        for p in orb.iter(start=Date(2008, 9, 20, 13), stop=timedelta(minutes=90), listeners=LightListener()):
            data.append(p)

        assert len(data) == 93
        assert mock.call_count == 228


def test_man(orb):

    # At the altitude of the ISS, two maneuvers of 28 m/s should result in roughly
    # an increment of 100 km of altitude
    man1 = Maneuver(Date(2008, 9, 20, 13, 48, 21, 763091), (28, 0, 0), frame="TNW")
    man2 = Maneuver(Date(2008, 9, 20, 14, 34, 39, 970298), (0, 28, 0), frame="QSW")
    orb.maneuvers = [man1, man2]

    altitude = []
    dates = []
    for p in orb.iter(stop=timedelta(minutes=300)):
        altitude.append(p.copy(form='spherical').r - p.frame.center.r)
        dates.append(p.date.datetime)

    # import matplotlib.pyplot as plt

    # plt.plot(dates, altitude)
    # plt.show()

    before = np.mean(altitude[:80])
    after = np.mean(altitude[140:])

    assert 98000 < after - before < 99000
