import numpy as np
from pytest import raises
from numpy.testing import assert_almost_equal

from beyond.orbits.orbit import AbstractOrbit
from beyond.errors import UnknownPropagatorError
from beyond.dates import Date, timedelta


def test_iter_on_dates(orbit):

    # Generate a free step ephemeris
    start = orbit.date if isinstance(orbit, AbstractOrbit) else orbit.start
    stop1 = start + timedelta(hours=3)
    step1 = timedelta(seconds=10)
    stop2 = stop1 + timedelta(hours=3)
    step2 = timedelta(seconds=120)

    dates = list(Date.range(start, stop1, step1)) + list(Date.range(stop1, stop2, step2, inclusive=True))

    ephem = orbit.ephem(dates=dates)

    assert ephem.start == start
    assert ephem.stop == stop2
    assert ephem[1].date - ephem[0].date == step1
    assert ephem[-1].date - ephem[-2].date == step2


def test_none(iss_tle):
    orbit = iss_tle.orbit().copy(form="keplerian", frame="EME2000")
    orbit.propagator = "NonePropagator"

    orb2 = orbit.propagate(timedelta(minutes=10)).copy(form="keplerian")
    assert_almost_equal(orbit.tolist(), orb2.tolist())


def test_wrong_none(iss_tle):
    orbit = iss_tle.orbit().copy(form="keplerian", frame="EME2000")
    orbit.propagator = None

    with raises(UnknownPropagatorError):
        orbit.propagate(timedelta(minutes=12))


def test_kepler(iss_tle):

    orbit = iss_tle.orbit().copy(form="keplerian", frame="EME2000")
    orbit.propagator = "Kepler"

    # Test that the orbit is perfectly periodic, and that nothing comes
    # to perturbate the path of the orbit
    orb2 = orbit.propagate(orbit.infos.period).copy(form="keplerian")

    assert orbit.date + orbit.infos.period == orb2.date
    assert_almost_equal(orbit.tolist(), orb2.tolist())


def test_j2(iss_tle):
    orbit = iss_tle.orbit().copy(form="keplerian", frame="EME2000")
    orbit.propagator = "J2"

    orb2 = orbit.propagate(orbit.infos.period).copy(form="keplerian")

    assert orbit.date + orbit.infos.period == orb2.date
    # a, e and i should not be modified
    assert_almost_equal(np.asarray(orbit[:3]), np.asarray(orb2[:3]))


def test_kepler_ephem(iss_tle):
    orbit = iss_tle.orbit().copy(form="keplerian", frame="EME2000")
    orbit.propagator = "Kepler"

    # These two calls should be equivalent, and use the orbit date as a starting point
    eph = orbit.ephem(stop=timedelta(days=1), step=timedelta(seconds=60))
    eph = orbit.ephem(start=None, stop=timedelta(days=1), step=timedelta(seconds=60))

