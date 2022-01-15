import numpy as np
import lxml.etree as ET

from ...dates import timedelta
from ...orbits import StateVector
from ...orbits.man import ImpulsiveMan, ContinuousMan
from ...utils import units
from ...frames.orient import G50, EME2000, GCRF, MOD, TEME, TOD, CIRF

from .cov import load_cov, dump_cov
from .commons import (
    parse_date,
    dump_kvn_meta_odm,
    dump_kvn_header,
    dump_xml_header,
    dump_xml_meta_odm,
    decode_unit,
    CcsdsError,
    DATE_FMT_DEFAULT,
    kvn2dict,
    xml2dict,
    get_format,
)


def loads(string, fmt):
    """Read of OPM string

    Args:
        string (str): Text containing the OPM in KVN or XML format
        fmt (str): format of the file to read
    Return:
        StateVector:
    """

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
        return _dumps_kvn(data, **kwargs)
    elif fmt == "xml":
        return _dumps_xml(data, **kwargs)
    else:  # pragma: no cover
        raise CcsdsError(f"Unknown format '{fmt}'")


def _loads_kvn(string):

    data = kvn2dict(string)

    try:
        name = data["OBJECT_NAME"].text
        cospar_id = data["OBJECT_ID"].text
        scale = data["TIME_SYSTEM"].text
        frame = data["REF_FRAME"].text
        center = data["CENTER_NAME"].text

        # Convert the frame and center into a beyond frame name
        # compatible with beyond.env.jpl
        if center.lower() != "earth":
            frame = center.title().replace(" ", "")

        date = parse_date(data["EPOCH"].text, scale)
        vx = decode_unit(data, "X_DOT", "km/s")
        vy = decode_unit(data, "Y_DOT", "km/s")
        vz = decode_unit(data, "Z_DOT", "km/s")
        x = decode_unit(data, "X", "km")
        y = decode_unit(data, "Y", "km")
        z = decode_unit(data, "Z", "km")
    except KeyError as e:
        raise CcsdsError(f"Missing mandatory parameter {e}")

    orb = StateVector(
        [x, y, z, vx, vy, vz], date, "cartesian", frame, name=name, cospar_id=cospar_id
    )

    for raw_man in data.get("maneuvers", []):
        man = {}
        man["date"] = parse_date(raw_man["MAN_EPOCH_IGNITION"].text, scale)
        man["duration"] = timedelta(seconds=decode_unit(raw_man, "MAN_DURATION", "s"))
        man["frame"] = (
            raw_man["MAN_REF_FRAME"].text
            if raw_man["MAN_REF_FRAME"].text != frame
            else None
        )
        man["delta_mass"] = raw_man["MAN_DELTA_MASS"].text
        man["comment"] = raw_man["COMMENT"].text if "COMMENT" in raw_man else None

        for i in range(1, 4):
            f_name = f"MAN_DV_{i}"
            man.setdefault("dv", []).append(decode_unit(raw_man, f_name, "km/s"))

        if man["duration"].total_seconds() == 0:
            orb.maneuvers.append(
                ImpulsiveMan(
                    man["date"],
                    man["dv"],
                    frame=man["frame"],
                    comment=man["comment"],
                )
            )
        else:
            orb.maneuvers.append(
                ContinuousMan(
                    man["date"],
                    man["duration"],
                    dv=man["dv"],
                    frame=man["frame"],
                    comment=man["comment"],
                    date_pos="start",
                )
            )

    if "CX_X" in data:
        orb.cov = load_cov(orb, data)

    for k in data.keys():
        if k.startswith("USER_DEFINED"):
            ud = orb._data.setdefault("ccsds_user_defined", {})
            ud[k[13:]] = data[k].text

    return orb


