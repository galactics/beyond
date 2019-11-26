import numpy as np
import lxml.etree as ET

from ...orbits import Orbit
from ...propagators.sgp4 import Sgp4, wgs72

from .cov import load_cov, dump_cov
from .commons import (
    xml2dict,
    kvn2dict,
    parse_date,
    CcsdsParseError,
    decode_unit,
    code_unit,
    dump_kvn_header,
    dump_kvn_meta_odm,
    dump_xml_header,
    dump_xml_meta_odm,
    DATE_DEFAULT_FMT,
)


def load_omm(string, fmt):

    if fmt == "kvn":
        orb = _load_omm_kvn(string)
    elif fmt == "xml":
        orb = _load_omm_xml(string)
    else:
        raise CcsdsParseError("Unknwon format '{}'".format(fmt))

    return orb


def _load_omm_kvn(string):

    data = kvn2dict(string)
    # if "item" in data.keys():
    #     # To process Space-Track's OMM, wich are not CCSDS compliant...
    #     data = data["item"]

    try:
        name = data["OBJECT_NAME"].text
        cospar_id = data["OBJECT_ID"].text
        scale = data["TIME_SYSTEM"].text
        frame = data["REF_FRAME"].text
        date = parse_date(data["EPOCH"].text, scale)
    except KeyError as e:
        raise CcsdsParseError("Missing mandatory parameter {}".format(e))

    if data["MEAN_ELEMENT_THEORY"].text in ("SGP/SGP4", "SGP4"):
        try:
            n = decode_unit(data, "MEAN_MOTION", "rev/day")
            e = float(data["ECCENTRICITY"].text)
            i = decode_unit(data, "INCLINATION", "deg")
            Omega = decode_unit(data, "RA_OF_ASC_NODE", "deg")
            omega = decode_unit(data, "ARG_OF_PERICENTER", "deg")
            M = decode_unit(data, "MEAN_ANOMALY", "deg")
            ephemeris_type = int(data["EPHEMERIS_TYPE"].text)
            classification_type = data["CLASSIFICATION_TYPE"].text
            norad_id = int(data["NORAD_CAT_ID"].text)
            revolutions = int(data["REV_AT_EPOCH"].text)
            element_nb = int(data["ELEMENT_SET_NO"].text)

            elements = [i, Omega, e, omega, M, n]
            form = "TLE"
            propagator = "Sgp4"
            kwargs = {
                "bstar": decode_unit(data, "BSTAR", "1/ER"),
                "ndot": decode_unit(data, "MEAN_MOTION_DOT", "rev/day**2") * 2,
                "ndotdot": decode_unit(data, "MEAN_MOTION_DDOT", "rev/day**3") * 6,
                "ephemeris_type": ephemeris_type,
                "classification_type": classification_type,
                "norad_id": norad_id,
                "revolutions": revolutions,
                "element_nb": element_nb,
            }

        except KeyError as e:
            raise CcsdsParseError("Missing mandatory parameter '{}'".format(e))
    else:
        raise CcsdsParseError(
            "Unknown OMM theory '{}'".format(data["MEAN_ELEMENT_THEORY"].text)
        )

    orb = Orbit(date, elements, form, frame, propagator, **kwargs)
    orb.name = name
    orb.cospar_id = cospar_id
    if "NORAD_CAT_ID" in data:
        orb.norad_id = norad_id

    if "CX_X" in data:
        orb.cov = load_cov(orb, data)

    return orb


def _load_omm_xml(string):

    data = xml2dict(string.encode())

    # if "item" in data.keys():
    #     # To process Space-Track's OMM, wich are not CCSDS compliant...
    #     data = data["item"]

    metadata = data["body"]["segment"]["metadata"]
    mean_elements = data["body"]["segment"]["data"]["meanElements"]
    tle_params = data["body"]["segment"]["data"]["tleParameters"]
    cov = data["body"]["segment"]["data"].get("covarianceMatrix")

    try:
        name = metadata["OBJECT_NAME"].text
        cospar_id = metadata["OBJECT_ID"].text
        scale = metadata["TIME_SYSTEM"].text
        frame = metadata["REF_FRAME"].text
        date = parse_date(mean_elements["EPOCH"].text, scale)
    except KeyError as e:
        raise CcsdsParseError("Missing mandatory parameter {}".format(e))

    if metadata["MEAN_ELEMENT_THEORY"].text in ("SGP/SGP4", "SGP4"):
        try:
            n = decode_unit(mean_elements, "MEAN_MOTION", "rev/day")
            e = float(mean_elements["ECCENTRICITY"].text)
            i = decode_unit(mean_elements, "INCLINATION", "deg")
            Omega = decode_unit(mean_elements, "RA_OF_ASC_NODE", "deg")
            omega = decode_unit(mean_elements, "ARG_OF_PERICENTER", "deg")
            M = decode_unit(mean_elements, "MEAN_ANOMALY", "deg")
            ephemeris_type = int(tle_params["EPHEMERIS_TYPE"].text)
            classification_type = tle_params["CLASSIFICATION_TYPE"].text
            norad_id = int(tle_params["NORAD_CAT_ID"].text)
            revolutions = int(tle_params["REV_AT_EPOCH"].text)
            element_nb = int(tle_params["ELEMENT_SET_NO"].text)

            elements = [i, Omega, e, omega, M, n]
            form = "TLE"
            propagator = "Sgp4"
            kwargs = {
                "bstar": decode_unit(tle_params, "BSTAR", "1/ER"),
                "ndot": decode_unit(tle_params, "MEAN_MOTION_DOT", "rev/day**2") * 2,
                "ndotdot": decode_unit(tle_params, "MEAN_MOTION_DDOT", "rev/day**3")
                * 6,
                "ephemeris_type": ephemeris_type,
                "classification_type": classification_type,
                "norad_id": norad_id,
                "revolutions": revolutions,
                "element_nb": element_nb,
            }

        except KeyError as e:
            raise CcsdsParseError("Missing mandatory parameter {}".format(e))
    else:
        raise CcsdsParseError(
            "Unknown OMM theory '{}'".format(data["MEAN_ELEMENT_THEORY"].text)
        )

    orb = Orbit(date, elements, form, frame, propagator, **kwargs)
    orb.name = name
    orb.cospar_id = cospar_id

    if cov:
        orb.cov = load_cov(orb, cov)

    return orb


