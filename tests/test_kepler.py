
import numpy as np

from contextlib import contextmanager
from pytest import fixture, raises, mark
from unittest.mock import patch

import beyond.io.ccsds as ccsds
from beyond.dates import Date, timedelta
from beyond.io.tle import Tle
from beyond.propagators.kepler import Kepler, SOIPropagator
from beyond.env.solarsystem import get_body
from beyond.orbits.listeners import LightListener, NodeListener, find_event, ApsideListener
from beyond.orbits.man import ImpulsiveMan, KeplerianImpulsiveMan, ContinuousMan, KeplerianContinuousMan

import beyond.env.jpl as jpl


@fixture
def orbit_kepler(iss_tle):

    orbit = iss_tle.orbit()

    orbit.propagator = Kepler(
        timedelta(seconds=60),
        bodies=get_body('Earth')
    )

    return orbit


@fixture
def molniya_kepler(molniya_tle):

    molniya = molniya_tle.orbit()

    molniya.propagator = Kepler(
        timedelta(seconds=120),
        bodies=get_body('Earth')
    )

    return molniya


@contextmanager
def mock_step(orb):
    with patch('beyond.propagators.kepler.Kepler._make_step', wraps=orb.propagator._make_step) as mock:
        yield mock


def count_steps(td, step, inclusive=True):
    """Count how many steps it take to travel td

    Args:
        td (timedelta)
        step (timedelta)
    Return:
        int
    """

    inclusive = 1 if inclusive else 0
    return abs(td) // step + inclusive


def test_propagate_rk4(orbit_kepler):

    orbit_kepler.propagator.method = Kepler.RK4

    assert orbit_kepler.date == Date(2018, 5, 4, 13, 20, 47, 630976)

    # simple propagation with a Date object
    orb2 = orbit_kepler.propagate(orbit_kepler.date + timedelta(minutes=121, seconds=12))

    assert orb2.date == Date(2018, 5, 4, 15, 21, 59, 630976)
    assert orb2.propagator.orbit is None  # brand new propagator

    # simple propagation with a timedelta object
    orb3 = orb2.propagate(timedelta(minutes=12, seconds=5))

    # Check if the propagator.orbit is initializd for orb2
    # and not yet initialized for orb3
    assert orb3.date == Date(2018, 5, 4, 15, 34, 4, 630976)
    assert orb2.propagator.orbit is not None
    assert orb3.propagator.orbit is None

    assert np.allclose(
        orb3,
        [-2267347.5906591383, 3865612.1569156954, -5093932.5567979375, -5238.634675262262, -5326.282920539333, -1708.6895889357945]
    )

    # simple propagation with a negative step
    orb4 = orb3.propagate(timedelta(minutes=-15))
    assert orb4.date == orb3.date - timedelta(minutes=15)


def test_micro_step(orbit_kepler):

    with mock_step(orbit_kepler) as mock:
        # Propagation with micro-step (< to the Kepler propagator step size)
        orb2 = orbit_kepler.propagate(orbit_kepler.date + timedelta(seconds=20))
        assert orb2.date == orbit_kepler.date + timedelta(seconds=20)

        assert mock.call_count == 7

    with mock_step(orbit_kepler) as mock:    
        # negative micro-step
        orb2 = orbit_kepler.propagate(orbit_kepler.date - timedelta(seconds=20))
        assert orb2.date == orbit_kepler.date - timedelta(seconds=20)
        assert mock.call_count == 7


def test_propagate_euler(orbit_kepler):

    orbit_kepler.propagator.method = Kepler.EULER

    assert orbit_kepler.date == Date(2018, 5, 4, 13, 20, 47, 630976)

    orb2 = orbit_kepler.propagate(orbit_kepler.date + timedelta(minutes=121, seconds=12))

    assert orb2.date == Date(2018, 5, 4, 15, 21, 59, 630976)
    assert orb2.propagator.orbit is None  # brand new propagator

    orb3 = orb2.propagate(timedelta(minutes=12, seconds=5))

    assert orb3.date == Date(2018, 5, 4, 15, 34, 4, 630976)
    assert orb2.propagator.orbit is not None
    assert orb3.propagator.orbit is None

    assert np.allclose(
        np.array(orb3),
        [-880124.9759610161, -10453560.873778934, 6457874.859314914, 4109.877000752121, 1881.4035807734163, 2961.5286009903316]
    )


