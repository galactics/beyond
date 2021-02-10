import numpy as np
import lxml.etree as ET

from ...utils import units
from ...orbits import Ephem, StateVector

from .commons import (
    parse_date,
    CcsdsError,
    dump_kvn_header,
    dump_kvn_meta_odm,
    dump_xml_header,
    dump_xml_meta_odm,
    DATE_FMT_DEFAULT,
    xml2dict,
    decode_unit,
    Field,
    get_format,
)
from .cov import load_cov


def loads(string, fmt):
    """
    Args:
        string (str): String containing the OEM
    Return:
        Ephem:
    """

    if fmt == "kvn":
        ephem = _loads_kvn(string)
    elif fmt == "xml":
        ephem = _loads_xml(string)
    else:  # pragma: no cover
        raise CcsdsError(f"Unknown format '{fmt}'")

    return ephem


def dumps(data, **kwargs):

    fmt = get_format(**kwargs)

    if isinstance(data, Ephem):
        data = [data]

    if fmt == "kvn":
        string = _dumps_kvn(data, **kwargs)
    elif fmt == "xml":
        string = _dumps_xml(data, **kwargs)
    else:  # pragma: no cover
        raise CcsdsError(f"Unknown format '{fmt}'")

    return string


def _loads_kvn(string):

    ephems = []
    required = ("REF_FRAME", "CENTER_NAME", "TIME_SYSTEM", "OBJECT_ID", "OBJECT_NAME")

    mode = None
    for line in string.splitlines():

        if not line or line.startswith("COMMENT"):  # pragma: no cover
            continue
        elif line.startswith("META_START"):
            mode = "meta"
            ephem = {"orbits": [], "orbit_mapping": {}}
            ephems.append(ephem)
        elif line.startswith("META_STOP"):
            mode = "data"

            # Check for required fields
            for k in required:
                if k not in ephem:
                    raise CcsdsError(f"Missing mandatory parameter '{k}'")

            # Conversion to be compliant with beyond.env.jpl dynamic reference
            # frames naming convention.
            if ephem["CENTER_NAME"].lower() != "earth":
                ephem["REF_FRAME"] = ephem["CENTER_NAME"].title().replace(" ", "")
        elif line == "COVARIANCE_START":
            mode = "covariance"
            ephem["dangling_covariance"] = []
        elif line == "COVARIANCE_STOP":
            mode = None
        elif mode == "meta":
            key, _, value = line.partition("=")
            ephem[key.strip()] = value.strip()
        elif mode == "data":
            date, *state_vector = line.split()
            date = parse_date(date, ephem["TIME_SYSTEM"])

            # Conversion from km to m, from km/s to m/s
            # and discard acceleration if present
            state_vector = np.array([float(x) for x in state_vector[:6]]) * units.km

            orb = StateVector(
                state_vector,
                date,
                "cartesian",
                ephem["REF_FRAME"],
                name=ephem["OBJECT_NAME"],
                cospar_id=ephem["OBJECT_ID"],
            )
            ephem["orbits"].append(orb)
            ephem["orbit_mapping"][date] = orb
        elif mode == "covariance":
            if line.startswith("EPOCH"):
                cov = {
                    "EPOCH": parse_date(
                        line.partition("=")[2].strip(), ephem["TIME_SYSTEM"]
                    )
                }
            elif line.startswith("COV_REF_FRAME"):
                cov["COV_REF_FRAME"] = Field(line.partition("=")[2].strip(), {})
            else:
                values = line.split()
                if len(values) > 6:  # pragma: no cover
                    raise CcsdsError("Unknown covariance field lenght")
                elif len(values) == 1:
                    cov["CX_X"] = Field(values[0], {})
                elif len(values) == 2:
                    cov["CY_X"] = Field(values[0], {})
                    cov["CY_Y"] = Field(values[1], {})
                elif len(values) == 3:
                    cov["CZ_X"] = Field(values[0], {})
                    cov["CZ_Y"] = Field(values[1], {})
                    cov["CZ_Z"] = Field(values[2], {})
                elif len(values) == 4:
                    cov["CX_DOT_X"] = Field(values[0], {})
                    cov["CX_DOT_Y"] = Field(values[1], {})
                    cov["CX_DOT_Z"] = Field(values[2], {})
                    cov["CX_DOT_X_DOT"] = Field(values[3], {})
                elif len(values) == 5:
                    cov["CY_DOT_X"] = Field(values[0], {})
                    cov["CY_DOT_Y"] = Field(values[1], {})
                    cov["CY_DOT_Z"] = Field(values[2], {})
                    cov["CY_DOT_X_DOT"] = Field(values[3], {})
                    cov["CY_DOT_Y_DOT"] = Field(values[4], {})
                elif len(values) == 6:
                    cov["CZ_DOT_X"] = Field(values[0], {})
                    cov["CZ_DOT_Y"] = Field(values[1], {})
                    cov["CZ_DOT_Z"] = Field(values[2], {})
                    cov["CZ_DOT_X_DOT"] = Field(values[3], {})
                    cov["CZ_DOT_Y_DOT"] = Field(values[4], {})
                    cov["CZ_DOT_Z_DOT"] = Field(values[5], {})

                    if cov["EPOCH"] in ephem["orbit_mapping"]:
                        orb = ephem["orbit_mapping"][cov["EPOCH"]]
                        cov_obj = load_cov(orb, cov)
                        orb.cov = cov_obj
                    else:  # pragma: no cover
                        raise CcsdsError(
                            "Impossible to attach a covariance matrix to an orbit object"
                        )
                else:  # pragma: no cover
                    continue

    for i, ephem_dict in enumerate(ephems):
        # In case there is no recommendation for interpolation
        # default to a Lagrange 8th order
        method = ephem_dict.get("INTERPOLATION", "Lagrange").lower()
        order = int(ephem_dict.get("INTERPOLATION_DEGREE", 7)) + 1
        ephem = Ephem(ephem_dict["orbits"], method=method, order=order)

        ephem.name = ephem_dict["OBJECT_NAME"]
        ephem.cospar_id = ephem_dict["OBJECT_ID"]
        ephems[i] = ephem

    if len(ephems) == 1:
        return ephems[0]

    return ephems


