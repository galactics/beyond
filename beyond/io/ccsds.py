"""This module provides ways to handle the CCSDS formats

It is based on the `CCSDS standard <https://public.ccsds.org/Publications/BlueBooks.aspx>`__
"""

import numpy as np
from collections.abc import Iterable

from ..utils import units
from ..dates import Date, timedelta
from ..orbits import Orbit, Ephem
from ..orbits.man import ImpulsiveMan, ContinuousMan
from ..utils.measures import Measure, Range, Doppler, Azimut, Elevation, MeasureSet
from ..errors import ParseError

__all__ = ["load", "loads", "dump", "dumps"]


class CcsdsParseError(ParseError):
    pass


def load(fp):  # pragma: no cover
    """Read CCSDS format from a file descriptor, and provide the beyond class
    corresponding; Orbit or list of Orbit if it's an OPM, Ephem if it's an
    OEM, MeasureSet if it's a TDM.

    Args:
        fp: file descriptor of a CCSDS file
    Return:
        Orbit or Ephem
    Raise:
        CcsdsParseError: when the text is not a recognizable CCSDS format
    """
    return loads(fp.read())


def loads(text):
    """Read CCSDS from a string, and provide the beyond class corresponding;
    Orbit or list of Orbit if it's an OPM, Ephem if it's an OEM, MeasureSet
    if it's a TDM.

    Args:
        text (str):
    Return:
        Orbit or Ephem
    Raise:
        CcsdsParseError: when the text is not a recognizable CCSDS format
    """
    if text.startswith("CCSDS_OEM_VERS"):
        func = _read_oem
    elif text.startswith("CCSDS_OPM_VERS"):
        func = _read_opm
    elif text.startswith("CCSDS_TDM_VERS"):
        func = _read_tdm
    else:
        raise CcsdsParseError("Unknown CCSDS type")
    return func(text)


def dump(data, fp, **kwargs):  # pragma: no cover
    """Write a CCSDS file depending on the type of data, this could be an OPM
    file (Orbit or list of Orbit), an OEM file (Ephem), or a TDM file
    (MeasureSet).

    Args:
        data (Orbit, list of Orbit, Ephem, or MeasureSet)
        fp (file descriptor)
    Keyword Arguments:
        name (str): Name of the object
        cospar_id (str): International designator of the object
        originator (str): Originator of the CCSDS file
    """
    fp.write(dumps(data, **kwargs))


def dumps(data, **kwargs):
    """Create a string CCSDS representation of the object

    Same arguments and behaviour as :py:func:`dump`
    """
    if isinstance(data, Ephem) or (
        isinstance(data, Iterable) and all(isinstance(x, Ephem) for x in data)
    ):
        content = _dump_oem(data, **kwargs)
    elif isinstance(data, Orbit):
        content = _dump_opm(data, **kwargs)
    elif isinstance(data, Iterable) and all(isinstance(x, Measure) for x in data):
        content = _dump_tdm(data, **kwargs)
    else:
        raise TypeError("Unknown object type")

    return content


def _float(name, value):
    """Conversion of state vector field, with automatic unit handling
    """
    if "[" in value:
        # There is a unit field
        value, sep, unit = value.partition("[")
        unit = sep + unit

        # As defined in the CCSDS Orbital Data Message Blue Book, the unit should
        # be the same as defined in table 3-3 which are for km and km/s for position and
        # velocity respectively. Thus, there should be no other conversion to make
        if unit in ("[km]", "[km/s]"):
            multiplier = units.km
        elif unit == "[s]":
            multiplier = 1
        else:
            raise CcsdsParseError(
                "Unknown unit '{}' for the field {}".format(unit, name)
            )
    else:
        # if no unit is provided, the default is km, and km/s
        multiplier = units.km

    return float(value) * multiplier


def _read_oem(string):
    """
    Args:
        string (str): String containing the OEM
    Return:
        Ephem:
    """

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
            date = Date.strptime(
                date, "%Y-%m-%dT%H:%M:%S.%f", scale=ephem["TIME_SYSTEM"]
            )

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


