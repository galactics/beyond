
from datetime import timedelta

from beyond.dates import Date
from beyond.io.tle import Tle

from pytest import raises, fixture


@fixture
def start():
    return Date(2008, 9, 20, 12, 30)

stop = timedelta(hours=1)
step = timedelta(minutes=3)


@fixture
def ref_orb():
    tle = """1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"""

    return Tle(tle).orbit()


@fixture
def ephem(ref_orb, start):
    return ref_orb.ephem(start=start, stop=stop, step=step)


def test_create(ephem, start):

    assert ephem.start == start
    assert ephem.stop == start + stop
    assert len(ephem) == stop // step + 1

    assert ephem.frame.__name__ == "TEME"


def test_interpolate(ephem):

    orb = ephem.interpolate(ephem.start + timedelta(minutes=33, seconds=27), method="linear")

    assert list(orb[:3]) == [-2343119.6282188366, 4140259.6343833795, -4744905.5643210905]
    assert list(orb[3:]) == [-4568.825145249858, -5572.6341438079435, -2614.704833575209]

    orb = ephem.interpolate(ephem.start + timedelta(minutes=33, seconds=27), method="lagrange")

    assert list(orb[:3]) == [-2349933.1374301873, 4150754.2288609436, -4757989.96860434]
    assert list(orb[3:]) == [-4580.715466516539, -5588.283144821399, -2620.9683124126564]

    with raises(ValueError):
        # We ask for a value clearly out of range
        ephem.propagate(ephem.start + timedelta(days=2))

    with raises(ValueError):
        ephem.interpolate(ephem.start + timedelta(minutes=33, seconds=27), method='dummy')


def test_subephem(ref_orb, ephem, start):

    # Same ephemeris
    subephem = ephem.ephem()
    assert subephem.start == ephem.start
    assert subephem.stop == ephem.stop

    # resampling of the ephem
    subephem = ref_orb.ephem(start=start, stop=stop, step=timedelta(minutes=1))
    assert subephem.start == ephem.start
    assert subephem.stop == ephem.stop
    assert len(subephem) == stop // timedelta(minutes=1) + 1

    # resample but with less points
    subephem = ephem.ephem(step=timedelta(minutes=10))
    assert subephem.start == ephem.start
    assert subephem.stop == ephem.stop
    assert len(subephem) == stop // timedelta(minutes=10) + 1

    # Trying to generate ephemeris out of the range of the current one
    with raises(ValueError):
        subephem = ephem.ephem(start=ephem.start - timedelta(minutes=10), strict=True)
    with raises(ValueError):
        subephem = ephem.ephem(stop=ephem.stop + timedelta(minutes=10), strict=True)

    # Changing of the starting date but with concervation of the step
    # (i.e. the start date provided is on already contained in the ephem object)
    subephem = ephem.ephem(start=ephem.start + timedelta(minutes=9))
    assert subephem.start == ephem.start + timedelta(minutes=9)
    assert subephem.stop == ephem.stop
    assert len(subephem) == (subephem.stop - subephem.start) // step + 1

    # Changing of the starting date, with an arbitraty date
    # (i.e. will take the next available point)
    subephem = ephem.ephem(start=ephem.start + timedelta(minutes=10, seconds=12))
    assert subephem.start == ephem.start + timedelta(minutes=12)
    assert subephem.stop == ephem.stop
    assert len(subephem) == (subephem.stop - subephem.start) // step + 1

    # Creation of a shorter ephemeris, with the same start, and same step
    subephem = ephem.ephem(stop=timedelta(minutes=12))
    assert subephem.start == ephem.start
    assert subephem.stop == ephem.start + timedelta(minutes=12)
    assert len(subephem) == (subephem.stop - subephem.start) // step + 1

    # Same as above, but as the stop date doesn't match one of the original ephemeris points,
    # the last point of the newly generated ephemeris will be on the previous point.
    subephem = ephem.ephem(stop=timedelta(minutes=11))
    assert subephem.start == ephem.start
    assert subephem.stop == ephem.start + timedelta(minutes=9)
    assert len(subephem) == (subephem.stop - subephem.start) // step + 1


def test_iter_on_dates(ephem):

    # Generate a free step ephemeris
    start = ephem.start
    stop1 = start + (ephem.stop - ephem.start) / 2
    step1 = timedelta(seconds=60)
    stop2 = ephem.stop
    step2 = timedelta(seconds=120)

    dates = list(Date.range(start, stop1, step1)) + list(Date.range(stop1, stop2, step2, inclusive=True))

    subephem = ephem.ephem(dates=dates)

    assert subephem.start == ephem.start
    assert subephem.stop == ephem.stop

    assert subephem[1].date - subephem[0].date == step1
    assert subephem[-1].date - subephem[-2].date == step2


def test_getitem(ephem):

    # Evolution of the Z component
    z = ephem[:, 2]

    assert len(z) == len(ephem)

    with raises(IndexError):
        # too many dimensions
        ephem[:, 1, :]


def test_tolerant(ephem):

    # Test for out of range starting and stoping points

    start = Date(2008, 9, 20, 12, 15)
    stop = timedelta(minutes=24)

    with raises(ValueError):
        ephem.ephem(start=start, stop=stop)

    with raises(ValueError):
        ephem.ephem(stop=timedelta(hours=1.5))

    subephem = ephem.ephem(start=start, stop=stop, strict=False)

    assert subephem.start == ephem.start
    assert subephem.stop == start + stop

    subephem = ephem.ephem(stop=timedelta(hours=1.5), strict=False)
    assert subephem.start == ephem.start
    assert subephem.stop == ephem.stop

    # Case where both start and stop are BEFORE the first date of the initial ephem
    subephem = ephem.ephem(start=start, stop=timedelta(minutes=6), strict=False)
    assert len(subephem) == 0

    # Case where both start and stop are AFTER the last date of the initial ephem
    subephem = ephem.ephem(start=ephem.start + timedelta(hours=2), stop=timedelta(minutes=6), strict=False)
    assert len(subephem) == 0

    # Case where start is before and stop is after
    subephem = ephem.ephem(start=start, stop=timedelta(hours=1, minutes=15), strict=False)
    assert subephem.start == ephem.start
    assert subephem.stop == ephem.stop
