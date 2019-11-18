import numpy as np
import xml.etree.ElementTree as ET

from ...utils import units
from ...dates import Date
from ...errors import ParseError


class CcsdsParseError(ParseError):
    pass


units_dict = {
    "km": units.km,
    "km/s": units.km,
    "s": 1,
    "deg": np.pi / 180.0,
    "rev/day": 2 * np.pi / units.day,
    "rev/day**2": 1,
    "rev/day**3": 1,
    "1/ER": 1,
    "km**3/s**2": units.km ** 3,
}


def decode_unit(data, name, default=None):
    """Conversion of state vector field, with automatic unit handling
    """

    value = data[name]

    if "[" in value:
        # There is a unit field
        value, sep, unit = value.partition("[")
        unit = unit.rstrip("]")
    else:
        unit = default

    if unit not in units_dict:
        raise CcsdsParseError("Unknown unit '{}' for the field {}".format(unit, name))

    return float(value) * units_dict[unit]


def code_unit(data, name, unit):
    """Convert the value in SI to a specific unit
    """

    if unit not in units_dict:
        raise CcsdsParseError("Unknown unit '{}' for the field {}".format(unit, name))

    return data[name] / units_dict[unit]


def parse_date(string, scale):

    try:
        out = Date.strptime(string, "%Y-%m-%dT%H:%M:%S.%f", scale=scale)
    except ValueError:
        try:
            out = Date.strptime(string, "%Y-%jT%H:%M:%S.%f", scale=scale)
        except ValueError:
            out = Date.strptime(string, "%Y-%m-%dT%H:%M:%S", scale=scale)

    return out


def str2dict(string):
    if string.startswith("CCSDS_"):
        return kvn2dict(string)
    else:
        return xml2dict(string)


def xml2dict(string):

    root = ET.fromstring(string)

    data = {}
    for item in root.iter("item"):
        for child in item:
            data[child.tag] = child.text

    return data


def kvn2dict(string):
    """Convert KVN (Key-Value Notation) to a dictionnary for easy reuse

    Args:
        string (str)
    Return:
        dict
    """

    data = {}
    comments = {}
    for i, line in enumerate(string.splitlines()):
        if not line:
            continue
        if line.startswith("COMMENT"):
            comments[i] = line.split("COMMENT")[-1].strip()
            continue

        key, _, value = line.partition("=")

        key = key.strip()
        value = value.strip()

        if key.startswith("MAN_"):
            if key == "MAN_EPOCH_IGNITION":
                man = {}
                data.setdefault("MAN", []).append(man)
                if i - 1 in comments:
                    man["comment"] = comments[i - 1]
            man[key] = value
        else:
            data[key] = value

    return data


def _dump_header(data, ccsds_type, version="1.0", **kwargs):

    return """CCSDS_{type}_VERS = {version}
CREATION_DATE = {creation_date:%Y-%m-%dT%H:%M:%S}
ORIGINATOR = {originator}
""".format(
        type=ccsds_type.upper(),
        creation_date=Date.now(),
        originator=kwargs.get("originator", "N/A"),
        version=version,
    )


def _dump_meta_odm(data, meta_tag=True, **kwargs):

    meta = """{meta}OBJECT_NAME          = {name}
OBJECT_ID            = {cospar_id}
CENTER_NAME          = {center}
REF_FRAME            = {frame}
""".format(
        meta="META_START\n" if meta_tag else "",
        name=kwargs.get("name", getattr(data, "name", "N/A")),
        cospar_id=kwargs.get("cospar_id", getattr(data, "cospar_id", "N/A")),
        center=data.frame.center.name.upper(),
        frame=data.frame.orientation.upper(),
    )

    return meta
