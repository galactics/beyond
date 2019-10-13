import re
import numpy as np
import lxml.etree as ET
from collections import namedtuple
from collections.abc import Iterable

from ...utils import units
from ...dates import Date
from ...orbits import StateVector, Orbit, Ephem
from ...errors import ParseError
from ...utils.measures import Measure
from ...propagators.base import AnalyticalPropagator
from ...frames.frames import TEME
from ...orbits.forms import TLE
from ...config import config


class CcsdsError(ParseError):
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


Field = namedtuple("Field", "text attrib")
DATE_FMT_DEFAULT = "%Y-%m-%dT%H:%M:%S.%f"
DATE_FMT_NO_MSEC = "%Y-%m-%dT%H:%M:%S"
DATE_FMT_D_OF_Y = "%Y-%jT%H:%M:%S.%f"

DEFAULT_FMT = "kvn"


def get_format(**kwargs):
    """retrieve the format to dump the file into"""
    return kwargs.get(
        "fmt", config.get("io", "ccsds_default_format", fallback=DEFAULT_FMT)
    )


def decode_unit(data, name, default=None):
    """Conversion of state vector field, with automatic unit handling"""

    value = data[name].text
    unit = data[name].attrib.get("units", default)

    if unit not in units_dict:
        raise CcsdsError(f"Unknown unit '{unit}' for the field {name}")

    return float(value) * units_dict[unit]


def code_unit(data, name, unit):
    """Convert the value in SI to a specific unit"""

    if unit not in units_dict:
        raise CcsdsError(f"Unknown unit '{unit}' for the field {name}")

    return data[name] / units_dict[unit]


def parse_date(string, scale):
    """Parse a date formated as described in the CCSDS Blue Books"""

    try:
        out = Date.strptime(string, DATE_FMT_DEFAULT, scale=scale)
    except ValueError:
        try:
            out = Date.strptime(string, DATE_FMT_D_OF_Y, scale=scale)
        except ValueError:
            out = Date.strptime(string, DATE_FMT_NO_MSEC, scale=scale)

    return out


def detect2load(string):
    """Detect the type and format of the CCSDS file

    types may be : "OPM", "OMM", "OEM", "TDM"
    format may be: "kvn" or "xml"
    """

    format = "kvn" if string.lstrip().startswith("CCSDS_") else "xml"

    m = re.search(r"CCSDS_([A-Z]{3})_VERS", string, re.M)

    if m and m.group(1) in ["OPM", "OMM", "OEM", "TDM"]:
        type = m.group(1).lower()
    elif m:
        raise CcsdsError(f"Unknown CCSDS type : {m}")
    else:
        raise CcsdsError("Unknown CCSDS type")

    return type, format


def detect2dump(data, **kwargs):
    """Detect the type of the input data and provide the type of ccsds
    file to generate

    Args:
        data (Ephem or List[Ephem] or StateVector or MeasureSet)
    Return:
        str: type of data (e.g. "oem", "opm", "omm", etc.)
    Raise:
        TypeError: for unknown type detected
    """

    if isinstance(data, Ephem) or (
        isinstance(data, Iterable) and all(isinstance(x, Ephem) for x in data)
    ):
        type = "oem"
    elif isinstance(data, StateVector):
        if (
            isinstance(data, Orbit)
            and isinstance(data.propagator, AnalyticalPropagator)
            and data.frame == TEME
            and data.form is TLE
        ):
            type = "omm"
        else:
            type = "opm"
    elif isinstance(data, Iterable) and all(isinstance(x, Measure) for x in data):
        type = "tdm"
    else:
        raise TypeError("Unknown object type")

    return type


