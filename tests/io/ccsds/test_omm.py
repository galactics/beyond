from itertools import product

from pytest import raises, fixture

import numpy as np

from beyond.dates import Date, timedelta
from beyond.orbits import MeanOrbit
from beyond.orbits.cov import Cov
from beyond.io.tle import Tle
from beyond.io.ccsds import dump, dumps, loads, CcsdsError
from beyond.propagators.analytical import EcksteinHechler


@fixture
def orbit_cov(tle, cov):
    orbit = tle.copy()
    orbit.cov = Cov(orbit, cov, orbit.frame)
    return orbit


@fixture
def ref_eh(tle):
    orb = tle.copy(form="mean_circular", frame="CIRF")
    orb.propagator = EcksteinHechler()
    return orb


def test_dump_omm(tle, datafile, ccsds_format, helper):
    ref = datafile("omm")
    txt = dumps(tle, fmt=ccsds_format)

    helper.assert_string(ref, txt)


def test_dump_omm_cov(orbit_cov, datafile, ccsds_format, helper):
    tle_cov = orbit_cov.copy(form="TLE")
    ref = datafile("omm_cov")
    txt = dumps(tle_cov, fmt=ccsds_format)

    helper.assert_string(ref, txt)

    tle_cov2 = tle_cov.copy()
    tle_cov2.cov.frame = "TNW"
    txt = dumps(tle_cov2, fmt=ccsds_format)
    helper.assert_string(datafile("omm_cov_tnw"), txt)

    tle_cov3 = tle_cov.copy()
    tle_cov3.cov.frame = "QSW"
    txt = dumps(tle_cov3, fmt=ccsds_format)

    helper.assert_string(datafile("omm_cov_qsw"), txt)


def test_dump_omm_bluebook(ccsds_format, datafile, str_tle_bluebook):
    """Example from the CCSDS Blue Book (4-1 and 4-2)"""

    tle = Tle(str_tle_bluebook)
    omm = tle.orbit()
    # omm.name = tle.name
    # omm.norad_id = tle.norad_id
    # omm.cospar_id = tle.cospar_id

    # assert tle.epoch == Date(2007, 5, 4, 10, 34, 41, 426400)

    omm = dumps(omm, fmt=ccsds_format).splitlines()
    ref_bluebook = datafile("omm_bluebook").splitlines()

    assert ref_bluebook[0] == omm[0]
    for i in range(4, len(ref_bluebook)):
        assert ref_bluebook[i] == omm[i]


def test_dump_omm_user_defined(tle, ccsds_format, datafile, helper):

    subdict = tle._data["ccsds_user_defined"] = {}

    subdict["FOO"] = "foo enters"
    subdict["BAR"] = "a bar"
    txt = dumps(tle, fmt=ccsds_format)

    helper.assert_string(datafile("omm_user_defined"), txt)


def test_dump_omm_eh(ref_eh, ccsds_format, datafile, helper):
    txt = dumps(ref_eh, fmt=ccsds_format)
    helper.assert_string(datafile("omm_eh"), txt)


def test_load_omm(tle, datafile, helper):
    data = loads(datafile("omm"))

    assert isinstance(data, MeanOrbit)
    helper.assert_orbit(tle, data, "TLE")

    # omm3 = loads(ref_omm_no_units)
    # helper.assert_orbit(omm, omm3)

    # # Dummy units, that aren't specified as valid
    # with raises(CcsdsError):
    #     loads(ref_omm_strange_units)


def test_load_omm_truncated(datafile):

    list_omm = datafile("omm").splitlines()
    for i, line in enumerate(list_omm):
        if "EPOCH" in line:
            list_omm.pop(i)
            break
    truncated_omm = "\n".join(list_omm)

    with raises(CcsdsError) as e:
        loads(truncated_omm)

    assert str(e.value) == "Missing mandatory parameter 'EPOCH'"


def test_load_omm_missing_sgp4(datafile):

    list_omm = datafile("omm").splitlines()
    for i, line in enumerate(list_omm):
        if "MEAN_MOTION" in line:
            list_omm.pop(i)
            break
    truncated_omm = "\n".join(list_omm)

    with raises(CcsdsError) as e:
        loads(truncated_omm)

    assert str(e.value) == "Missing mandatory parameter 'MEAN_MOTION'"


def test_load_omm_missing_optional_sgp4(tle, datafile, helper):
    """Test of optionality"""
    list_omm = datafile("omm").splitlines()
    for i, line in enumerate(list_omm):
        if "CLASSIFICATION_TYPE" in line:
            list_omm.pop(i)
            break
    truncated_omm = "\n".join(list_omm)

    data = loads(truncated_omm)
    helper.assert_orbit(tle, data, "TLE")
    data.propagate(timedelta(1))

    list_omm = datafile("omm").splitlines()
    for i, line in enumerate(list_omm):
        if "EPHEMERIS_TYPE" in line:
            list_omm.pop(i)
            break
    truncated_omm = "\n".join(list_omm)

    data = loads(truncated_omm)
    helper.assert_orbit(tle, data, "TLE")
    data.propagate(timedelta(1))



def test_load_omm_cov(orbit_cov, datafile, helper):

    tle_cov = orbit_cov.copy(form="TLE")
    data = loads(datafile("omm_cov"))

    helper.assert_orbit(tle_cov, data)


def test_load_user_defined(tle, datafile, helper):

    data_omm = loads(datafile("omm_user_defined"))

    helper.assert_orbit(tle, data_omm)

    assert "ccsds_user_defined" in data_omm._data
    subdict = data_omm._data["ccsds_user_defined"]
    assert subdict["FOO"] == "foo enters"
    assert subdict["BAR"] == "a bar"


def test_load_omm_eh(ref_eh, datafile, helper):
    orb = loads(datafile("omm_eh"))
    helper.assert_orbit(ref_eh, orb, form="mean_circular")


def test_tle(tle, ccsds_format):
    # Check that a TLE and its OMM representation are the same

    txt = dumps(tle, fmt=ccsds_format)
    orb = loads(txt)
    new_tle = Tle.from_orbit(orb)
    assert str(tle.tle) == str(new_tle)

    assert all(tle == orb)
    date = Date(2020, 9, 30)
    assert all(tle.propagate(date) == orb.propagate(date))
