
import numpy as np

from pytest import fixture, raises
from unittest.mock import patch

import beyond.utils.ccsds as ccsds
from beyond.dates import Date, timedelta
from beyond.orbits import Tle
from beyond.propagators.kepler import Kepler, SOIPropagator
from beyond.env.solarsystem import get_body
from beyond.orbits.listeners import LightListener, NodeListener
from beyond.orbits.man import Maneuver, DeltaCombined

import beyond.env.jpl as jpl


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

    print(repr(orb))
    # At the altitude of the ISS, two maneuvers of 28 m/s should result in roughly
    # an increment of 100 km of altitude

    with raises(ValueError):
        Maneuver(Date(2008, 9, 20, 13, 48, 21, 763091), (28, 0, 0, 0))

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


def test_man_delta_a(orb):

    # We try to dupplicate the change in altitude of the previous test
    man1 = DeltaCombined(Date(2008, 9, 20, 13, 48, 21, 763091), delta_a=50000)
    man2 = DeltaCombined(Date(2008, 9, 20, 14, 34, 39, 970298), delta_a=50000)
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

    assert 99000 < after - before < 101000


def test_man_delta_i(orb):

    i0 = orb.i

    # Search for the next ascending node
    for p in orb.iter(stop=timedelta(minutes=200), listeners=NodeListener()):
        if p.event and p.event.info.startswith("Asc"):
            man_date = p.date
            break

    man = DeltaCombined(man_date, delta_angle=np.radians(5))
    orb.maneuvers = man

    inclination, dates = [], []
    for p in orb.iter(stop=timedelta(minutes=100)):
        inclination.append(p.copy(form="keplerian").i)
        dates.append(p.date.datetime)

    # import matplotlib.pyplot as plt
    # plt.plot(dates, np.degrees(inclination))
    # plt.show()

    before = np.degrees(np.mean(inclination[:30]))
    after = np.degrees(np.mean(inclination[-30:]))

    assert 4.99 < after - before <= 5.01


def test_soi(jplfiles):

    opm = ccsds.loads("""CCSDS_OPM_VERS = 2.0
CREATION_DATE = 2019-02-22T23:22:31
ORIGINATOR = N/A

META_START
OBJECT_NAME          = N/A
OBJECT_ID            = N/A
CENTER_NAME          = EARTH
REF_FRAME            = EME2000
TIME_SYSTEM          = UTC
META_STOP

COMMENT  State Vector
EPOCH                = 2018-05-02T00:00:00.000000
X                    =  6678.000000 [km]
Y                    =     0.000000 [km]
Z                    =     0.000000 [km]
X_DOT                =     0.000000 [km/s]
Y_DOT                =     7.088481 [km/s]
Z_DOT                =     3.072802 [km/s]

COMMENT  Keplerian elements
SEMI_MAJOR_AXIS      =  6678.000000 [km]
ECCENTRICITY         =     0.000000
INCLINATION          =    23.436363 [deg]
RA_OF_ASC_NODE       =     0.000000 [deg]
ARG_OF_PERICENTER    =     0.000000 [deg]
TRUE_ANOMALY         =     0.000000 [deg]

COMMENT  Escaping Earth
MAN_EPOCH_IGNITION   = 2018-05-02T00:39:03.955092
MAN_DURATION         = 0.000 [s]
MAN_DELTA_MASS       = 0.000 [kg]
MAN_REF_FRAME        = TNW
MAN_DV_1             = 3.456791 [km/s]
MAN_DV_2             = 0.000000 [km/s]
MAN_DV_3             = 0.000000 [km/s]
""")

    planetary_step = timedelta(seconds=180)
    solar_step = timedelta(hours=12)

    jpl.create_frames()

    central = jpl.get_body('Sun')
    planets = jpl.get_body('Earth')

    opm.propagator = SOIPropagator(solar_step, planetary_step, central, planets)

    frames = set()
    for orb in opm.iter(stop=timedelta(5)):
        frames.add(orb.frame.name)

    assert not frames.symmetric_difference(['Sun', 'EME2000'])

    # Check if the last point is out of Earth sphere of influence
    assert orb.copy(frame='EME2000', form="spherical").r > SOIPropagator.SOI['Earth'].radius