def _read_opm(string):
    """Read of OPM string

    Args:
        string (str): Text containing the OPM
    Return:
        Orbit:
    """

    data = {"MAN": []}
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
                data["MAN"].append(man)
                if i - 1 in comments:
                    man["comment"] = comments[i - 1]
            man[key] = value
        else:
            data[key] = value

    try:
        name = data["OBJECT_NAME"]
        cospar_id = data["OBJECT_ID"]
        scale = data["TIME_SYSTEM"]
        frame = data["REF_FRAME"]
        date = Date.strptime(data["EPOCH"], "%Y-%m-%dT%H:%M:%S.%f", scale=scale)
        vx = _float("X_DOT", data["X_DOT"])
        vy = _float("Y_DOT", data["Y_DOT"])
        vz = _float("Z_DOT", data["Z_DOT"])
        x = _float("X", data["X"])
        y = _float("Y", data["Y"])
        z = _float("Z", data["Z"])
    except KeyError as e:
        raise CcsdsParseError("Missing mandatory parameter")

    orb = Orbit(date, [x, y, z, vx, vy, vz], "cartesian", frame, None)
    orb.name = name
    orb.cospar_id = cospar_id

    for raw_man in data["MAN"]:

        man = {}
        man["date"] = Date.strptime(
            raw_man["MAN_EPOCH_IGNITION"], "%Y-%m-%dT%H:%M:%S.%f", scale=scale
        )
        man["duration"] = timedelta(
            seconds=_float("MAN_DURATION", raw_man["MAN_DURATION"])
        )
        man["frame"] = (
            raw_man["MAN_REF_FRAME"] if raw_man["MAN_REF_FRAME"] != frame else None
        )
        man["delta_mass"] = raw_man["MAN_DELTA_MASS"]
        man["comment"] = raw_man.get("comment")

        for i in range(1, 4):
            f_name = "MAN_DV_{}".format(i)
            man.setdefault("dv", []).append(_float(f_name, raw_man[f_name]))

        if man["duration"].total_seconds() == 0:
            orb.maneuvers.append(
                ImpulsiveMan(
                    man["date"], man["dv"], frame=man["frame"], comment=man["comment"]
                )
            )
        else:
            orb.maneuvers.append(
                ContinuousMan(
                    man["date"],
                    man["duration"],
                    man["dv"],
                    frame=man["frame"],
                    comment=man["comment"],
                    date_pos="start",
                )
            )

    if "CX_X" in data:

        frame = data.get("COV_REF_FRAME", orb.cov.PARENT_FRAME)
        if frame in ("RSW", "RTN"):
            frame = "QSW"

        values = [
            [
                data["CX_X"],
                data["CY_X"],
                data["CZ_X"],
                data["CX_DOT_X"],
                data["CY_DOT_X"],
                data["CZ_DOT_X"],
            ],
            [
                data["CY_X"],
                data["CY_Y"],
                data["CZ_Y"],
                data["CX_DOT_Y"],
                data["CY_DOT_Y"],
                data["CZ_DOT_Y"],
            ],
            [
                data["CZ_X"],
                data["CZ_Y"],
                data["CZ_Z"],
                data["CX_DOT_Z"],
                data["CY_DOT_Z"],
                data["CZ_DOT_Z"],
            ],
            [
                data["CX_DOT_X"],
                data["CX_DOT_Y"],
                data["CX_DOT_Z"],
                data["CX_DOT_X_DOT"],
                data["CY_DOT_X_DOT"],
                data["CZ_DOT_X_DOT"],
            ],
            [
                data["CY_DOT_X"],
                data["CY_DOT_Y"],
                data["CY_DOT_Z"],
                data["CY_DOT_X_DOT"],
                data["CY_DOT_Y_DOT"],
                data["CZ_DOT_Y_DOT"],
            ],
            [
                data["CZ_DOT_X"],
                data["CZ_DOT_Y"],
                data["CZ_DOT_Z"],
                data["CZ_DOT_X_DOT"],
                data["CZ_DOT_Y_DOT"],
                data["CZ_DOT_Z_DOT"],
            ],
        ]

        orb.cov = np.array(values).astype(np.float) * 1e6
        orb.cov._frame = frame

    return orb


def _read_tdm(string):
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
            date = Date.strptime(date.strip(), "%Y-%m-%dT%H:%M:%S.%f", scale=scale)
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


def _dump_meta_odm(data, **kwargs):

    meta = """META_START
OBJECT_NAME          = {name}
OBJECT_ID            = {cospar_id}
CENTER_NAME          = {center}
REF_FRAME            = {frame}
""".format(
        name=kwargs.get("name", getattr(data, "name", "N/A")),
        cospar_id=kwargs.get("cospar_id", getattr(data, "cospar_id", "N/A")),
        center=data.frame.center.name.upper(),
        frame=data.frame.orientation.upper(),
    )

    return meta