def test_propagate_dopri(orbit_kepler):

    orbit_kepler.propagator.method = Kepler.DOPRI

    assert orbit_kepler.date == Date(2018, 5, 4, 13, 20, 47, 630976)

    orb2 = orbit_kepler.propagate(orbit_kepler.date + timedelta(minutes=121, seconds=12))

    assert orb2.date == Date(2018, 5, 4, 15, 21, 59, 630976)
    assert orb2.propagator.orbit is None  # brand new propagator

    orb3 = orb2.propagate(timedelta(minutes=12, seconds=5))

    assert orb3.date == Date(2018, 5, 4, 15, 34, 4, 630976)
    assert orb2.propagator.orbit is not None
    assert orb3.propagator.orbit is None

    assert np.allclose(
        np.array(orb3),
        [-2267319.8725340427, 3865646.423538732, -5093927.810461366, -5238.647479926973, -5326.249640066392, -1708.7264386468821]
    )


def test_iter(orbit_kepler):

    data = []
    for p in orbit_kepler.iter(stop=timedelta(minutes=120)):
        data.append(p)

    assert len(data) == 121
    assert min(data, key=lambda x: x.date).date == orbit_kepler.date
    assert max(data, key=lambda x: x.date).date == orbit_kepler.date + timedelta(minutes=120)

    data2 = []
    for p in orbit_kepler.iter(stop=timedelta(minutes=120)):
        data2.append(p)

    assert data[0].date == data2[0].date
    assert all(data[0] == data2[0])
    assert data[0] is not data2[0]

    # Test retropolation then extrapolation

    # same but with step interpolation


def test_iter_on_dates(orbit_kepler):
    # Generate a free step ephemeris
    start = orbit_kepler.date
    stop = timedelta(hours=3)
    step = timedelta(seconds=10)

    drange = Date.range(start, stop, step, inclusive=True)
    ephem = orbit_kepler.ephem(dates=drange)

    assert ephem.start == start
    assert ephem.stop == start + stop
    assert ephem[1].date - ephem[0].date == step


def test_duty_cycle(orbit_kepler):

    with mock_step(orbit_kepler) as mock:
        date = Date(2018, 5, 4, 15)
        orbit_kepler.propagate(date)

        assert mock.call_count == count_steps(orbit_kepler.date - date, orbit_kepler.propagator.step)
        assert mock.call_count == 100

    with mock_step(orbit_kepler) as mock:
        date = orbit_kepler.date - timedelta(seconds=652)
        orbit_kepler.propagate(date)

        assert mock.call_count == count_steps(orbit_kepler.date - date, orbit_kepler.propagator.step)
        assert mock.call_count == 11

    with mock_step(orbit_kepler) as mock:

        start = Date(2018, 5, 4, 13)
        stop = start + timedelta(minutes=90)

        data = []
        for p in orbit_kepler.iter(start=start, stop=stop):
            data.append(p)

        assert len(data) == 91
        assert data[0].date == start
        assert data[-1].date == stop
        assert mock.call_count == (
            count_steps(orbit_kepler.date - start, orbit_kepler.propagator.step)
            + count_steps(stop - start, orbit_kepler.propagator.step, False)
        )
        # assert mock.call_count == 125


def test_listener(orbit_kepler):
    with mock_step(orbit_kepler) as mock:

        start = Date(2018, 5, 4, 13)
        stop = start + timedelta(minutes=90)

        data = []
        for p in orbit_kepler.iter(start=start, stop=stop, listeners=LightListener()):
            data.append(p)

        assert len(data) == 93
        assert mock.call_count == (
            count_steps(orbit_kepler.date - start, orbit_kepler.propagator.step)
            + count_steps(stop - start, orbit_kepler.propagator.step, False)
        )
        # assert mock.call_count == 111

        events = [x for x in data if x.event]
        assert len(events) == 2
        assert events[0].date == Date(2018, 5, 4, 13, 8, 38, 869128)
        assert events[0].event.info == "Umbra exit"

        assert events[1].date == Date(2018, 5, 4, 14, 5, 21, 256924)
        assert events[1].event.info == "Umbra entry"

    with mock_step(orbit_kepler) as mock:

        start = Date(2018, 5, 4, 13)
        stop = start + timedelta(minutes=90)

        data = []
        for p in orbit_kepler.iter(start=start, stop=stop, listeners=ApsideListener()):
            data.append(p)

        assert len(data) == 93
        assert mock.call_count == (
            count_steps(orbit_kepler.date - start, orbit_kepler.propagator.step)
            + count_steps(stop - start, orbit_kepler.propagator.step, False)
        )
        # assert mock.call_count == 125

        events = [x for x in data if x.event]
        assert len(events) == 2
        assert str(events[0].date) == "2018-05-04T13:08:30.765143 UTC"
        assert events[0].event.info == "Periapsis"

        assert str(events[1].date) == "2018-05-04T13:54:50.178229 UTC"
        assert events[1].event.info == "Apoapsis"