def _loads_xml(string):

    data = xml2dict(string.encode())

    metadata = data["body"]["segment"]["metadata"]
    statevector = data["body"]["segment"]["data"]["stateVector"]
    maneuvers = data["body"]["segment"]["data"].get("maneuverParameters")
    if isinstance(maneuvers, dict):
        maneuvers = [maneuvers]
    cov = data["body"]["segment"]["data"].get("covarianceMatrix")

    try:
        name = metadata["OBJECT_NAME"].text
        cospar_id = metadata["OBJECT_ID"].text
        scale = metadata["TIME_SYSTEM"].text
        frame = metadata["REF_FRAME"].text
        center = metadata["CENTER_NAME"].text

        # Convert the frame and center into a beyond frame name
        # compatible with beyond.env.jpl
        if center.lower() != "earth":
            frame = center.title().replace(" ", "")

        date = parse_date(statevector["EPOCH"].text, scale)
        vx = decode_unit(statevector, "X_DOT", "km/s")
        vy = decode_unit(statevector, "Y_DOT", "km/s")
        vz = decode_unit(statevector, "Z_DOT", "km/s")
        x = decode_unit(statevector, "X", "km")
        y = decode_unit(statevector, "Y", "km")
        z = decode_unit(statevector, "Z", "km")
    except KeyError as e:
        raise CcsdsError(f"Missing mandatory parameter {e}")

    orb = StateVector(
        [x, y, z, vx, vy, vz], date, "cartesian", frame, name=name, cospar_id=cospar_id
    )

    if maneuvers:
        for raw_man in maneuvers:
            man = {}
            man["date"] = parse_date(raw_man["MAN_EPOCH_IGNITION"].text, scale)
            man["duration"] = timedelta(
                seconds=decode_unit(raw_man, "MAN_DURATION", "s")
            )
            man["frame"] = (
                raw_man["MAN_REF_FRAME"].text
                if raw_man["MAN_REF_FRAME"].text != frame
                else None
            )
            man["delta_mass"] = raw_man["MAN_DELTA_MASS"].text
            man["comment"] = raw_man["COMMENT"].text if "COMMENT" in raw_man else None

            for i in range(1, 4):
                f_name = f"MAN_DV_{i}"
                man.setdefault("dv", []).append(decode_unit(raw_man, f_name, "km/s"))

            if man["duration"].total_seconds() == 0:
                orb.maneuvers.append(
                    ImpulsiveMan(
                        man["date"],
                        man["dv"],
                        frame=man["frame"],
                        comment=man["comment"],
                    )
                )
            else:
                orb.maneuvers.append(
                    ContinuousMan(
                        man["date"],
                        man["duration"],
                        dv=man["dv"],
                        frame=man["frame"],
                        comment=man["comment"],
                        date_pos="start",
                    )
                )

    if cov:
        orb.cov = load_cov(orb, cov)

    ud_dict = data["body"]["segment"]["data"].get("userDefinedParameters", {})

    for field in ud_dict.get("USER_DEFINED", []):
        ud = orb._data.setdefault("ccsds_user_defined", {})
        ud[field.attrib["parameter"]] = field.text

    return orb


def _dumps_kvn(data, *, kep=True, **kwargs):
    cart = data.copy(form="cartesian")

    header = dump_kvn_header(data, "OPM", version="2.0", **kwargs)

    meta = dump_kvn_meta_odm(data, **kwargs)

    text = """COMMENT  State Vector
EPOCH                = {cartesian.date:{dfmt}}
X                    = {cartesian.x: 12.6f} [km]
Y                    = {cartesian.y: 12.6f} [km]
Z                    = {cartesian.z: 12.6f} [km]
X_DOT                = {cartesian.vx: 12.6f} [km/s]
Y_DOT                = {cartesian.vy: 12.6f} [km/s]
Z_DOT                = {cartesian.vz: 12.6f} [km/s]
""".format(
        cartesian=cart / units.km,
        dfmt=DATE_FMT_DEFAULT,
    )

    if kep and cart.frame.orientation in (G50, EME2000, GCRF, MOD, TOD, TEME, CIRF):
        kep = data.copy(form="keplerian")
        text += """
COMMENT  Keplerian elements
SEMI_MAJOR_AXIS      = {kep_a: 12.6f} [km]
ECCENTRICITY         = {kep_e: 12.6f}
INCLINATION          = {angles[0]: 12.6f} [deg]
RA_OF_ASC_NODE       = {angles[1]: 12.6f} [deg]
ARG_OF_PERICENTER    = {angles[2]: 12.6f} [deg]
TRUE_ANOMALY         = {angles[3]: 12.6f} [deg]
GM                   = {gm:11.4f} [km**3/s**2]
""".format(
            kep_a=kep.a / units.km,
            kep_e=kep.e,
            angles=np.degrees(kep[2:]),
            gm=kep.frame.center.body.mu / (units.km ** 3),
        )

    # Covariance handling
    if cart.cov is not None:
        text += dump_cov(cart.cov)

    if cart.maneuvers:
        for i, man in enumerate(cart.maneuvers):
            comment = f"\nCOMMENT  {man.comment}" if man.comment else ""

            if man.frame is None:
                frame = cart.frame
            elif man.frame == "QSW":
                frame = "RSW"
            else:
                frame = man.frame

            if isinstance(man, ContinuousMan):
                date = man.start
                duration = man.duration.total_seconds()
            else:
                date = man.date
                duration = 0

            text += """{comment}
MAN_EPOCH_IGNITION   = {date:{dfmt}}
MAN_DURATION         = {duration:0.3f} [s]
MAN_DELTA_MASS       = 0.000 [kg]
MAN_REF_FRAME        = {frame}
MAN_DV_1             = {dv[0]:.6f} [km/s]
MAN_DV_2             = {dv[1]:.6f} [km/s]
MAN_DV_3             = {dv[2]:.6f} [km/s]
""".format(
                i=i + 1,
                date=date,
                duration=duration,
                man=man,
                dv=man._dv / units.km,
                frame=frame,
                comment=comment,
                dfmt=DATE_FMT_DEFAULT,
            )

    if "ccsds_user_defined" in data._data:
        text += "\n"
        for k, v in data._data["ccsds_user_defined"].items():
            text += f"USER_DEFINED_{k} = {v}\n"

    return header + "\n" + meta + text