def xml2dict(string):
    """Convert and XML string into nested dicts

    The lowest element will be a Field object
    """

    root = ET.fromstring(string)

    data = {}

    def _recurse(elem):
        data = {}
        for subelem in elem:
            if hasattr(subelem, "text") and subelem.text.strip():
                field = Field(subelem.text, subelem.attrib)
                if subelem.tag not in data:
                    data[subelem.tag] = field
                elif not isinstance(data[subelem.tag], list):
                    data[subelem.tag] = [data[subelem.tag], field]
                else:
                    data[subelem.tag].append(field)
            elif subelem.tag in data:
                if not isinstance(data[subelem.tag], list):
                    # We encounter a new child, but a sibling with the same
                    # tag already exists
                    data[subelem.tag] = [data[subelem.tag], _recurse(subelem)]
                else:
                    data[subelem.tag].append(_recurse(subelem))
            else:
                data[subelem.tag] = _recurse(subelem)
        return data

    return _recurse(root)


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

        if "[" in value:
            # There is a unit field
            value, sep, unit = value.partition("[")
            attrib = {"units": unit.rstrip("]")}
        else:
            attrib = {}

        if key.startswith("MAN_"):
            if key == "MAN_EPOCH_IGNITION":
                man = {}
                data.setdefault("maneuvers", []).append(man)
                if i - 1 in comments:
                    man["COMMENT"] = Field(comments[i - 1], {})
            man[key] = Field(value, attrib)
        else:
            data[key] = Field(value, attrib)

    return data


def dump_kvn_header(data, ccsds_type, version="1.0", **kwargs):

    return """CCSDS_{type}_VERS = {version}
CREATION_DATE = {creation_date:{fmt}}
ORIGINATOR = {originator}
""".format(
        type=ccsds_type.upper(),
        creation_date=Date.now(),
        originator=kwargs.get("originator", "N/A"),
        version=version,
        fmt=DATE_FMT_DEFAULT,
    )


def dump_xml_header(data, ccsds_type, version="1.0", **kwargs):

    attrib = {
        "{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation": "http://sanaregistry.org/r/ndmxml/ndmxml-1.0-master.xsd",
        "id": f"CCSDS_{ccsds_type.upper()}_VERS",
        "version": version,
    }

    top = ET.Element(
        ccsds_type.lower(),
        attrib,
        nsmap={"xsi": "http://www.w3.org/2001/XMLSchema-instance"},
    )
    header = ET.SubElement(top, "header")
    creation_date = ET.SubElement(header, "CREATION_DATE")
    creation_date.text = Date.now().strftime(DATE_FMT_DEFAULT)
    originator = ET.SubElement(header, "ORIGINATOR")
    originator.text = kwargs.get("originator", "N/A")

    return top


def dump_kvn_meta_odm(data, meta_tag=True, extras={}, **kwargs):

    center = data.frame.center.name

    if re.search(r"Barycenter|L\d", center):
        center = " ".join(re.findall("[A-Z][^A-Z]*", center))

    meta = """{meta}OBJECT_NAME          = {name}
OBJECT_ID            = {cospar_id}
CENTER_NAME          = {center}
REF_FRAME            = {frame}
TIME_SYSTEM          = {timesystem}
""".format(
        meta="META_START\n" if meta_tag else "",
        name=kwargs.get("name", getattr(data, "name", "N/A")),
        cospar_id=kwargs.get("cospar_id", getattr(data, "cospar_id", "N/A")),
        center=center.upper(),
        frame=data.frame.orientation.name.upper(),
        timesystem=data.date.scale.name
        if isinstance(data, StateVector)
        else data.start.scale.name,
    )

    for k, v in extras.items():
        meta += f"{k:<20} = {v}\n"

    if meta_tag:
        meta += "META_STOP\n"

    meta += "\n"

    return meta


def dump_xml_meta_odm(segment, data, **kwargs):

    metadata = ET.SubElement(segment, "metadata")

    name = ET.SubElement(metadata, "OBJECT_NAME")
    name.text = kwargs.get("name", getattr(data, "name", "N/A"))

    cospar_id = ET.SubElement(metadata, "OBJECT_ID")
    cospar_id.text = kwargs.get("cospar_id", getattr(data, "cospar_id", "N/A"))

    center_txt = data.frame.center.name
    if "Barycenter" in center_txt:
        center_txt = " ".join(re.findall("[A-Z][^A-Z]*", center_txt))

    center = ET.SubElement(metadata, "CENTER_NAME")
    center.text = center_txt.upper()

    frame = ET.SubElement(metadata, "REF_FRAME")
    frame.text = data.frame.orientation.name.upper()

    timescale = ET.SubElement(metadata, "TIME_SYSTEM")
    if isinstance(data, StateVector):
        timescale.text = data.date.scale.name
    else:
        timescale.text = data.start.scale.name

    for key, value in kwargs.get("extras", {}).items():
        x = ET.SubElement(metadata, key)
        x.text = value
