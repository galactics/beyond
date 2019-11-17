
from pytest import fixture, raises

import numpy as np
from pathlib import Path
from itertools import product
from datetime import timedelta

from beyond.orbits.man import ImpulsiveMan, ContinuousMan
from beyond.io.tle import Tle
from beyond.io.ccsds import dumps, loads, CcsdsParseError
from beyond.dates import Date, timedelta
from beyond.propagators.kepler import Kepler
from beyond.env.solarsystem import get_body


folder = Path(__file__).parent / "data" / "io" / "ccsds"

def get_ref(name):
    return folder.joinpath(name).read_text()


ref_opm = get_ref("opm.kvn")
ref_opm_cov = get_ref("opm_cov.kvn")
ref_omm = get_ref("omm.kvn")
ref_opm_strange_units = get_ref("opm_strange_units.kvn")
ref_man = get_ref("impulsive_man.kvn")
ref_opm_no_units = get_ref("opm_no_unit.kvn")
ref_oem = get_ref("oem.kvn")
ref_double_oem = get_ref("oem_double.kvn")
ref_tle_bluebook = get_ref("bluebook.tle")
ref_omm_bluebook = get_ref("bluebook_omm.kvn")


@fixture
def omm():
    tle = Tle("""1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537""")

    return tle.orbit()


@fixture
def opm(omm):
    return omm.copy(form='cartesian')


@fixture
def opm_cov(opm):
    opm = opm.copy()
    opm.cov = [
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
            6.224444338635500e-4
        ]
    ]

    return opm


@fixture
def opm_man(opm):
    opm = opm.copy()
    opm.propagator = Kepler(get_body('Earth'), timedelta(seconds=60))
    opm.maneuvers = [
        ImpulsiveMan(Date(2008, 9, 20, 12, 41, 9, 984493), [280, 0, 0], frame="TNW", comment="Maneuver 1"),
        ImpulsiveMan(Date(2008, 9, 20, 13, 33, 11, 374985), [270, 0, 0], frame="TNW"),
    ]
    return opm


@fixture
def opm_continuous_man(opm):
    opm = opm.copy()
    opm.propagator = Kepler(get_body('Earth'), timedelta(seconds=60))
    opm.maneuvers = [
        ContinuousMan(Date(2008, 9, 20, 12, 41, 9, 984493), timedelta(minutes=3), [280, 0, 0], frame="TNW", comment="Maneuver 1"),
        ContinuousMan(Date(2008, 9, 20, 13, 33, 11, 374985), timedelta(minutes=3), [270, 0, 0], frame="TNW"),
    ]
    return opm


@fixture
def ephem(opm):
    return opm.ephem(start=opm.date, stop=timedelta(minutes=120), step=timedelta(minutes=3))


@fixture
def ephem2(opm):
    return opm.ephem(start=opm.date, stop=timedelta(hours=5), step=timedelta(minutes=5))


def assert_orbit(ref, orb, form='cartesian'):

    ref.form = form
    orb.form = form

    assert ref.frame == orb.frame
    assert ref.date == orb.date

    # Precision down to millimeter due to the truncature when writing the CCSDS OPM
    assert abs(ref[0] - orb[0]) < 1e-3
    assert abs(ref[1] - orb[1]) < 1e-3
    assert abs(ref[2] - orb[2]) < 1e-3
    assert abs(ref[3] - orb[3]) < 1e-3
    assert abs(ref[4] - orb[4]) < 1e-3
    assert abs(ref[5] - orb[5]) < 1e-3


def test_dummy():
    with raises(TypeError):
        dumps(None)
    with raises(CcsdsParseError):
        loads("dummy text")


def test_dump_opm(opm):

    ref = ref_opm.splitlines()
    txt = dumps(opm).splitlines()

    # the split is here to avoid the creation date line
    assert txt[0] == ref[0]
    assert "\n".join(txt[2:]) == "\n".join(ref[2:])


