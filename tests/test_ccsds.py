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
ref_man = get_ref("opm_impulsive_man.kvn")
ref_opm_no_units = get_ref("opm_no_unit.kvn")
ref_oem = get_ref("oem.kvn")
ref_double_oem = get_ref("oem_double.kvn")
ref_tle_bluebook = get_ref("bluebook.tle")
ref_omm_bluebook = get_ref("bluebook_omm.kvn")


@fixture(params=["kvn", "xml"])
def filetype(request):
    return request.param


@fixture
def str_opm(filetype):
    return get_ref("opm.{}".format(filetype))


@fixture
def str_opm_cov(filetype):
    return get_ref("opm_cov.{}".format(filetype))


@fixture
def str_opm_impulsive_man(filetype):
    return get_ref("opm_impulsive_man.{}".format(filetype))


@fixture
def str_opm_no_unit(filetype):
    return get_ref("opm_no_unit.{}".format(filetype))


@fixture
def str_opm_strange_units(filetype):
    return get_ref("opm_strange_units.{}".format(filetype))


@fixture
def str_omm(filetype):
    return get_ref("omm.{}".format(filetype))


@fixture
def str_omm_bluebook(filetype):
    return get_ref("bluebook_omm.{}".format(filetype))


@fixture
def str_oem(filetype):
    return get_ref("oem.{}".format(filetype))


@fixture
def str_oem_double(filetype):
    return get_ref("oem_double.{}".format(filetype))


@fixture
def omm():
    tle = Tle(
        """ISS (ZARYA)
1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"""
    )

    return tle.orbit()


@fixture
def opm(omm):
    return omm.copy(form="cartesian")


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
            6.224444338635500e-4,
        ],
    ]

    return opm


@fixture
def opm_man(opm):
    opm = opm.copy()
    opm.propagator = Kepler(get_body("Earth"), timedelta(seconds=60))
    opm.maneuvers = [
        ImpulsiveMan(
            Date(2008, 9, 20, 12, 41, 9, 984493),
            [280, 0, 0],
            frame="TNW",
            comment="Maneuver 1",
        ),
        ImpulsiveMan(Date(2008, 9, 20, 13, 33, 11, 374985), [270, 0, 0], frame="TNW"),
    ]
    return opm


@fixture
def opm_continuous_man(opm):
    opm = opm.copy()
    opm.propagator = Kepler(get_body("Earth"), timedelta(seconds=60))
    opm.maneuvers = [
        ContinuousMan(
            Date(2008, 9, 20, 12, 41, 9, 984493),
            timedelta(minutes=3),
            [280, 0, 0],
            frame="TNW",
            comment="Maneuver 1",
        ),
        ContinuousMan(
            Date(2008, 9, 20, 13, 33, 11, 374985),
            timedelta(minutes=3),
            [270, 0, 0],
            frame="TNW",
        ),
    ]
    return opm


@fixture
def ephem(opm):
    return opm.ephem(
        start=opm.date, stop=timedelta(minutes=120), step=timedelta(minutes=3)
    )


@fixture
def ephem2(opm):
    return opm.ephem(start=opm.date, stop=timedelta(hours=5), step=timedelta(minutes=5))


def assert_orbit(ref, orb, form="cartesian"):

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


def assert_string_lines(str1, str2, ignore=[]):

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


def test_dummy(filetype):

    with raises(TypeError):
        dumps(None, fmt=filetype)

    with raises(CcsdsParseError):
        loads("dummy text")


def test_dump_opm(opm, str_opm, filetype):

    ref = str_opm.splitlines()
    txt = dumps(opm, fmt=filetype).splitlines()

    assert_string_lines(ref, txt)


def test_dump_opm_cov(opm_cov, str_opm_cov, filetype):

    ref = str_opm_cov.splitlines()
    txt = dumps(opm_cov, fmt=filetype).splitlines()

    assert_string_lines(ref, txt)

    opm_cov2 = opm_cov.copy()
    opm_cov2.cov.frame = "TNW"
    txt = dumps(opm_cov2, fmt=filetype).splitlines()

    opm_cov3 = opm_cov.copy()
    opm_cov3.cov.frame = "QSW"
    txt = dumps(opm_cov3, fmt=filetype).splitlines()


def test_dump_omm(omm, str_omm, filetype):
    ref = str_omm.splitlines()
    txt = dumps(omm, fmt=filetype).splitlines()

    assert_string_lines(ref, txt)


def test_dump_omm_bluebook(filetype, str_omm_bluebook):
    """Example from the CCSDS Blue Book (4-1 and 4-2)
    """

    tle = Tle(ref_tle_bluebook)
    omm = tle.orbit()
    omm.name = tle.name
    omm.norad_id = tle.norad_id
    omm.cospar_id = tle.cospar_id

    # assert tle.epoch == Date(2007, 5, 4, 10, 34, 41, 426400)

    omm = dumps(omm, fmt=filetype).splitlines()
    ref_bluebook = str_omm_bluebook.splitlines()

    assert ref_bluebook[0] == omm[0]
    for i in range(4, len(ref_bluebook)):
        assert ref_bluebook[i] == omm[i]


def test_dump_opm_man_impulsive(opm_man, str_opm_impulsive_man, filetype):

    ref = str_opm_impulsive_man.splitlines()
    txt = dumps(opm_man, fmt=filetype).splitlines()

    assert_string_lines(ref, txt)


