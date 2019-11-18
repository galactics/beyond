import numpy as np

from ...dates import timedelta
from ...orbits import Orbit
from ...orbits.man import ImpulsiveMan, ContinuousMan
from ...utils import units

from .cov import read_cov, dump_cov
from .commons import (
    str2dict,
    parse_date,
    _dump_meta_odm,
    _dump_header,
    decode_unit,
    CcsdsParseError,
)


def read_opm(string):
    """Read of OPM string

    Args:
        string (str): Text containing the OPM
    Return:
        Orbit:
    """

    data = str2dict(string)

    try:
        name = data["OBJECT_NAME"]
        cospar_id = data["OBJECT_ID"]
        scale = data["TIME_SYSTEM"]
        frame = data["REF_FRAME"]
        date = parse_date(data["EPOCH"], scale)
        vx = decode_unit(data, "X_DOT", "km/s")
        vy = decode_unit(data, "Y_DOT", "km/s")
        vz = decode_unit(data, "Z_DOT", "km/s")
        x = decode_unit(data, "X", "km")
        y = decode_unit(data, "Y", "km")
        z = decode_unit(data, "Z", "km")
    except KeyError as e:
        raise CcsdsParseError("Missing mandatory parameter '{}'".format(e))

    orb = Orbit(date, [x, y, z, vx, vy, vz], "cartesian", frame, None)
    orb.name = name
    orb.cospar_id = cospar_id

    for raw_man in data.get("MAN", []):

        man = {}
        man["date"] = parse_date(raw_man["MAN_EPOCH_IGNITION"], scale)
        man["duration"] = timedelta(seconds=decode_unit(raw_man, "MAN_DURATION"))
        man["frame"] = (
            raw_man["MAN_REF_FRAME"] if raw_man["MAN_REF_FRAME"] != frame else None
        )
        man["delta_mass"] = raw_man["MAN_DELTA_MASS"]
        man["comment"] = raw_man.get("comment")

        for i in range(1, 4):
            f_name = "MAN_DV_{}".format(i)
            man.setdefault("dv", []).append(decode_unit(raw_man, f_name))

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
        orb.cov = read_cov(orb, data)

    return orb


def dump_opm(data, **kwargs):

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
        text += dump_cov(cart.cov)

    if cart.maneuvers:
        for i, man in enumerate(cart.maneuvers):
            comment = "\nCOMMENT  {}".format(man.comment) if man.comment else ""

            frame = cart.frame if man.frame is None else man.frame
            if isinstance(man, ContinuousMan):
                date = man.start
                duration = man.duration.total_seconds()
            else:
                date = man.date
                duration = 0

            text += """{comment}
MAN_EPOCH_IGNITION   = {date:%Y-%m-%dT%H:%M:%S.%f}
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
            )

    return header + "\n" + meta + text