def test_man(orb):

    # At the altitude of the ISS, two maneuvers of 28 m/s should result in roughly
    # an increment of 100 km of altitude

    with raises(ValueError):
        ImpulsiveMan(Date(2008, 9, 20, 13, 48, 21, 763091), (28, 0, 0, 0))

    peri = find_event('Periapsis', orb.iter(stop=timedelta(minutes=180), listeners=ApsideListener()), offset=1)
    man1 = ImpulsiveMan(peri.date, (28, 0, 0), frame="TNW")
    orb.maneuvers = [man1]

    apo = find_event('Apoapsis', orb.iter(stop=timedelta(minutes=180), listeners=ApsideListener()), offset=1)
    # This should also work, but doesn't return the exact same date as
    # the uncommented apogee search.
    # apo = find_event('Apoapsis', orb.iter(start=peri.date - 10*orb.propagator.step, stop=timedelta(minutes=180), listeners=ApsideListener()))

    man2 = ImpulsiveMan(apo.date, (28, 0, 0), frame="TNW")


    orb.maneuvers = [man1, man2]

    altitude = []
    eccentricity = []
    dates = []
    for p in orb.iter(stop=timedelta(minutes=300)):
        altitude.append(p.copy(form='spherical').r - p.frame.center.r)
        eccentricity.append(p.copy(form="keplerian").e)
        dates.append(p.date.datetime)

    # import matplotlib.pyplot as plt
    # fig = plt.figure()
    # g1 = fig.add_subplot(111)
    # g2 = g1.twinx()
    # p1, = g1.plot(dates, altitude, label="altitude", color="orange")
    # p2, = g2.plot(dates[:80], eccentricity[:80], label="eccentricity")
    # g2.plot(dates[150:], eccentricity[150:], label="eccentricity")

    # g1.set_ylabel("Altitude (m)")
    # g2.set_ylabel("Eccentricity")
    # g1.yaxis.label.set_color(p1.get_color())
    # g2.yaxis.label.set_color(p2.get_color())
    # g2.set_yscale('log')
    # plt.tight_layout()
    # plt.show()

    alt_before = np.mean(altitude[:80])
    alt_after = np.mean(altitude[150:])

    ecc_before = np.mean(eccentricity[:80])
    ecc_after = np.mean(eccentricity[150:])

    assert abs(ecc_before - 6.7e-4) < 1e-6
    assert abs(ecc_after - 7.46e-4) < 1e-6
    # assert abs(ecc_after - 6.57e-4) < 1e-6

    assert str(man1.date) == "2008-09-20T14:06:09.988586 UTC"
    assert str(man2.date) == "2008-09-20T14:52:55.773122 UTC"
    # assert str(man2.date) == "2008-09-20T14:52:28.201126 UTC"

    assert 97900 < alt_after - alt_before < 98000


def test_man_delta_a(orb):

    # We try to dupplicate the change in altitude of the previous test
    man1 = KeplerianImpulsiveMan(Date(2008, 9, 20, 13, 48, 21, 763091), delta_a=50000)
    man2 = KeplerianImpulsiveMan(Date(2008, 9, 20, 14, 34, 39, 970298), delta_a=50000)
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

    asc = find_event("Asc Node", orb.iter(stop=timedelta(minutes=200), listeners=NodeListener()))

    man = KeplerianImpulsiveMan(asc.date, delta_angle=np.radians(5))
    orb.maneuvers = man

    inclination, dates = [], []
    for p in orb.iter(stop=timedelta(minutes=100)):
        inclination.append(p.copy(form="keplerian").i)
        dates.append(p.date.datetime)

    # import matplotlib.pyplot as plt
    # plt.figure()
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
