
from datetime import timedelta

from space.utils import Date
from space.orbits import Tle

from pytest import raises, fixture

start = Date(2008, 9, 20, 12, 30)
stop = timedelta(hours=1)
step = timedelta(minutes=3)


@fixture
def ref_orb():
    tle = """1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
    2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"""

    return Tle(tle).orbit()


@fixture
def ephem(ref_orb):
    return ref_orb.ephem(start, stop, step)


def test_create(ephem):

    assert ephem.start == start
    assert ephem.stop == start + stop
    assert len(ephem) == stop // step + 1

    assert ephem.frame.__name__ == "TEME"


def test_interpolate(ephem):

    orb = ephem.interpolate(ephem.start + timedelta(hours=0.5), method="linear")

    assert list(orb[:3]) == [-1345306.8788385859, 5181620.4607680216, -4088075.611075501]
    assert list(orb[3:]) == [-5080.8194130861202, -4325.1407145624016, -3821.7458439122233]

    orb = ephem.interpolate(ephem.start + timedelta(hours=0.5), method="lagrange")

    assert list(orb[:3]) == [-1345304.9541785978, 5181617.05590453, -4088071.6593303955]
    assert list(orb[3:]) == [-5080.8211218599981, -4325.1688590092863, -3821.7340028755452]

    with raises(ValueError):
        # We ask for a value clearly out of range
        ephem.propagate(ephem.start + timedelta(days=2))


def test_subephem(ref_orb, ephem):

    # Same ephemeris
    subephem = ephem.ephem()
    assert subephem.start == ephem.start
    assert subephem.stop == ephem.stop

    # resampling of the ephem
    subephem = ref_orb.ephem(start, stop, timedelta(minutes=1))
    assert subephem.start == ephem.start
    assert subephem.stop == ephem.stop
    assert len(subephem) == stop // timedelta(minutes=1) + 1

    # resample but with less points
    subephem = ephem.ephem(step=timedelta(minutes=10))
    assert subephem.start == ephem.start
    assert subephem.stop == ephem.stop
    assert len(subephem) == stop // timedelta(minutes=10) + 1

    # change of the start date of the ephem
    with raises(ValueError):
        subephem = ephem.ephem(start=ephem.start + timedelta(minutes=10))

    subephem = ephem.ephem(start=ephem.start + timedelta(minutes=9))
    assert subephem.start == ephem.start + timedelta(minutes=9)
    assert subephem.stop == ephem.stop
    assert len(subephem) == (subephem.stop - subephem.start) // step + 1

    with raises(ValueError):
        subephem = ephem.ephem(stop=ephem.stop - timedelta(minutes=10))

    subephem = ephem.ephem(stop=timedelta(minutes=12))
    assert subephem.start == ephem.start
    assert subephem.stop == ephem.start + timedelta(minutes=12)
    assert len(subephem) == (subephem.stop - subephem.start) // step + 1


def test_getitem(ephem):

    # Evolution of the Z component
    z = ephem[:, 2]

    assert len(z) == len(ephem)

    with raises(IndexError):
        # too many dimensions
        ephem[:, 1, :]