def _loads_xml(string):

    data = xml2dict(string.encode())

    ephems = []

    segments = data["body"]["segment"]
    if isinstance(segments, dict):
        segments = [segments]

    try:
        for segment in segments:
            metadata = segment["metadata"]
            data_tag = segment["data"]

            ref_frame = metadata["REF_FRAME"].text
            if metadata["CENTER_NAME"].text.lower() != "earth":
                ref_frame = metadata["CENTER_NAME"].text.title().replace(" ", "")

            ephem = []
            orbit_mapping = {}
            for statevector in data_tag["stateVector"]:
                orb = StateVector(
                    [
                        decode_unit(statevector, "X", units.km),
                        decode_unit(statevector, "Y", units.km),
                        decode_unit(statevector, "Z", units.km),
                        decode_unit(statevector, "X_DOT", units.km),
                        decode_unit(statevector, "Y_DOT", units.km),
                        decode_unit(statevector, "Z_DOT", units.km),
                    ],
                    parse_date(statevector["EPOCH"].text, metadata["TIME_SYSTEM"].text),
                    "cartesian",
                    ref_frame,
                    name=metadata["OBJECT_NAME"].text,
                    cospar_id=metadata["OBJECT_ID"].text,
                )
                ephem.append(orb)
                orbit_mapping[orb.date] = orb

            for cov in data_tag.get("covarianceMatrix", []):
                date = parse_date(cov["EPOCH"].text, metadata["TIME_SYSTEM"].text)
                if date in orbit_mapping:
                    orb = orbit_mapping[date]
                    orb.cov = load_cov(orb, cov)
                else:  # pragma: no cover
                    raise CcsdsError(
                        "Impossible to attach a covariance matrix to an orbit object"
                    )

            ephem = Ephem(
                ephem,
                method=metadata.get("INTERPOLATION", "Lagrange").text.lower(),
                order=int(metadata.get("INTERPOLATION_DEGREE", 7).text) + 1,
            )
            ephem.name = metadata["OBJECT_NAME"].text
            ephem.cospar_id = metadata["OBJECT_ID"].text
            ephems.append(ephem)
    except KeyError as e:
        raise CcsdsError(f"Missing mandatory parameter {e}")

    if len(ephems) == 1:
        ephems = ephems[0]

    return ephems


