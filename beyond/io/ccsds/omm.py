import numpy as np
import lxml.etree as ET

from ...orbits import Orbit
from ...propagators.sgp4 import Sgp4, wgs72

from .cov import load_cov, dump_cov
from .commons import (
    xml2dict,
    kvn2dict,
    parse_date,
    CcsdsError,
    decode_unit,
    code_unit,
    dump_kvn_header,
    dump_kvn_meta_odm,
    dump_xml_header,
    dump_xml_meta_odm,
    DATE_FMT_DEFAULT,
    get_format,
)


def loads(string, fmt):

    if fmt == "kvn":
        orb = _loads_kvn(string)
    elif fmt == "xml":
        orb = _loads_xml(string)
    else:  # pragma: no cover
        raise CcsdsError(f"Unknown format '{fmt}'")

    return orb


def dumps(data, **kwargs):

    # Inject a default format if it is not provided, either by argument or by configuration
    fmt = get_format(**kwargs)

    if fmt == "kvn":
        string = _dumps_kvn(data, **kwargs)
    elif fmt == "xml":
        string = _dumps_xml(data, **kwargs)
    else:  # pragma: no cover
        raise CcsdsError(f"Unknown format '{fmt}'")

    return string


def _loads_kvn(string):

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
        raise CcsdsError(f"Missing mandatory parameter {e}")

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
                "cospar_id": cospar_id,
                "name": name,
            }

        except KeyError as e:
            raise CcsdsError(f"Missing mandatory parameter {e}")
    else:  # pragma: no cover
        raise CcsdsError(f"Unknown OMM theory '{data['MEAN_ELEMENT_THEORY'].text}'")

    orb = Orbit(elements, date, form, frame, propagator, **kwargs)

    if "CX_X" in data:
        orb.cov = load_cov(orb, data)

    for k in data.keys():
        if k.startswith("USER_DEFINED"):
            ud = orb._data.setdefault("ccsds_user_defined", {})
            ud[k[13:]] = data[k].text

    return orb


def _loads_xml(string):

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
        raise CcsdsError(f"Missing mandatory parameter {e}")

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
            raise CcsdsError(f"Missing mandatory parameter {e}")
    else:  # pragma: no cover
        raise CcsdsError(f"Unknown OMM theory '{data['MEAN_ELEMENT_THEORY'].text}'")

    orb = Orbit(elements, date, form, frame, propagator, **kwargs)
    orb.name = name
    orb.cospar_id = cospar_id

    if cov:
        orb.cov = load_cov(orb, cov)

    ud_dict = data["body"]["segment"]["data"].get("userDefinedParameters", {})

    for field in ud_dict.get("USER_DEFINED", []):
        ud = orb._data.setdefault("ccsds_user_defined", {})
        ud[field.attrib["parameter"]] = field.text

    return orb


def _dumps_kvn(data, **kwargs):

    header = dump_kvn_header(data, "OMM", version="2.0", **kwargs)

    if isinstance(data.propagator, Sgp4):
        theory = "SGP/SGP4"
    else:  # pragma: no cover
        raise CcsdsError(f"Unknown propagator type '{data.propagator}' for OMM")

    meta = dump_kvn_meta_odm(
        data, meta_tag=False, extras={"MEAN_ELEMENT_THEORY": theory}, **kwargs
    )

    text = """
EPOCH                = {tle.date:{dfmt}}
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
BSTAR                = {bstar:6.9f} [1/ER]
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
        dfmt=DATE_FMT_DEFAULT,
    )

    if data.cov is not None:
        text += dump_cov(data.cov)

    if "ccsds_user_defined" in data._data:
        text += "\n"
        for k, v in data._data["ccsds_user_defined"].items():
            text += f"USER_DEFINED_{k} = {v}\n"

    return header + "\n" + meta + text


def _dumps_xml(data, **kwargs):
    top = dump_xml_header(data, "OMM", version="2.0", **kwargs)

    body = ET.SubElement(top, "body")
    segment = ET.SubElement(body, "segment")

    if isinstance(data.propagator, Sgp4):
        theory = "SGP/SGP4"
    else:  # pragma: no cover
        raise CcsdsError(f"Unknown propagator type '{data.propagator}' for OMM")

    dump_xml_meta_odm(segment, data, extras={"MEAN_ELEMENT_THEORY": theory}, **kwargs)

    data_tag = ET.SubElement(segment, "data")

    meanelements = ET.SubElement(data_tag, "meanElements")

    epoch = ET.SubElement(meanelements, "EPOCH")
    epoch.text = data.date.strftime(DATE_FMT_DEFAULT)

    sma = ET.SubElement(meanelements, "MEAN_MOTION", units="rev/day")
    sma.text = f"{code_unit(data, 'n', 'rev/day'):0.8f}"
    ecc = ET.SubElement(meanelements, "ECCENTRICITY")
    ecc.text = f"{data.e:0.7f}"

    elems = {
        "INCLINATION": "i",
        "RA_OF_ASC_NODE": "Omega",
        "ARG_OF_PERICENTER": "omega",
        "MEAN_ANOMALY": "M",
    }
    for k, v in elems.items():
        x = ET.SubElement(meanelements, k, units="deg")
        x.text = f"{np.degrees(getattr(data, v)):0.4f}"

    gm = ET.SubElement(meanelements, "GM", units="km**3/s**2")
    gm.text = f"{wgs72.mu:0.1f}"

    if theory == "SGP/SGP4":  # pragma: no branch
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
        bstar.text = f"{data.bstar:.9f}"

        ndot = ET.SubElement(tle_params, "MEAN_MOTION_DOT")
        ndot.text = f"{data.ndot / 2:.8f}"

        ndotdot = ET.SubElement(tle_params, "MEAN_MOTION_DDOT")
        ndotdot.text = f"{data.ndotdot / 6:.1f}"

    if data.cov is not None:
        cov = ET.SubElement(data_tag, "covarianceMatrix")

        if data.cov.frame != data.frame:
            frame = data.cov.frame
            if frame == "QSW":
                frame = "RSW"

            cov_frame = ET.SubElement(cov, "COV_REF_FRAME")
            cov_frame.text = f"{frame}"

        elems = ["X", "Y", "Z", "X_DOT", "Y_DOT", "Z_DOT"]
        for i, a in enumerate(elems):
            for j, b in enumerate(elems[: i + 1]):
                x = ET.SubElement(cov, f"C{a}_{b}")
                x.text = f"{data.cov[i, j] / 1000000.0:0.12e}"

    if "ccsds_user_defined" in data._data:
        ud = ET.SubElement(data_tag, "userDefinedParameters")
        for k, v in data._data["ccsds_user_defined"].items():
            el = ET.SubElement(ud, "USER_DEFINED", parameter=k)
            el.text = v

    return ET.tostring(
        top, pretty_print=True, encoding="UTF-8", xml_declaration=True
    ).decode()
