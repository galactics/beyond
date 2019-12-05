import numpy as np
import lxml.etree as ET

from ...dates import Date
from ...utils import units
from ...orbits import Orbit, Ephem

from .commons import (
    parse_date,
    CcsdsParseError,
    dump_kvn_header,
    dump_kvn_meta_odm,
    dump_xml_header,
    dump_xml_meta_odm,
    DATE_DEFAULT_FMT,
    xml2dict,
    decode_unit,
)


def load_oem(string, fmt):
    """
    Args:
        string (str): String containing the OEM
    Return:
        Ephem:
    """

    if fmt == "kvn":
        ephem = _load_oem_kvn(string)
    elif fmt == "xml":
        ephem = _load_oem_xml(string)
    else:  # pragma: no cover
        raise CcsdsParseError("Unknwon format '{}'".format(fmt))

    return ephem


def _load_oem_kvn(string):

    ephems = []
    required = ("REF_FRAME", "CENTER_NAME", "TIME_SYSTEM", "OBJECT_ID", "OBJECT_NAME")

    mode = None
    for line in string.splitlines():

        if not line or line.startswith("COMMENT"):  # pragma: no cover
            continue
        elif line.startswith("META_START"):
            mode = "meta"
            ephem = {"orbits": []}
            ephems.append(ephem)
        elif line.startswith("META_STOP"):
            mode = "data"

            # Check for required fields
            for k in required:
                if k not in ephem:
                    raise CcsdsParseError("Missing field '{}'".format(k))

            # Conversion to be compliant with beyond.env.jpl dynamic reference
            # frames naming convention.
            if ephem["CENTER_NAME"].lower() != "earth":
                ephem["REF_FRAME"] = ephem["CENTER_NAME"].title().replace(" ", "")
        elif mode == "meta":
            key, _, value = line.partition("=")
            ephem[key.strip()] = value.strip()
        elif mode == "data":
            date, *state_vector = line.split()
            date = parse_date(date, ephem["TIME_SYSTEM"])

            # Conversion from km to m, from km/s to m/s
            # and discard acceleration if present
            state_vector = np.array([float(x) for x in state_vector[:6]]) * units.km

            ephem["orbits"].append(
                Orbit(date, state_vector, "cartesian", ephem["REF_FRAME"], None)
            )

    for i, ephem_dict in enumerate(ephems):
        if not ephem_dict["orbits"]:
            raise CcsdsParseError("Empty ephemeris")

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


def _load_oem_xml(string):

    data = xml2dict(string.encode())

    ephems = []

    segments = data["body"]["segment"]
    if isinstance(segments, dict):
        segments = [segments]

    for segment in segments:
        metadata = segment["metadata"]
        data_tag = segment["data"]

        ref_frame = metadata["REF_FRAME"].text
        if metadata["CENTER_NAME"].text.lower() != "earth":
            ref_frame = metadata["CENTER_NAME"].text.title().replace(" ", "")

        ephem = []
        for statevector in data_tag["stateVector"]:
            ephem.append(
                Orbit(
                    parse_date(statevector["EPOCH"].text, metadata["TIME_SYSTEM"].text),
                    [
                        decode_unit(statevector, "X", units.km),
                        decode_unit(statevector, "Y", units.km),
                        decode_unit(statevector, "Z", units.km),
                        decode_unit(statevector, "X_DOT", units.km),
                        decode_unit(statevector, "Y_DOT", units.km),
                        decode_unit(statevector, "Z_DOT", units.km),
                    ],
                    "cartesian",
                    ref_frame,
                    None,
                )
            )

        ephem = Ephem(
            ephem,
            method=metadata.get("INTERPOLATION", "Lagrange").text.lower(),
            order=int(metadata.get("INTERPOLATION_DEGREE", 7).text) + 1,
        )
        ephem.name = metadata["OBJECT_NAME"].text
        ephem.cospar_id = metadata["OBJECT_ID"].text
        ephems.append(ephem)

    if len(ephems) == 1:
        ephems = ephems[0]

    return ephems


def dump_oem(data, fmt="kvn", **kwargs):

    if isinstance(data, Ephem):
        data = [data]

    if fmt == "kvn":
        header = dump_kvn_header(data, "OEM", version="2.0", **kwargs)

        content = []
        for i, data in enumerate(data):

            data.form = "cartesian"

            extras = {
                "START_TIME": "{:{}}".format(data.start, DATE_DEFAULT_FMT),
                "STOP_TIME": "{:{}}".format(data.stop, DATE_DEFAULT_FMT),
                "INTERPOLATION": data.method.upper(),
            }
            if data.method != data.LINEAR:
                extras["INTERPOLATION_DEGREE"] = "{}".format(data.order - 1)

            meta = dump_kvn_meta_odm(data, extras=extras, **kwargs)

            text = []
            for orb in data:
                text.append(
                    "{date:%Y-%m-%dT%H:%M:%S.%f} {orb[0]:{fmt}} {orb[1]:{fmt}} {orb[2]:{fmt}} {orb[3]:{fmt}} {orb[4]:{fmt}} {orb[5]:{fmt}}".format(
                        date=orb.date, orb=orb.base / units.km, fmt=" 10f"
                    )
                )

            content.append(meta + "\n".join(text))

        string = header + "\n" + "\n\n\n".join(content)

    elif fmt == "xml":
        top = dump_xml_header(data, "OEM", version="2.0", **kwargs)
        body = ET.SubElement(top, "body")

        for i, data in enumerate(data):
            segment = ET.SubElement(body, "segment")

            extras = {
                "START_TIME": data.start.strftime(DATE_DEFAULT_FMT),
                "STOP_TIME": data.stop.strftime(DATE_DEFAULT_FMT),
                "INTERPOLATION": data.method.upper(),
            }
            if data.method != data.LINEAR:
                extras["INTERPOLATION_DEGREE"] = str(data.order - 1)

            dump_xml_meta_odm(segment, data, extras=extras, **kwargs)

            data_tag = ET.SubElement(segment, "data")

            for el in data:
                statevector = ET.SubElement(data_tag, "stateVector")
                epoch = ET.SubElement(statevector, "EPOCH")
                epoch.text = el.date.strftime(DATE_DEFAULT_FMT)

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
                    x.text = "{:0.6f}".format(getattr(el, v) / units.km)

            for el in data:
                if el.cov.any():
                    cov = ET.SubElement(data_tag, "covarianceMatrix")

                    if el.cov.frame != el.cov.PARENT_FRAME:
                        frame = el.cov.frame
                        if frame == "QSW":
                            frame = "RSW"

                        cov_frame = ET.SubElement(cov, "COV_REF_FRAME")
                        cov_frame.text = "{frame}".format(frame=frame)

                    elems = ["X", "Y", "Z", "X_DOT", "Y_DOT", "Z_DOT"]
                    for i, a in enumerate(elems):
                        for j, b in enumerate(elems[: i + 1]):
                            x = ET.SubElement(cov, "C{a}_{b}".format(a=a, b=b))
                            x.text = "{:0.16e}".format(el.cov[i, j] / 1e6)

        string = ET.tostring(
            top, pretty_print=True, xml_declaration=True, encoding="UTF-8"
        ).decode()

    else:  # pragma: no cover
        raise CcsdsParseError("Unknown format '{}'".format(fmt))

    return string