def _dump_oem(data, **kwargs):

    if isinstance(data, Ephem):
        data = [data]

    header = _dump_header(data, "OEM", version="2.0", **kwargs)

    content = []
    for i, data in enumerate(data):

        data.form = "cartesian"

        interp = data.method.upper()
        if data.method != data.LINEAR:
            interp += "\nINTERPOLATION_DEGREE = {}".format(data.order - 1)

        meta = _dump_meta_odm(data, **kwargs)
        meta += """TIME_SYSTEM          = {orb.start.scale.name}
START_TIME           = {orb.start:%Y-%m-%dT%H:%M:%S.%f}
STOP_TIME            = {orb.stop:%Y-%m-%dT%H:%M:%S.%f}
INTERPOLATION        = {interp}
META_STOP

""".format(
            creation_date=Date.now(),
            originator=kwargs.get("originator", "N/A"),
            name=kwargs.get("name", "N/A"),
            cospar_id=kwargs.get("cospar_id", "N/A"),
            orb=data,
            interp=interp,
        )

        text = []
        for orb in data:
            text.append(
                "{date:%Y-%m-%dT%H:%M:%S.%f} {orb[0]:{fmt}} {orb[1]:{fmt}} {orb[2]:{fmt}} {orb[3]:{fmt}} {orb[4]:{fmt}} {orb[5]:{fmt}}".format(
                    date=orb.date, orb=orb.base / units.km, fmt=" 10f"
                )
            )

        content.append(meta + "\n".join(text))

    return header + "\n" + "\n\n\n".join(content)


def _dump_opm(data, **kwargs):

    cart = data.copy(form="cartesian")
    kep = data.copy(form="keplerian")

    header = _dump_header(data, "OPM", version="2.0", **kwargs)

    meta = _dump_meta_odm(data, **kwargs)
    meta += """TIME_SYSTEM          = {orb.date.scale.name}
META_STOP

""".format(
        orb=cart
    )

    text = """COMMENT  State Vector
EPOCH                = {cartesian.date:%Y-%m-%dT%H:%M:%S.%f}
X                    = {cartesian.x: 12.6f} [km]
Y                    = {cartesian.y: 12.6f} [km]
Z                    = {cartesian.z: 12.6f} [km]
X_DOT                = {cartesian.vx: 12.6f} [km/s]
Y_DOT                = {cartesian.vy: 12.6f} [km/s]
Z_DOT                = {cartesian.vz: 12.6f} [km/s]

COMMENT  Keplerian elements
SEMI_MAJOR_AXIS      = {kep_a: 12.6f} [km]
ECCENTRICITY         = {kep_e: 12.6f}
INCLINATION          = {angles[0]: 12.6f} [deg]
RA_OF_ASC_NODE       = {angles[1]: 12.6f} [deg]
ARG_OF_PERICENTER    = {angles[2]: 12.6f} [deg]
TRUE_ANOMALY         = {angles[3]: 12.6f} [deg]
""".format(
        cartesian=cart / units.km,
        kep_a=kep.a / units.km,
        kep_e=kep.e,
        angles=np.degrees(kep[2:]),
    )

    # Covariance handling
    if cart.cov.any():
        text += "\nCOMMENT  COVARIANCE\n"
        if cart.cov.frame != cart.cov.PARENT_FRAME:
            frame = cart.cov.frame
            if frame == "QSW":
                frame = "RSW"
            text += "COV_REF_FRAME        = {frame}\n".format(frame=frame)

        l = ["X", "Y", "Z", "X_DOT", "Y_DOT", "Z_DOT"]
        for i, a in enumerate(l):
            for j, b in enumerate(l[: i + 1]):
                txt = "{a}_{b}".format(a=a, b=b)

                text += "C{txt:<19} = {v: 0.16e}\n".format(
                    txt=txt, v=cart.cov[i, j] / 1e6
                )

    if cart.maneuvers:
        for i, man in enumerate(cart.maneuvers):
            comment = (
                man.comment if man.comment is not None else "Maneuver {}".format(i + 1)
            )
            frame = cart.frame if man.frame is None else man.frame
            if isinstance(man, ContinuousMan):
                text += """
COMMENT  {comment}
MAN_EPOCH_IGNITION   = {man.start:%Y-%m-%dT%H:%M:%S.%f}
MAN_DURATION         = {duration:0.3f} [s]
MAN_DELTA_MASS       = 0.000 [kg]
MAN_REF_FRAME        = {frame}
MAN_DV_1             = {dv[0]:.6f} [km/s]
MAN_DV_2             = {dv[1]:.6f} [km/s]
MAN_DV_3             = {dv[2]:.6f} [km/s]
""".format(
                    i=i + 1,
                    man=man,
                    duration=man.duration.total_seconds(),
                    dv=man._dv / units.km,
                    frame=frame,
                    comment=comment,
                )
            else:
                text += """
COMMENT  {comment}
MAN_EPOCH_IGNITION   = {man.date:%Y-%m-%dT%H:%M:%S.%f}
MAN_DURATION         = 0.000 [s]
MAN_DELTA_MASS       = 0.000 [kg]
MAN_REF_FRAME        = {frame}
MAN_DV_1             = {dv[0]:.6f} [km/s]
MAN_DV_2             = {dv[1]:.6f} [km/s]
MAN_DV_3             = {dv[2]:.6f} [km/s]
""".format(
                    i=i + 1,
                    man=man,
                    dv=man._dv / units.km,
                    frame=frame,
                    comment=comment,
                )

    return header + "\n" + meta + text


def _dump_tdm(data, **kwargs):

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