def test_dump_opm_cov(opm_cov):

    ref = ref_opm_cov.splitlines()
    txt = dumps(opm_cov).splitlines()

    # the split is here to avoid the creation date line
    assert txt[0] == ref[0]
    assert "\n".join(ref[2:]) == "\n".join(txt[2:])    

    opm_cov2 = opm_cov.copy()
    opm_cov2.cov.frame = "TNW"
    txt = dumps(opm_cov2).splitlines()

    opm_cov3 = opm_cov.copy()
    opm_cov3.cov.frame = "QSW"
    txt = dumps(opm_cov3).splitlines()


def test_dump_omm(omm):
    ref = ref_omm.splitlines()
    txt = dumps(omm).splitlines()

    # the split is here to avoid the creation date line
    assert txt[0] == ref[0]
    assert "\n".join(txt[2:]) == "\n".join(ref[2:])


def test_omm_dump_bluebook():
    """Example from the CCSDS Blue Book (4-1 and 4-2)
    """

    tle = Tle(ref_tle_bluebook)
    omm = tle.orbit()
    omm.name = tle.name
    omm.norad_id = tle.norad_id
    omm.cospar_id = tle.cospar_id

    # assert tle.epoch == Date(2007, 5, 4, 10, 34, 41, 426400)

    omm = dumps(omm).splitlines()
    ref_bluebook = ref_omm_bluebook.splitlines()

    assert omm[0] == ref_bluebook[0]
    for i in range(4, len(ref_bluebook)):
        assert omm[i] == ref_bluebook[i]


def test_dump_opm_man_impulsive(opm_man):

    ref = ref_man.splitlines()
    txt = dumps(opm_man).splitlines()

    # the split is here to avoid the creation date line
    assert txt[0] == ref[0]
    assert "\n".join(txt[2:]) == "\n".join(ref[2:])


def test_dump_opm_man_continuous(opm_continuous_man):
    ref = ref_man.splitlines()
    txt = dumps(opm_continuous_man).splitlines()
    # the split is here to avoid the creation date line
    assert txt[0] == ref[0]
    assert "\n".join(txt[2:31]) == "\n".join(ref[2:31])
    assert txt[31] == "MAN_DURATION         = 180.000 [s]"
    assert "\n".join(txt[32:39]) == "\n".join(ref[32:39])
    assert txt[39] == "MAN_DURATION         = 180.000 [s]"
    assert "\n".join(txt[40]) == "\n".join(ref[40])


def test_dump_oem(ephem):

    ref = ref_oem.splitlines()
    txt = dumps(ephem).splitlines()
    # the split is here to avoid the creation date line
    assert txt[0] == ref[0]
    assert "\n".join(txt[2:]) == "\n".join(ref[2:])


def test_dump_double_oem(ephem, ephem2):

    ref = ref_double_oem.splitlines()
    txt = dumps([ephem, ephem2]).splitlines()

    assert txt[0] == ref[0]
    assert "\n".join(txt[2:]) == "\n".join(ref[2:])


def test_dump_oem_linear(ephem):

    ephem.method = ephem.LINEAR
    txt = dumps(ephem).splitlines()

    assert "\n".join(txt[2:14]) == """ORIGINATOR = N/A

META_START
OBJECT_NAME          = N/A
OBJECT_ID            = N/A
CENTER_NAME          = EARTH
REF_FRAME            = TEME
TIME_SYSTEM          = UTC
START_TIME           = 2008-09-20T12:25:40.104192
STOP_TIME            = 2008-09-20T14:25:40.104192
INTERPOLATION        = LINEAR
META_STOP"""


def test_load_opm(opm):

    opm2 = loads(ref_opm)
    assert_orbit(opm, opm2)

    opm3 = loads(ref_opm_no_units)
    assert_orbit(opm, opm3)

    # Dummy units, that aren't specified as valid
    with raises(CcsdsParseError):
        loads(ref_opm_strange_units)

    # One mandatory line is missing
    truncated_opm = "\n".join(ref_opm.splitlines()[:15] + ref_opm.splitlines()[16:])
    with raises(CcsdsParseError):
        loads(truncated_opm)


