
from beyond.orbits import Orbit
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

