from pathlib import Path
import numpy as np
from pytest import fixture
from functools import partial

from beyond.orbits.cov import Cov
from beyond.orbits.man import ImpulsiveMan, ContinuousMan
from beyond.io.tle import Tle
from beyond.dates import Date, timedelta
from beyond.propagators.numerical import KeplerNum
from beyond.env.solarsystem import get_body
from beyond.orbits import StateVector


@fixture(params=["kvn", "xml"])
def ccsds_format(request):
    return request.param


@fixture
def raw_datafile():
    def func(name, kep=True, suffix=None):
        FOLDER = Path(__file__).parent / "data"

        name = name if kep else f"{name}-nokep"
        filepath = FOLDER.joinpath(name)

        if suffix is not None:
            filepath = filepath.with_suffix(suffix)

        return filepath.read_text()

    return func


@fixture
def datafile(ccsds_format, raw_datafile):
    return partial(raw_datafile, suffix=f".{ccsds_format}")


@fixture
def str_tle_bluebook(raw_datafile):
    return raw_datafile("bluebook.tle")


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
    # Quick and dirty transformation of the MeanOrbit into a StateVector, without
    # any propagation. This is done for simplicity, as the resulting StateVector
    # will be used for nothing but CCSDS OPM formatting.
    new_dict = tle._data.copy()
    new_dict.pop("propagator")
    sv = StateVector(tle.base, **new_dict).copy(form="cartesian")
    return sv


@fixture
def cov(orbit):
    cov = [
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

    return cov


@fixture
def orbit_cov(orbit, cov):
    orbit = orbit.copy()
    orbit.cov = Cov(orbit, cov, orbit.frame)
    return orbit


@fixture
def orbit_man(orbit):
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
def ephem(tle):
    ephem = tle.ephem(
        start=tle.date, stop=timedelta(minutes=120), step=timedelta(minutes=3)
    )
    ephem.name = tle.name
    ephem.cospar_id = tle.cospar_id
    return ephem


@fixture
def ephem2(tle):
    ephem = tle.ephem(
        start=tle.date, stop=timedelta(hours=5), step=timedelta(minutes=5)
    )
    ephem.name = tle.name
    ephem.cospar_id = tle.cospar_id
    return ephem
