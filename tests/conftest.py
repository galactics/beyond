import numpy as np
from pytest import fixture, mark, skip
from unittest.mock import patch
from pathlib import Path
from itertools import product

from beyond.config import config
from beyond.dates.eop import Eop
from beyond.frames.stations import create_station
from beyond.io.tle import Tle
from beyond.propagators.numerical import KeplerNum
from beyond.dates import Date, timedelta
from beyond.env.solarsystem import get_body
from beyond.env import jpl
from beyond.orbits.man import ContinuousMan
from beyond.orbits.statevector import AbstractStateVector

np.set_printoptions(linewidth=200)


@fixture(autouse=True, scope="session")
def config_override():
    """Create a dummy config dict containing basic data
    """
    config.set("eop", "missing_policy", "pass")


@fixture
def common_env():
    with patch('beyond.dates.date.EopDb.get') as m:
        m.return_value = Eop(
            x=-0.00951054166666622, y=0.31093590624999734, dpsi=-94.19544791666682,
            deps=-10.295645833333051, dy=-0.10067361111115315, dx=-0.06829513888889051,
            lod=1.6242802083331438, ut1_utc=0.01756018472222477, tai_utc=36.0
        )
        yield


@fixture
def station(common_env):
    return create_station('Toulouse', (43.604482, 1.443962, 172.))


@fixture
def iss_tle(common_env):
    return Tle("""ISS (ZARYA)
1 25544U 98067A   18124.55610684  .00001524  00000-0  30197-4 0  9997
2 25544  51.6421 236.2139 0003381  47.8509  47.6767 15.54198229111731""")


@fixture
def molniya_tle(common_env):
    return Tle("""MOLNIYA 1-90
1 24960U 97054A   18123.22759647  .00000163  00000-0  24467-3 0  9999
2 24960  62.6812 182.7824 6470982 294.8616  12.8538  3.18684355160009""")


@fixture(params=["tle", "ephem"])
def orbit(request, iss_tle):

    orb = iss_tle.orbit()

    if request.param == "tle":
        return orb
    elif request.param == "ephem":
        start = Date(2018, 4, 5, 16, 50)
        stop = timedelta(hours=6)
        step = timedelta(seconds=15)

        return orb.ephem(start=start, stop=stop, step=step)
    elif request.param == "kepler":
        orb.propagator = KeplerNum(
            timedelta(seconds=60),
            get_body('Earth')
        )
        return orb


@fixture(params=["tle", "ephem"])
def molniya(request, molniya_tle):

    orb = molniya_tle.orbit()

    if request.param == "tle":
        return orb
    elif request.param == "ephem":
        start = Date(2018, 4, 5, 16, 50)
        stop = timedelta(hours=15)
        step = timedelta(minutes=1)

        return orb.ephem(start=start, stop=stop, step=step)


@fixture
def jplfiles():
    config.set('env', 'jpl', 'files', [
        str(Path(__file__).parent / "data" / "jpl" / "de403_2000-2020.bsp"),
        str(Path(__file__).parent / "data" / "jpl" / "pck00010.tpc"),
        str(Path(__file__).parent / "data" / "jpl" / "gm_de431.tpc"),
    ])

    jpl.create_frames()


