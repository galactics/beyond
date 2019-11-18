from ...orbits import Orbit
from ...propagators.sgp4 import Sgp4, wgs72

from .cov import read_cov, dump_cov
from .commons import (
    str2dict,
    parse_date,
    CcsdsParseError,
    decode_unit,
    code_unit,
    _dump_header,
    _dump_meta_odm,
)


def read_omm(string):

    data = str2dict(string)

    try:
        name = data["OBJECT_NAME"]
        cospar_id = data["OBJECT_ID"]
        scale = data["TIME_SYSTEM"]
        frame = data["REF_FRAME"]
        date = parse_date(data["EPOCH"], scale)
    except KeyError as e:
        raise CcsdsParseError("Missing mandatory parameter '{}'".format(e))

    if data["MEAN_ELEMENT_THEORY"] in ("SGP/SGP4", "SGP4"):
        try:
            n = decode_unit(data, "MEAN_MOTION", "rev/day")
            e = float(data["ECCENTRICITY"])
            i = decode_unit(data, "INCLINATION", "deg")
            Omega = decode_unit(data, "RA_OF_ASC_NODE", "deg")
            omega = decode_unit(data, "ARG_OF_PERICENTER", "deg")
            M = decode_unit(data, "MEAN_ANOMALY", "deg")
            ephemeris_type = float(data["EPHEMERIS_TYPE"])
            classification_type = data["CLASSIFICATION_TYPE"]
            norad_id = float(data["NORAD_CAT_ID"])
            revolutions = float(data["REV_AT_EPOCH"])

            elements = [i, Omega, e, omega, M, n]
            form = "TLE"
            propagator = "Sgp4"
            kwargs = {
                "bstar": decode_unit(data, "BSTAR", "1/ER"),
                "ndot": decode_unit(data, "MEAN_MOTION_DOT", "rev/day**2") * 2,
                "ndotdot": decode_unit(data, "MEAN_MOTION_DDOT", "rev/day**3") * 6,
            }

        except KeyError as e:
            raise CcsdsParseError("Missing mandatory parameter '{}'".format(e))
    else:
        raise CcsdsParseError(
            "Unknown OMM theory '{}'".format(data["MEAN_ELEMENT_THEORY"])
        )

    orb = Orbit(date, elements, form, frame, propagator, **kwargs)
    orb.name = name
    orb.cospar_id = cospar_id
    if "NORAD_CAT_ID" in data:
        orb.norad_id = norad_id

    if "CX_X" in data:
        orb.cov = read_cov(orb, data)

    return orb


def dump_omm(data, **kwargs):
    header = _dump_header(data, "OMM", version="2.0", **kwargs)

    if isinstance(data.propagator, Sgp4):
        theory = "SGP/SGP4"
    else:
        raise CcsdsParseError(
            "Unknown propagator type '{}' for OMM".format(data.propagator)
        )

    meta = _dump_meta_odm(data, meta_tag=False, **kwargs)
    meta += """TIME_SYSTEM          = {orb.date.scale.name}
MEAN_ELEMENT_THEORY  = {theory}

""".format(
        orb=data, theory=theory
    )

    text = """
EPOCH                = {tle.date:%Y-%m-%dT%H:%M:%S.%f}
MEAN_MOTION          = {n: 12.8f} [rev/day]
ECCENTRICITY         = {tle.e: 11.7f}
INCLINATION          = {i: 8.4f} [deg]
RA_OF_ASC_NODE       = {Omega:8.4f} [deg]
ARG_OF_PERICENTER    = {omega:8.4f} [deg]
MEAN_ANOMALY         = {M:8.4f} [deg]
GM                   = {mu:0.1f} [km**3/s**2]

EPHEMERIS_TYPE       = {tle.tle.type}
CLASSIFICATION_TYPE  = {tle.tle.classification:}
NORAD_CAT_ID         = {tle.tle.norad_id}
ELEMENT_SET_NO       = {tle.tle.element_nb}
REV_AT_EPOCH         = {tle.tle.revolutions}
BSTAR                = {bstar:6.4f} [1/ER]
MEAN_MOTION_DOT      = {ndot: 10.8f} [rev/day**2]
MEAN_MOTION_DDOT     = {ndotdot:0.1f} [rev/day**3]
""".format(
        n=code_unit(data, "n", "rev/day"),
        i=code_unit(data, "i", "deg"),
        Omega=code_unit(data, "Omega", "deg"),
        omega=code_unit(data, "omega", "deg"),
        M=code_unit(data, "M", "deg"),
        tle=data,
        bstar=code_unit(data, "bstar", "1/ER"),
        ndot=code_unit(data, "ndot", "rev/day**2") / 2,
        ndotdot=code_unit(data, "ndotdot", "rev/day**3") / 6,
        mu=wgs72.mu,  # this is already in km**3/s**2
    )

    if data.cov.any():
        text += dump_cov(data.cov)

    return header + "\n" + meta + text