def _dumps_kvn(data, **kwargs):

    header = dump_kvn_header(data, "OEM", version="2.0", **kwargs)

    content = []
    for i, data in enumerate(data):

        data.form = "cartesian"

        extras = {
            "START_TIME": "{:{}}".format(data.start, DATE_FMT_DEFAULT),
            "STOP_TIME": "{:{}}".format(data.stop, DATE_FMT_DEFAULT),
            "INTERPOLATION": data.method.upper(),
        }
        if data.method != data.LINEAR:
            extras["INTERPOLATION_DEGREE"] = f"{data.order - 1}"

        meta = dump_kvn_meta_odm(data, extras=extras, **kwargs)

        text = []
        cov = []
        for orb in data:
            text.append(
                "{date:{dfmt}} {orb[0]:{fmt}} {orb[1]:{fmt}} {orb[2]:{fmt}} {orb[3]:{fmt}} {orb[4]:{fmt}} {orb[5]:{fmt}}".format(
                    date=orb.date,
                    orb=orb.base / units.km,
                    fmt=" 10f",
                    dfmt=DATE_FMT_DEFAULT,
                )
            )

            if orb.cov is not None:
                cov_text = []

                if cov:
                    cov_text.append("")

                cov_text.append(
                    "EPOCH = {date:{dfmt}}".format(date=orb.date, dfmt=DATE_FMT_DEFAULT)
                )

                if orb.cov.frame != orb.frame:
                    frame = orb.cov.frame
                    if frame == "QSW":
                        frame = "RSW"
                    cov_text.append(f"COV_REF_FRAME = {frame}")

                elems = ["X", "Y", "Z", "X_DOT", "Y_DOT", "Z_DOT"]

                for i in range(6):
                    line = []
                    for j in range(i + 1):
                        line.append(f"{orb.cov[i, j] / 1000000.0: 0.12e}")
                    cov_text.append(" ".join(line))

                cov.append("\n".join(cov_text))

        if cov:
            cov.insert(0, "\n\nCOVARIANCE_START")
            cov.append("COVARIANCE_STOP\n")

        content.append(meta + "\n".join(text) + "\n".join(cov))

    return header + "\n" + "\n\n\n".join(content)


def _dumps_xml(data, **kwargs):
    top = dump_xml_header(data, "OEM", version="2.0", **kwargs)
    body = ET.SubElement(top, "body")

    for i, data in enumerate(data):
        segment = ET.SubElement(body, "segment")

        extras = {
            "START_TIME": data.start.strftime(DATE_FMT_DEFAULT),
            "STOP_TIME": data.stop.strftime(DATE_FMT_DEFAULT),
            "INTERPOLATION": data.method.upper(),
        }
        if data.method != data.LINEAR:
            extras["INTERPOLATION_DEGREE"] = str(data.order - 1)

        dump_xml_meta_odm(segment, data, extras=extras, **kwargs)

        data_tag = ET.SubElement(segment, "data")

        for el in data:
            statevector = ET.SubElement(data_tag, "stateVector")
            epoch = ET.SubElement(statevector, "EPOCH")
            epoch.text = el.date.strftime(DATE_FMT_DEFAULT)

            elems = {
                "X": "x",
                "Y": "y",
                "Z": "z",
                "X_DOT": "vx",
                "Y_DOT": "vy",
                "Z_DOT": "vz",
            }

            for k, v in elems.items():
                x = ET.SubElement(
                    statevector, k, units="km" if "DOT" not in k else "km/s"
                )
                x.text = f"{getattr(el, v) / units.km:0.6f}"

        for el in data:
            if el.cov is not None:
                cov = ET.SubElement(data_tag, "covarianceMatrix")

                cov_date = ET.SubElement(cov, "EPOCH")
                cov_date.text = el.date.strftime(DATE_FMT_DEFAULT)

                if el.cov.frame != el.frame:
                    frame = el.cov.frame
                    if frame == "QSW":
                        frame = "RSW"

                    cov_frame = ET.SubElement(cov, "COV_REF_FRAME")
                    cov_frame.text = f"{frame}"

                elems = ["X", "Y", "Z", "X_DOT", "Y_DOT", "Z_DOT"]
                for i, a in enumerate(elems):
                    for j, b in enumerate(elems[: i + 1]):
                        x = ET.SubElement(cov, f"C{a}_{b}")
                        x.text = f"{el.cov[i, j] / 1000000.0:0.12e}"

    return ET.tostring(
        top, pretty_print=True, xml_declaration=True, encoding="UTF-8"
    ).decode()