def _dumps_xml(data, *, kep=True, **kwargs):

    cart = data.copy(form="cartesian")

    # Write an intermediary, with field name, unit and value
    # like a dict of tuple
    # {
    #     "X": (cartesian.x / units.km, units.km)
    # }

    top = dump_xml_header(data, "OPM", version="2.0", **kwargs)

    body = ET.SubElement(top, "body")
    segment = ET.SubElement(body, "segment")

    dump_xml_meta_odm(segment, data, **kwargs)

    data_tag = ET.SubElement(segment, "data")

    statevector = ET.SubElement(data_tag, "stateVector")
    epoch = ET.SubElement(statevector, "EPOCH")
    epoch.text = data.date.strftime(DATE_FMT_DEFAULT)

    elems = {
        "X": "x",
        "Y": "y",
        "Z": "z",
        "X_DOT": "vx",
        "Y_DOT": "vy",
        "Z_DOT": "vz",
    }

    for k, v in elems.items():
        x = ET.SubElement(statevector, k, units="km" if "DOT" not in k else "km/s")
        x.text = f"{getattr(cart, v) / units.km:0.6f}"

    if kep and cart.frame.orientation in (G50, EME2000, GCRF, MOD, TOD, TEME, CIRF):
        kep = data.copy(form="keplerian")
        keplerian = ET.SubElement(data_tag, "keplerianElements")

        sma = ET.SubElement(keplerian, "SEMI_MAJOR_AXIS", units="km")
        sma.text = f"{kep.a / units.km:0.6}"
        ecc = ET.SubElement(keplerian, "ECCENTRICITY")
        ecc.text = f"{kep.e:0.6}"

        elems = {
            "INCLINATION": "i",
            "RA_OF_ASC_NODE": "Omega",
            "ARG_OF_PERICENTER": "omega",
            "TRUE_ANOMALY": "nu",
        }

        for k, v in elems.items():
            x = ET.SubElement(keplerian, k, units="deg")
            x.text = f"{np.degrees(getattr(kep, v)):0.6}"

        gm = ET.SubElement(keplerian, "GM", units="km**3/s**2")
        gm.text = f"{kep.frame.center.body.mu / units.km ** 3:11.4f}"

    if cart.cov is not None:
        cov = ET.SubElement(data_tag, "covarianceMatrix")

        if cart.cov.frame != cart.frame:
            frame = cart.cov.frame
            if frame == "QSW":
                frame = "RSW"

            cov_frame = ET.SubElement(cov, "COV_REF_FRAME")
            cov_frame.text = f"{frame}"

        elems = ["X", "Y", "Z", "X_DOT", "Y_DOT", "Z_DOT"]
        for i, a in enumerate(elems):
            for j, b in enumerate(elems[: i + 1]):
                x = ET.SubElement(cov, f"C{a}_{b}")
                x.text = f"{cart.cov[i, j] / 1000000.0:0.12e}"

    if cart.maneuvers:
        for man in cart.maneuvers:
            mans = ET.SubElement(data_tag, "maneuverParameters")
            if man.comment:
                com = ET.SubElement(mans, "COMMENT")
                com.text = man.comment

            if man.frame is None:
                frame = cart.frame
            elif man.frame == "QSW":
                frame = "RSW"
            else:
                frame = man.frame

            if isinstance(man, ContinuousMan):
                date = man.start
                duration = man.duration.total_seconds()
            else:
                date = man.date
                duration = 0

            man_epoch = ET.SubElement(mans, "MAN_EPOCH_IGNITION")
            man_epoch.text = date.strftime(DATE_FMT_DEFAULT)
            man_dur = ET.SubElement(mans, "MAN_DURATION", units="s")
            man_dur.text = f"{duration:0.3f}"

            man_mass = ET.SubElement(mans, "MAN_DELTA_MASS", units="kg")
            man_mass.text = "-0.001"

            man_frame = ET.SubElement(mans, "MAN_REF_FRAME")
            man_frame.text = f"{frame}"

            for i in range(3):
                x = ET.SubElement(mans, f"MAN_DV_{i + 1}", units="km/s")
                x.text = f"{man._dv[i] / units.km:.6f}"

    if "ccsds_user_defined" in data._data:
        ud = ET.SubElement(data_tag, "userDefinedParameters")
        for k, v in data._data["ccsds_user_defined"].items():
            el = ET.SubElement(ud, "USER_DEFINED", parameter=k)
            el.text = v

    return ET.tostring(
        top, pretty_print=True, xml_declaration=True, encoding="UTF-8"
    ).decode()
