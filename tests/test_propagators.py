import numpy as np
from pytest import raises
from numpy.testing import assert_almost_equal

from beyond.orbits import Orbit
from beyond.errors import UnknownPropagatorError
from beyond.dates import Date, timedelta


def test_iter_on_dates(orbit):

    # Generate a free step ephemeris
    start = orbit.date if isinstance(orbit, Orbit) else orbit.start
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