def test_dump_opm_man_continuous(opm_continuous_man, str_opm_impulsive_man, filetype):
    ref = str_opm_impulsive_man.splitlines()
    txt = dumps(opm_continuous_man, fmt=filetype).splitlines()

    assert_string_lines(ref, txt, ignore="MAN_DURATION")


def test_dump_oem(ephem, str_oem, filetype):

    ref = str_oem.splitlines()
    txt = dumps(ephem, fmt=filetype).splitlines()

    assert_string_lines(ref, txt)


def test_dump_double_oem(ephem, ephem2, str_oem_double, filetype):

    ref = str_oem_double.splitlines()
    txt = dumps([ephem, ephem2], fmt=filetype).splitlines()

    assert_string_lines(ref, txt)


def test_dump_oem_linear(ephem, filetype):

    ephem.method = ephem.LINEAR
    txt = dumps(ephem, fmt="xml").splitlines()

    for line in txt:
        if "INTERPOLATION" in line:
            assert "LINEAR" in line


def test_load_opm(opm, str_opm):

    ref = loads(str_opm)
    assert_orbit(opm, ref)


def test_load_opm_no_unit(opm, str_opm_no_unit):
    ref = loads(str_opm_no_unit)
    assert_orbit(opm, ref)


def test_load_opm_strange_unit(str_opm_strange_units):
    # Dummy units, that aren't specified as valid
    with raises(CcsdsParseError) as e:
        loads(str_opm_strange_units)

    assert str(e.value) == "Unknown unit 'm/s' for the field X_DOT"


def test_load_opm_truncated():
    # One mandatory line is missing
    truncated_opm = "\n".join(ref_opm.splitlines()[:15] + ref_opm.splitlines()[16:])
    with raises(CcsdsParseError) as e:
        loads(truncated_opm)

    assert str(e.value) == "Missing mandatory parameter 'Y'"


def test_load_opm_cov(opm_cov, str_opm_cov):
    ref_opm = loads(str_opm_cov)
    assert_orbit(opm_cov, ref_opm)

    assert hasattr(ref_opm, "cov")
    for i, j in product(range(6), repeat=2):
        assert abs(ref_opm.cov[i, j] - opm_cov.cov[i, j]) < np.finfo(float).eps


def test_load_opm_man_impulsive(opm_man, str_opm_impulsive_man):

    ref_opm_man = loads(str_opm_impulsive_man)
    assert len(ref_opm_man.maneuvers) == 2

    for i, man in enumerate(opm_man.maneuvers):
        assert ref_opm_man.maneuvers[i].date == man.date
        assert ref_opm_man.maneuvers[i]._dv.tolist() == man._dv.tolist()
        assert ref_opm_man.maneuvers[i].frame == man.frame
        assert ref_opm_man.maneuvers[i].comment == man.comment


def test_load_opm_man_continuous(opm_continuous_man, str_opm_impulsive_man, filetype):

    # Tweak the reference to convert impulsive maneuvers into continuous ones
    str_opm_continuous_man = str_opm_impulsive_man.splitlines()

    for i, line in enumerate(str_opm_continuous_man):
        if "MAN_DURATION" in line:
            if filetype == "kvn":
                str_opm_continuous_man[i] = "MAN_DURATION         = 180.000 [s]"
            else:
                str_opm_continuous_man[i] = '          <MAN_DURATION units="s">180.000</MAN_DURATION>'

    ref_continuous_man = "\n".join(str_opm_continuous_man)

    ref_opm_continuous_man = loads(ref_continuous_man)

    assert len(ref_opm_continuous_man.maneuvers) == 2

    for i, man in enumerate(opm_continuous_man.maneuvers):
        assert ref_opm_continuous_man.maneuvers[i].date == man.date
        assert ref_opm_continuous_man.maneuvers[i].duration == man.duration
        assert ref_opm_continuous_man.maneuvers[i]._dv.tolist() == man._dv.tolist()
        assert ref_opm_continuous_man.maneuvers[i].frame == man.frame
        assert ref_opm_continuous_man.maneuvers[i].comment == man.comment


def test_load_omm(omm, str_omm):
    omm2 = loads(str_omm)
    assert_orbit(omm, omm2, "TLE")

    # omm3 = loads(ref_omm_no_units)
    # assert_orbit(omm, omm3)

    # # Dummy units, that aren't specified as valid
    # with raises(CcsdsParseError):
    #     loads(ref_omm_strange_units)

    # # One mandatory line is missing
    # truncated_omm = "\n".join(ref_omm.splitlines()[:15] + ref_omm.splitlines()[16:])
    # with raises(CcsdsParseError):
    #     loads(truncated_omm)


def test_load_oem(ephem, str_oem):

    ref_ephem = loads(str_oem)

    assert ref_ephem.frame == ephem.frame
    assert ref_ephem.start == ephem.start
    assert ref_ephem.stop == ephem.stop
    assert ref_ephem.method == ref_ephem.LAGRANGE
    assert ref_ephem.order == 8

    for opm, opm2 in zip(ephem, ref_ephem):
        assert_orbit(opm, opm2)

    # with raises(CcsdsParseError):
    #     loads("\n".join(ref_oem.splitlines()[:15]))

    # with raises(CcsdsParseError):
    #     loads("\n".join(ref_oem.splitlines()[:8] + ref_oem.splitlines()[9:]))


def test_load_double_oem(ephem, ephem2, str_oem_double):

    ephem_bis, ephem2_bis = loads(str_oem_double)

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