class Helper:

    @staticmethod
    def assert_vector(ref, pv, precision=(4, 6)):

        if isinstance(ref, AbstractStateVector):
            ref = ref.base
        if isinstance(pv, AbstractStateVector):
            pv = pv.base

        np.testing.assert_almost_equal(ref[:3], pv[:3], precision[0], "Position")
        np.testing.assert_almost_equal(ref[3:], pv[3:], precision[1], "Velocity")

    @staticmethod
    def assert_orbit(orb1, orb2, form="cartesian"):

        cov_eps = 1e-10

        orb1 = orb1.copy(form=form)
        orb2 = orb2.copy(form=form)

        assert hasattr(orb1, "name") == hasattr(orb2, "name")
        if hasattr(orb1, "name") and hasattr(orb2, "name"):
            assert orb1.name == orb2.name

        assert hasattr(orb1, "cospar_id") == hasattr(orb2, "cospar_id")
        if hasattr(orb1, "cospar_id") and hasattr(orb2, "cospar_id"):
            assert orb1.cospar_id == orb2.cospar_id

        assert orb1.frame == orb2.frame
        assert orb1.date == orb2.date

        # Check if the two orb objects are of the same type (StateVector, MeanOrbit, or Orbit)
        assert orb1.__class__ is orb2.__class__

        assert hasattr(orb1, "propagator") == hasattr(orb2, "propagator")
        if hasattr(orb1, "propagator"):
            assert orb1.propagator.__class__ is orb2.propagator.__class__
            # TODO : It would be nice if we could check the parameters of the propagator

        # Precision down to millimeter due to the truncature when writing the CCSDS OPM
        assert abs(orb1[0] - orb2[0]) < 1e-3
        assert abs(orb1[1] - orb2[1]) < 1e-3
        assert abs(orb1[2] - orb2[2]) < 1e-3
        assert abs(orb1[3] - orb2[3]) < 1e-3
        assert abs(orb1[4] - orb2[4]) < 1e-3
        assert abs(orb1[5] - orb2[5]) < 1e-3

        if orb1.cov is not None and orb2.cov is not None:
            elems = "X Y Z X_DOT Y_DOT Z_DOT".split()
            for i, j in product(range(6), repeat=2):
                assert abs(orb1.cov[i,j] - orb2.cov[i,j]) < cov_eps, "C{}_{}".format(elems[i], elems[j])

        if hasattr(orb1, "maneuvers") and hasattr(orb2, "maneuvers"):
            assert len(orb1.maneuvers) == len(orb2.maneuvers)

            # Check for maneuvers if there is some
            for i, (o1_man, o2_man) in enumerate(zip(orb1.maneuvers, orb2.maneuvers)):
                assert o1_man.date == o2_man.date

                if isinstance(o1_man, ContinuousMan):
                    assert isinstance(o2_man, ContinuousMan)
                    assert o1_man.duration == o2_man.duration

                assert o1_man._dv.tolist() == o2_man._dv.tolist()
                assert o1_man.frame == o2_man.frame
                assert o1_man.comment == o2_man.comment
        elif hasattr(orb1, "maneuvers") != hasattr(orb2, "maneuvers"):
            assert False, "Incoherent structures"

    @classmethod
    def assert_ephem(cls, ephem1, ephem2):

        assert len(ephem1) == len(ephem2)

        assert ephem1.frame == ephem2.frame
        assert ephem1.start == ephem2.start
        assert ephem1.stop == ephem2.stop
        assert ephem1.method == ephem2.method
        assert ephem1.order == ephem2.order

        for e1, e2 in zip(ephem1, ephem2):
            cls.assert_orbit(e1, e2)

    @staticmethod
    def assert_string(str1, str2, ignore=[]):

        str1 = str1.splitlines()
        str2 = str2.splitlines()

        assert len(str1) == len(str2)

        if isinstance(ignore, str):
            ignore = [ignore]

        ignore.append("CREATION_DATE")

        for r, t in zip(str1, str2):
            _ignore = False

            for ig in ignore:
                if ig in r:
                    _ignore = True
                    break
            if _ignore:
                continue

            assert r == t


@fixture
def helper():
    return Helper



def _skip_if_no_mpl():
    """Specific for dynamically skipping the test if matplotlib is not present
    as it is not a dependency of the library, but merely a convenience
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return True
    else:
        return False


def pytest_configure(config):
    """Declare the skip_if_no_mpl marker in pytest's '--markers' helper option
    This has no actual effect on the tests
    """
    config.addinivalue_line(
        "markers", "mpl: Test using matplotlib. Skipped if matplotlib not available"
    )
    config.addinivalue_line(
        "markers", "jpl: Test using beyond.env.jpl functions and classes"
    )


def pytest_runtest_setup(item):
    """This function is called for each test case.
    It looks if the test case has the skip_if_no_mpl decorator. If so, skip the test case
    """
    if _skip_if_no_mpl() and list(item.iter_markers(name="mpl")):
        skip("matplotlib not installed")