def dump_omm(data, fmt="kvn", **kwargs):

    if fmt == "kvn":

        header = dump_kvn_header(data, "OMM", version="2.0", **kwargs)

        if isinstance(data.propagator, Sgp4):
            theory = "SGP/SGP4"
        else:
            raise CcsdsParseError(
                "Unknown propagator type '{}' for OMM".format(data.propagator)
            )

        meta = dump_kvn_meta_odm(
            data, meta_tag=False, extras={"MEAN_ELEMENT_THEORY": theory}, **kwargs
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

        string = header + "\n" + meta + text

    elif fmt == "xml":

        top = dump_xml_header(data, "OMM", version="2.0", **kwargs)

        body = ET.SubElement(top, "body")
        segment = ET.SubElement(body, "segment")

        if isinstance(data.propagator, Sgp4):
            theory = "SGP/SGP4"
        else:
            raise CcsdsParseError(
                "Unknown propagator type '{}' for OMM".format(data.propagator)
            )

        dump_xml_meta_odm(
            segment, data, extras={"MEAN_ELEMENT_THEORY": theory}, **kwargs
        )

        data_tag = ET.SubElement(segment, "data")

        meanelements = ET.SubElement(data_tag, "meanElements")

        epoch = ET.SubElement(meanelements, "EPOCH")
        epoch.text = data.date.strftime(DATE_DEFAULT_FMT)

        sma = ET.SubElement(meanelements, "MEAN_MOTION", units="rev/day")
        sma.text = "{:0.8f}".format(code_unit(data, "n", "rev/day"))
        ecc = ET.SubElement(meanelements, "ECCENTRICITY")
        ecc.text = "{:0.7f}".format(data.e)

        elems = {
            "INCLINATION": "i",
            "RA_OF_ASC_NODE": "Omega",
            "ARG_OF_PERICENTER": "omega",
            "MEAN_ANOMALY": "M",
        }
        for k, v in elems.items():
            x = ET.SubElement(meanelements, k, units="deg")
            x.text = "{:0.4f}".format(np.degrees(getattr(data, v)))

        gm = ET.SubElement(meanelements, "GM", units="km**3/s**2")
        gm.text = "{:0.1f}".format(wgs72.mu)

        if theory == "SGP/SGP4":
            tle_params = ET.SubElement(data_tag, "tleParameters")
            ephemeris_type = ET.SubElement(tle_params, "EPHEMERIS_TYPE")
            ephemeris_type.text = "0"
            classification = ET.SubElement(tle_params, "CLASSIFICATION_TYPE")
            classification.text = "U"
            norad_id = ET.SubElement(tle_params, "NORAD_CAT_ID")
            norad_id.text = str(data.norad_id)
            element_nb = ET.SubElement(tle_params, "ELEMENT_SET_NO")
            element_nb.text = str(data.element_nb)
            revolutions = ET.SubElement(tle_params, "REV_AT_EPOCH")
            revolutions.text = str(data.revolutions)

            bstar = ET.SubElement(tle_params, "BSTAR")
            bstar.text = "{:.4f}".format(data.bstar)

            ndot = ET.SubElement(tle_params, "MEAN_MOTION_DOT")
            ndot.text = "{:.8f}".format(data.ndot)

            ndotdot = ET.SubElement(tle_params, "MEAN_MOTION_DDOT")
            ndotdot.text = "{:.1f}".format(data.ndotdot)

        if data.cov.any():
            cov = ET.SubElement(data_tag, "covarianceMatrix")

            if data.cov.frame != data.cov.PARENT_FRAME:
                frame = data.cov.frame
                if frame == "QSW":
                    frame = "RSW"

                cov_frame = ET.SubElement(cov, "COV_REF_FRAME")
                cov_frame.text = "{frame}".format(frame=frame)

            elems = ["X", "Y", "Z", "X_DOT", "Y_DOT", "Z_DOT"]
            for i, a in enumerate(elems):
                for j, b in enumerate(elems[: i + 1]):
                    x = ET.SubElement(cov, "C{a}_{b}".format(a=a, b=b))
                    x.text = "{:0.16e}".format(data.cov[i, j] * 1e-6)

        string = ET.tostring(
            top, pretty_print=True, encoding="UTF-8", xml_declaration=True
        ).decode()

    else:
        raise CcsdsParseError("Unknown format '{}'".format(fmt))

    return string