def test_load_opm_cov(opm_cov):
    ref_opm = loads(ref_opm_cov)
    assert_orbit(opm_cov, ref_opm)

    assert hasattr(ref_opm, 'cov')
    for i, j in product(range(6), repeat=2):
        assert abs(ref_opm.cov[i, j] - opm_cov.cov[i, j]) < np.finfo(float).eps


def test_load_opm_man_impulsive(opm_man):

    ref_opm_man = loads(ref_man)
    assert len(ref_opm_man.maneuvers) == 2

    for i, man in enumerate(opm_man.maneuvers):
        assert ref_opm_man.maneuvers[i].date == man.date
        assert ref_opm_man.maneuvers[i]._dv.tolist() == man._dv.tolist()
        assert ref_opm_man.maneuvers[i].frame == man.frame
        assert ref_opm_man.maneuvers[i].comment == man.comment


def test_load_opm_man_continuous(opm_continuous_man):

    ref_opm_man = loads(ref_man)
    # Tweak the reference to convert impulsive maneuvers into continuous ones
    ref_continuous_man = ref_man.splitlines()
    ref_continuous_man[31] = "MAN_DURATION         = 180.000 [s]"
    ref_continuous_man[39] = "MAN_DURATION         = 180.000 [s]"
    ref_continuous_man = "\n".join(ref_continuous_man)

    ref_opm_continuous_man = loads(ref_continuous_man)

    assert len(ref_opm_continuous_man.maneuvers) == 2

    for i, man in enumerate(opm_continuous_man.maneuvers):
        assert ref_opm_continuous_man.maneuvers[i].date == man.date
        assert ref_opm_continuous_man.maneuvers[i].duration == man.duration
        assert ref_opm_continuous_man.maneuvers[i]._dv.tolist() == man._dv.tolist()
        assert ref_opm_continuous_man.maneuvers[i].frame == man.frame
        assert ref_opm_continuous_man.maneuvers[i].comment == man.comment


def test_load_omm(omm):
    omm2 = loads(ref_omm)
    assert_orbit(omm, omm2, 'TLE')

    # omm3 = loads(ref_omm_no_units)
    # assert_orbit(omm, omm3)

    # # Dummy units, that aren't specified as valid
    # with raises(CcsdsParseError):
    #     loads(ref_omm_strange_units)

    # # One mandatory line is missing
    # truncated_omm = "\n".join(ref_omm.splitlines()[:15] + ref_omm.splitlines()[16:])
    # with raises(CcsdsParseError):
    #     loads(truncated_omm)    


def test_load_oem(ephem):

    ephem2 = loads(ref_oem)

    assert ephem2.frame == ephem.frame
    assert ephem2.start == ephem.start
    assert ephem2.stop == ephem.stop
    assert ephem2.method == ephem2.LAGRANGE
    assert ephem2.order == 8

    for opm, opm2 in zip(ephem, ephem2):
        assert_orbit(opm, opm2)

    with raises(CcsdsParseError):
        loads("\n".join(ref_oem.splitlines()[:15]))

    with raises(CcsdsParseError):
        loads("\n".join(ref_oem.splitlines()[:8] + ref_oem.splitlines()[9:]))


def test_load_double_oem(ephem, ephem2):

    ephem_bis, ephem2_bis = loads(ref_double_oem)

    assert ephem_bis.frame == ephem.frame
    assert ephem_bis.frame == ephem.frame
    assert ephem_bis.start == ephem.start
    assert ephem_bis.stop == ephem.stop
    assert ephem_bis.method == ephem_bis.LAGRANGE
    assert ephem_bis.order == 8

    assert ephem2_bis.frame == ephem2.frame
    assert ephem2_bis.frame == ephem2.frame
    assert ephem2_bis.start == ephem2.start
    assert ephem2_bis.stop == ephem2.stop
    assert ephem2_bis.method == ephem2_bis.LAGRANGE
    assert ephem2_bis.order == 8
