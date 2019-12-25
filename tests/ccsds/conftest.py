
from pathlib import Path
import numpy as np
from pytest import fixture
from itertools import product

from beyond.orbits.man import ImpulsiveMan, ContinuousMan
from beyond.io.tle import Tle
from beyond.dates import Date, timedelta
from beyond.propagators.kepler import Kepler
from beyond.env.solarsystem import get_body


@fixture(params=["kvn", "xml"])
def ccsds_format(request):
    return request.param


@fixture
def datafile(ccsds_format):
    return lambda name: Helper.datafile(name, suffix=".{}".format(ccsds_format))


@fixture
def str_tle_bluebook():
    return Helper.datafile("bluebook.tle")


@fixture
def tle():
    tle = Tle(
        """ISS (ZARYA)
1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"""
    )

    return tle.orbit()


@fixture
def orbit(tle):
    return tle.copy(form="cartesian")


@fixture
def orbit_cov(orbit):
    orbit = orbit.copy()
    orbit.cov = [
        [
            3.331349476038534e2,
            4.618927349220216e2,
            -3.070007847730449e2,
            -3.349365033922630e-1,
            -2.211832501084875e-1,
            -3.041346050686871e-1,
        ],
        [
            4.618927349220216e2,
            6.782421679971363e2,
            -4.221234189514228e2,
            -4.686084221046758e-1,
            -2.864186892102733e-1,
            -4.989496988610662e-1,
        ],
        [
            -3.070007847730449e2,
            -4.221234189514228e2,
            3.231931992380369e2,
            2.484949578400095e-1,
            1.798098699846038e-1,
            3.540310904497689e-1,
        ],
        [
            -3.349365033922630e-1,
            -4.686084221046758e-1,
            2.484949578400095e-1,
            4.296022805587290e-4,
            2.608899201686016e-4,
            1.869263192954590e-4,
        ],
        [
            -2.211832501084875e-1,
            -2.864186892102733e-1,
            1.798098699846038e-1,
            2.608899201686016e-4,
            1.767514756338532e-4,
            1.008862586240695e-4,
        ],
        [
            -3.041346050686871e-1,
            -4.989496988610662e-1,
            3.540310904497689e-1,
            1.869263192954590e-4,
            1.008862586240695e-4,
            6.224444338635500e-4,
        ],
    ]

    return orbit


@fixture
def orbit_man(orbit):
    orbit = orbit.copy()
    orbit.propagator = Kepler(get_body("Earth"), timedelta(seconds=60))
    orbit.maneuvers = [
        ImpulsiveMan(
            Date(2008, 9, 20, 12, 41, 9, 984493),
            [280, 0, 0],
            frame="TNW",
            comment="Maneuver 1",
        ),
        ImpulsiveMan(Date(2008, 9, 20, 13, 33, 11, 374985), [270, 0, 0], frame="TNW"),
    ]
    return orbit


@fixture
def orbit_continuous_man(orbit):
    orbit = orbit.copy()
    orbit.propagator = Kepler(get_body("Earth"), timedelta(seconds=60))
    orbit.maneuvers = [
        ContinuousMan(
            Date(2008, 9, 20, 12, 41, 9, 984493),
            timedelta(minutes=3),
            dv=[280, 0, 0],
            frame="TNW",
            comment="Maneuver 1",
        ),
        ContinuousMan(
            Date(2008, 9, 20, 13, 33, 11, 374985),
            timedelta(minutes=3),
            dv=[270, 0, 0],
            frame="TNW",
        ),
    ]
    return orbit


@fixture
def ephem(orbit):
    ephem = orbit.ephem(
        start=orbit.date, stop=timedelta(minutes=120), step=timedelta(minutes=3)
    )
    ephem.name = orbit.name
    ephem.cospar_id = orbit.cospar_id
    return ephem


@fixture
def ephem2(orbit):
    ephem = orbit.ephem(
        start=orbit.date, stop=timedelta(hours=5), step=timedelta(minutes=5)
    )
    ephem.name = orbit.name
    ephem.cospar_id = orbit.cospar_id
    return ephem


class Helper:

    FOLDER = Path(__file__).parent / "data"

    @classmethod
    def datafile(cls, name, suffix=None):

        filepath = cls.FOLDER.joinpath(name)
        if suffix is not None:
            filepath = filepath.with_suffix(suffix)

        return filepath.read_text()

    @staticmethod
    def assert_orbit(orb1, orb2, form="cartesian", cov_eps=None):

        cov_eps = np.finfo(float).eps if cov_eps is None else cov_eps

        orb1.form = form
        orb2.form = form

        assert orb1.frame == orb2.frame
        assert orb1.date == orb2.date

        # Precision down to millimeter due to the truncature when writing the CCSDS OPM
        assert abs(orb1[0] - orb2[0]) < 1e-3
        assert abs(orb1[1] - orb2[1]) < 1e-3
        assert abs(orb1[2] - orb2[2]) < 1e-3
        assert abs(orb1[3] - orb2[3]) < 1e-3
        assert abs(orb1[4] - orb2[4]) < 1e-3
        assert abs(orb1[5] - orb2[5]) < 1e-3

        if orb1.cov.any() and orb2.cov.any():
            elems = "X Y Z X_DOT Y_DOT Z_DOT".split()
            for i, j in product(range(6), repeat=2):
                assert abs(orb1.cov[i,j] - orb2.cov[i,j]) < cov_eps, "C{}_{}".format(elems[i], elems[j])

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

    @classmethod
    def assert_ephem(cls, ephem1, ephem2, cov_eps=None):

        assert len(ephem1) == len(ephem2)

        assert ephem1.frame == ephem2.frame
        assert ephem1.start == ephem2.start
        assert ephem1.stop == ephem2.stop
        assert ephem1.method == ephem2.method
        assert ephem1.order == ephem2.order

        for e1, e2 in zip(ephem1, ephem2):
            cls.assert_orbit(e1, e2, cov_eps=cov_eps)

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
