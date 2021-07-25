import numpy as np
import lxml.etree as ET

from ...constants import c
from ...utils import units
from ...utils.measures import MeasureSet, Range, Azimut, Elevation, Doppler

from .commons import (
    CcsdsError,
    parse_date,
    dump_kvn_header,
    dump_xml_header,
    DATE_FMT_DEFAULT,
    xml2dict,
    get_format,
)


def loads(string, fmt="kvn"):
    """Read CCSDS TDM format and convert it to a MeasureSet"""

    if fmt == "kvn":
        measures = _loads_kvn(string)
    else:
        measures = _loads_xml(string)

    return measures


def dumps(data, **kwargs):

    fmt = get_format(**kwargs)

    if fmt == "kvn":
        string = _dumps_kvn(data, **kwargs)
    elif fmt == "xml":
        string = _dumps_xml(data, **kwargs)
    else:  # pragma: no cover
        raise CcsdsError(f"Unknown format : {fmt}")

    return string


def _loads_kvn(string):

    mode = "meta"
    meta = {}
    sets = []
    for i, line in enumerate(string.splitlines()):

        if not line or line.startswith("COMMENT"):
            continue
        elif line.startswith("DATA_START"):
            participants = [
                v for k, v in sorted(meta.items()) if k.startswith("PARTICIPANT_")
            ]
            path_txt = meta["PATH"]
            path = [participants[int(p) - 1] for p in path_txt.split(",")]
            scale = meta["TIME_SYSTEM"]
            mode = "data"
            r_unit = units.km
            if meta.get("RANGE_UNITS") == "s":
                r_unit *= c
            data = MeasureSet()
            sets.append(data)
            continue
        elif line.startswith("DATA_STOP"):
            mode = "meta"
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        if mode == "meta":
            meta[key] = value
        elif mode == "data":
            date, value = value.split()
            date = parse_date(date.strip(), scale)
            value = float(value)

            if key == "RANGE":
                obj = Range(path, date, value * r_unit)
            elif key == "ANGLE_1" and meta["ANGLE_TYPE"] == "AZEL":
                obj = Azimut(path, date, np.radians(-value))
            elif key == "ANGLE_2" and meta["ANGLE_TYPE"] == "AZEL":
                obj = Elevation(path, date, np.radians(value))
            else:
                raise CcsdsError(f"Unknown type : {key}")

            data.append(obj)

    if len(sets) == 1:
        sets = sets.pop()

    return sets


def _loads_xml(string):

    data = xml2dict(string.encode())

    sets = []
    segments = data["body"]["segment"]

    if isinstance(segments, dict):
        segments = [segments]

    for segment in segments:
        meta = segment["metadata"]
        measures = MeasureSet()
        sets.append(measures)

        participants = [
            v.text
            for k, v in sorted(segment["metadata"].items())
            if k.startswith("PARTICIPANT_")
        ]
        path_txt = meta["PATH"].text
        path = [participants[int(p) - 1] for p in path_txt.split(",")]
        scale = meta["TIME_SYSTEM"].text

        if "RANGE_UNITS" in meta:
            r_unit = units.km
            if meta["RANGE_UNITS"].text == "s":
                r_unit *= c
        if "ANGLE_TYPE" in meta:
            angle_type = meta["ANGLE_TYPE"].text

        for obs in segment["data"]["observation"]:
            date = parse_date(obs.pop("EPOCH").text, scale)
            meas_type, value = list(obs.items())[0]
            value = float(value.text)
            if meas_type == "RANGE":
                measures.append(Range(path, date, value * r_unit))
            elif meas_type == "ANGLE_1" and angle_type == "AZEL":
                measures.append(Azimut(path, date, np.radians(-value)))
            elif meas_type == "ANGLE_2" and angle_type == "AZEL":
                measures.append(Elevation(path, date, np.radians(value)))
            else:
                raise CcsdsError(f"Unknown type : {meas_type}")

    if len(sets) == 1:
        sets = sets.pop()

    return sets


