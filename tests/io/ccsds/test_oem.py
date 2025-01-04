from pytest import raises, fixture, mark

from beyond.io.ccsds import dumps, loads, CcsdsError
from beyond.dates import timedelta
from beyond.orbits.cov import Cov


@fixture
def orbit_cov(tle, cov):
    orbit = tle.copy()
    orbit.cov = Cov(orbit, cov, orbit.frame)
    return orbit


@fixture
def ephem_cov(orbit_cov):
    ephem = orbit_cov.ephem(start=orbit_cov.date, stop=timedelta(hours=1), step=timedelta(minutes=2))
    ephem.name = orbit_cov.name
    ephem.cospar_id = orbit_cov.cospar_id
    return ephem


def test_dump_oem(ephem, datafile, ccsds_format, helper):

    ref = datafile("oem")
    txt = dumps(ephem, fmt=ccsds_format)

    helper.assert_string(ref, txt)


def test_dump_double_oem(ephem, ephem2, datafile, ccsds_format, helper):

    ref = datafile("oem_double")
    txt = dumps([ephem, ephem2], fmt=ccsds_format)

    helper.assert_string(ref, txt)


def test_dump_oem_linear(ephem, ccsds_format):

    ephem.method = ephem.LINEAR
    txt = dumps(ephem, fmt=ccsds_format).splitlines()

    for line in txt:
        if "INTERPOLATION" in line:
            assert "LINEAR" in line


@mark.jpl
def test_dump_oem_interplanetary(jplfiles, ephem, ccsds_format, datafile, helper):

    ephem.frame = "MarsBarycenter"

    ref = datafile("oem_interplanetary")
    txt = dumps(ephem, fmt=ccsds_format)

    helper.assert_string(ref, txt)


def test_dump_oem_cov(ephem_cov, ccsds_format, datafile, helper):
    txt = dumps(ephem_cov, fmt=ccsds_format)
    helper.assert_string(datafile("oem_cov"), txt)


def test_dump_oem_cov_qsw(ephem_cov, ccsds_format, datafile, helper):
    ephem_cov[0].cov.frame = "QSW"
    txt = dumps(ephem_cov, fmt=ccsds_format)
    helper.assert_string(datafile("oem_cov_qsw"), txt)


def test_dump_oem_cov_tnw(ephem_cov, ccsds_format, datafile, helper):
    ephem_cov[0].cov.frame = "TNW"
    txt = dumps(ephem_cov, fmt=ccsds_format)
    helper.assert_string(datafile("oem_cov_tnw"), txt)


def test_load_oem(ephem, datafile, helper):

    data = loads(datafile("oem"))

    helper.assert_ephem(ephem, data)

    # with raises(CcsdsError):
    #     loads("\n".join(ref_oem.splitlines()[:15]))

    truncated = datafile("oem").split()
    for i, line in enumerate(truncated):
        if "REF_FRAME" in line:
            truncated.pop(i)
            break

    with raises(CcsdsError) as e:
        loads("\n".join(truncated))

    assert str(e.value) == "Missing mandatory parameter 'REF_FRAME'"


def test_load_oem_minimal(ephem, datafile, helper):
    data = loads(datafile("oem_minimal"))
    helper.assert_ephem(ephem, data)


def test_load_double_oem(ephem, ephem2, datafile, helper):

    data, data2 = loads(datafile("oem_double"))

    helper.assert_ephem(ephem, data)
    helper.assert_ephem(ephem2, data2)


def test_load_oem_cov(ephem_cov, datafile, helper):
    data = loads(datafile("oem_cov"))
    helper.assert_ephem(ephem_cov, data)


def test_load_oem_cov_qsw(ephem_cov, datafile, helper):
    ephem_cov[0].cov.frame = "QSW"
    data = loads(datafile("oem_cov_qsw"))
    helper.assert_ephem(ephem_cov, data)


def test_load_oem_cov_tnw(ephem_cov, datafile, helper):
    ephem_cov[0].cov.frame = "TNW"
    data = loads(datafile("oem_cov_tnw"))
    helper.assert_ephem(ephem_cov, data)


@mark.jpl
def test_load_oem_interplanetary(jplfiles, ephem, datafile, helper):

    ephem.frame = "MarsBarycenter"

    data = loads(datafile("oem_interplanetary"))

    helper.assert_ephem(ephem, data)
