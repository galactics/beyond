
from pytest import raises

from beyond.env.jpl import create_frames
from beyond.io.ccsds import dumps, loads, CcsdsParseError


def test_dump_opm(orbit, datafile, ccsds_format, helper):

    ref = datafile("opm")
    txt = dumps(orbit, fmt=ccsds_format)

    helper.assert_string(ref, txt)


def test_dump_opm_cov(orbit_cov, datafile, ccsds_format, helper):

    ref = datafile("opm_cov")
    txt = dumps(orbit_cov, fmt=ccsds_format)

    helper.assert_string(ref, txt)

    # Conversion to TNW
    orbit_cov2 = orbit_cov.copy()
    orbit_cov2.cov.frame = "TNW"
    txt = dumps(orbit_cov2, fmt=ccsds_format)

    helper.assert_string(datafile("opm_cov_tnw"), txt)

    # Conversion to QSW
    orbit_cov3 = orbit_cov.copy()
    orbit_cov3.cov.frame = "QSW"
    txt = dumps(orbit_cov3, fmt=ccsds_format)
    
    helper.assert_string(datafile("opm_cov_qsw"), txt)


def test_dump_opm_man_impulsive(orbit_man, datafile, ccsds_format, helper):

    ref = datafile("opm_impulsive_man")
    txt = dumps(orbit_man, fmt=ccsds_format)

    helper.assert_string(ref, txt)


def test_dump_opm_man_continuous(orbit_continuous_man, datafile, ccsds_format, helper):
    ref = datafile("opm_impulsive_man")
    txt = dumps(orbit_continuous_man, fmt=ccsds_format)

    helper.assert_string(ref, txt, ignore="MAN_DURATION")


def test_dump_opm_interplanetary(jplfiles, orbit, ccsds_format, datafile, helper):
    create_frames("Mars")
    orbit.frame = "Mars"

    txt = dumps(orbit, fmt=ccsds_format)
    helper.assert_string(datafile("opm_interplanetary"), txt)


########## LOAD

def test_load_opm(orbit, datafile, helper):

    data = loads(datafile("opm"))
    helper.assert_orbit(orbit, data)


def test_load_opm_no_unit(orbit, datafile, helper):
    data = loads(datafile("opm_no_unit"))
    helper.assert_orbit(orbit, data)


def test_load_opm_strange_unit(datafile):
    # Dummy units, that aren't specified as valid
    with raises(CcsdsParseError) as e:
        loads(datafile("opm_strange_units"))

    assert str(e.value) == "Unknown unit 'm/s' for the field X_DOT"


def test_load_opm_truncated(datafile):
    # One mandatory line is missing

    list_opm = datafile("opm").splitlines()

    for i, line in enumerate(list_opm):
        if "EPOCH" in line:
            list_opm.pop(i)
            break
    truncated_opm = "\n".join(list_opm)

    with raises(CcsdsParseError) as e:
        loads(truncated_opm)

    assert str(e.value) == "Missing mandatory parameter 'EPOCH'"


def test_load_opm_cov(orbit_cov, datafile, helper):
    data_opm = loads(datafile("opm_cov"))

    helper.assert_orbit(orbit_cov, data_opm)


def test_load_opm_cov_qsw(orbit_cov, datafile, helper):
    data_opm = loads(datafile("opm_cov_qsw"))
    orbit_cov.cov.frame = "QSW"

    helper.assert_orbit(orbit_cov, data_opm, cov_eps=1e-12)


def test_load_opm_man_impulsive(orbit_man, datafile, helper, ccsds_format):

    str_data_opm_man = datafile("opm_impulsive_man")
    data_opm_man = loads(str_data_opm_man)

    helper.assert_orbit(orbit_man, data_opm_man)

    list_data_opm_man = str_data_opm_man.splitlines()
    if ccsds_format == "kvn":
        number = 0
        for i, line in enumerate(list_data_opm_man):
            if ccsds_format == "kvn" and "MAN_EPOCH_IGNITION" in line:
                if number:
                    list_data_opm_man = list_data_opm_man[:i]
                    break
                else:
                    number += 1
        data = "\n".join(list_data_opm_man)
    else:
        continue_flag = False
        new_data = []
        number = 0
        for line in list_data_opm_man:
            if continue_flag:
                if "</maneuverParameters>" in line:
                    continue_flag = False
                continue
            if "<maneuverParameters>" in line:
                if number:
                    continue_flag = True
                    continue
                number += 1

            new_data.append(line)
        data = "\n".join(new_data)

    orbit_man.maneuvers = orbit_man.maneuvers[0]
    data = loads(data)

    helper.assert_orbit(orbit_man, data)


def test_load_opm_man_continuous(orbit_continuous_man, datafile, ccsds_format, helper):

    # Tweak the reference to convert impulsive maneuvers into continuous ones
    data_continuous_man = datafile("opm_impulsive_man").splitlines()

    for i, line in enumerate(data_continuous_man):
        if "MAN_DURATION" in line:
            if ccsds_format == "kvn":
                data_continuous_man[i] = "MAN_DURATION         = 180.000 [s]"
            else:
                data_continuous_man[i] = '          <MAN_DURATION units="s">180.000</MAN_DURATION>'

    data_continuous_man = loads("\n".join(data_continuous_man))

    helper.assert_orbit(orbit_continuous_man, data_continuous_man)


def test_load_interplanetary(jplfiles, orbit, datafile, helper):

    create_frames(until="Mars")
    orbit.frame = "Mars"

    data_opm = loads(datafile("opm_interplanetary"))

    helper.assert_orbit(orbit, data_opm)
