import numpy as np

from ...constants import c
from ...utils import units
from ...utils.measures import MeasureSet, Range, Azimut, Elevation, Doppler

from .commons import CcsdsParseError, parse_date, _dump_header


def read_tdm(string):
    """Read CCSDS TDM format and convert it to a MeasureSet
    """

    mode = "meta"
    meta = {}
    data = MeasureSet()
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
                if meta["RANGE_UNITS"] == "km":
                    obj = Range(path, date, value * units.km)
                elif meta["RANGE_UNITS"] == "s":
                    obj = Range(path, date, value * c * units.km)
            elif key == "ANGLE_1":
                if meta["ANGLE_TYPE"] == "AZEL":
                    obj = Azimut(path, date, np.radians(-value))
                else:
                    raise CcsdsParseError("Unknown angle type")
            elif key == "ANGLE_2":
                if meta["ANGLE_TYPE"] == "AZEL":
                    obj = Elevation(path, date, np.radians(value))
                else:
                    raise CcsdsParseError("Unknown angle type")

            data.append(obj)

    return data


def dump_tdm(data, **kwargs):

    header = _dump_header(data, "TDM", **kwargs)
    date_fmt = "%Y-%m-%dT%H:%M:%S.%f"

    filtered = ((path, data.filter(path=path)) for path in data.paths)

    text = ""
    for path, measure_set in filtered:

        meta = {
            "TIME_SYSTEM": measure_set.start.scale.name,
            "START_TIME": measure_set.start.strftime(date_fmt),
            "STOP_TIME": measure_set.stop.strftime(date_fmt),
        }

        i = 0
        parts = {}
        for p in path:
            if p in parts:
                continue
            else:
                i += 1
            parts[p] = i
            meta["PARTICIPANT_{}".format(i)] = p

        meta["MODE"] = "SEQUENTIAL"
        meta["PATH"] = ",".join([str(parts[p]) for p in path])

        if "Range" in measure_set.types:
            meta["RANGE_UNITS"] = "km"
        if "Azimut" in measure_set.types:
            meta["ANGLE_TYPE"] = "AZEL"

        txt = ["META_START"]

        for k, v in meta.items():
            txt.append("{:20} = {}".format(k, v))

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
                "{name:20} = {date:{date_fmt}} {value:{value_fmt}}".format(
                    name=name,
                    date=m.date,
                    date_fmt=date_fmt,
                    value=value,
                    value_fmt=value_fmt,
                )
            )

        txt.append("DATA_STOP")
        txt.append("")

        text += "\n".join(txt)

    return header + "\n" + text