def _dumps_kvn(data, **kwargs):

    filtered = ((path, data.filter(path=path)) for path in data.paths)

    header = dump_kvn_header(data, "TDM", **kwargs)

    text = ""
    for path, measure_set in filtered:

        meta = {
            "TIME_SYSTEM": measure_set.start.scale.name,
            "START_TIME": measure_set.start.strftime(DATE_FMT_DEFAULT),
            "STOP_TIME": measure_set.stop.strftime(DATE_FMT_DEFAULT),
        }

        i = 0
        parts = {}
        for p in path:
            if p in parts:
                continue
            else:
                i += 1
            parts[p] = i
            meta[f"PARTICIPANT_{i}"] = p

        meta["MODE"] = "SEQUENTIAL"
        meta["PATH"] = ",".join([str(parts[p]) for p in path])

        if "Range" in measure_set.types:
            meta["RANGE_UNITS"] = "km"
        if "Azimut" in measure_set.types:
            meta["ANGLE_TYPE"] = "AZEL"

        txt = ["META_START"]

        for k, v in meta.items():
            txt.append(f"{k:20} = {v}")

        txt.append("META_STOP")
        txt.append("")
        txt.append("DATA_START")

        for m in measure_set:

            if isinstance(m, Doppler):
                name = "DOPPLER_INSTANTANEOUS"
                value_fmt = "16.6f"
                value = m.value
            elif isinstance(m, Range):
                name = "RANGE"
                value_fmt = "16.6f"
                value = m.value / units.km
            elif isinstance(m, Azimut):
                name = "ANGLE_1"
                value_fmt = "12.2f"
                value = -np.degrees(m.value) % 360
            elif isinstance(m, Elevation):
                name = "ANGLE_2"
                value_fmt = "12.2f"
                value = np.degrees(m.value)

            txt.append(
                "{name:20} = {date:{DATE_FMT_DEFAULT}} {value:{value_fmt}}".format(
                    name=name,
                    date=m.date,
                    DATE_FMT_DEFAULT=DATE_FMT_DEFAULT,
                    value=value,
                    value_fmt=value_fmt,
                )
            )

        txt.append("DATA_STOP")
        txt.append("")

        text += "\n".join(txt)

    return header + "\n" + text


def _dumps_xml(data, **kwargs):
    filtered = ((path, data.filter(path=path)) for path in data.paths)

    top = dump_xml_header(data, "TDM", version="1.0", **kwargs)

    body = ET.SubElement(top, "body")

    for path, measure_set in filtered:
        segment = ET.SubElement(body, "segment")
        meta = ET.SubElement(segment, "metadata")
        ts = ET.SubElement(meta, "TIME_SYSTEM")
        ts.text = measure_set.start.scale.name

        start = ET.SubElement(meta, "START_TIME")
        start.text = measure_set.start.strftime(DATE_FMT_DEFAULT)

        stop = ET.SubElement(meta, "STOP_TIME")
        stop.text = measure_set.stop.strftime(DATE_FMT_DEFAULT)

        i = 0
        parts = {}
        for p in path:
            if p in parts:
                continue
            else:
                i += 1
            parts[p] = i
            participant = ET.SubElement(meta, f"PARTICIPANT_{i}")
            participant.text = p

        mode = ET.SubElement(meta, "MODE")
        mode.text = "SEQUENTIAL"

        path_tag = ET.SubElement(meta, "PATH")
        path_tag.text = ",".join([str(parts[p]) for p in path])

        if "Range" in measure_set.types:
            r_unit = ET.SubElement(meta, "RANGE_UNITS")
            r_unit.text = "km"
        if "Azimut" in measure_set.types:
            angle_type = ET.SubElement(meta, "ANGLE_TYPE")
            angle_type.text = "AZEL"

        data_tag = ET.SubElement(segment, "data")

        for m in measure_set:
            obs = ET.SubElement(data_tag, "observation")

            epoch = ET.SubElement(obs, "EPOCH")
            epoch.text = m.date.strftime(DATE_FMT_DEFAULT)

            if isinstance(m, Doppler):
                name = "DOPPLER_INSTANTANEOUS"
                value_fmt = ".6f"
                value = m.value
            elif isinstance(m, Range):
                name = "RANGE"
                value_fmt = ".6f"
                value = m.value / units.km
            elif isinstance(m, Azimut):
                name = "ANGLE_1"
                value_fmt = ".2f"
                value = -np.degrees(m.value) % 360
            elif isinstance(m, Elevation):
                name = "ANGLE_2"
                value_fmt = ".2f"
                value = np.degrees(m.value)

            field = ET.SubElement(obs, name)
            field.text = "{:{}}".format(value, value_fmt)

    return ET.tostring(
        top, pretty_print=True, xml_declaration=True, encoding="UTF-8"
    ).decode()
