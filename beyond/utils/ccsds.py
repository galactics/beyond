"""This module provides ways to handle the CCSDS Orbit Data Message formats

It is based ond the CCSDS ODM Blue Book from Nov. 2009 (502.0-B-2)
"""

import numpy as np
from collections.abc import Iterable

from ..dates import Date, timedelta
from ..orbits import Orbit, Ephem
from ..orbits.man import Maneuver

__all__ = ['load', 'loads', 'dump', "dumps"]


def load(fp):  # pragma: no cover
    """Read a file
    """
    return loads(fp.read())


def loads(text):
    """
    Args:
        text (str):
    Return:
        Orbit or Ephem
    Raise:
        ValueError: when the text is not a recognizable CCSDS format
    """
    if text.startswith("CCSDS_OEM_VERS"):
        content = _read_oem(text)
    elif text.startswith("CCSDS_OPM_VERS"):
        content = _read_opm(text)
    else:
        raise ValueError("Unknown CCSDS type")
    return content


def dump(data, fp, **kwargs):  # pragma: no cover
    """Write a file
    """
    fp.write(dumps(data, **kwargs))


def dumps(data, **kwargs):
    """Create a string CCSDS representation of the object
    """
    if isinstance(data, Ephem) or (isinstance(data, Iterable) and all(isinstance(x, Ephem) for x in data)):
        content = _dump_oem(data, **kwargs)
    elif isinstance(data, Orbit):
        content = _dump_opm(data, **kwargs)
    else:
        raise TypeError("Unknown object type")

    return content


def _float(line):
    """Conversion of state vector field, with automatic unit handling
    """
    field = line.partition('=')[-1].strip()
    if "[" in field:
        # There is a unit field
        value, sep, unit = field.partition("[")
        unit = sep + unit

        # As defined in the CCSDS Orbital Data Message Blue Book, the unit should
        # be the same as defined in table 3-3 which are for km and km/s for position and
        # velocity respectively. Thus, there should be no other conversion to make
        if unit in ("[km]", "[km/s]"):
            multiplier = 1000
        elif unit == "[s]":
            multiplier = 1
        else:
            raise ValueError("Unknown unit for this field", unit)
    else:
        value = field
        # if no unit is provided, the default is km, and km/s
        multiplier = 1000

    return float(value) * multiplier


def _read_oem(string):
    """
    Args:
        string (str): String containing the OEM
    Return:
        Ephem:
    """

    ephem_dicts = []
    data_block = False

    for line in string.splitlines():

        if not line or line.startswith("COMMENT"):  # pragma: no cover
            continue

        elif line.startswith("META_START"):
            orbits = []
            ephem = {
                'orbits': orbits,
                'name': None,
                'cospar_id': None,
                'method': None,
                'order': None,
                'frame': None,
                'center': None,
                'scale': None
            }
            ephem_dicts.append(ephem)
            data_block = False

        elif line.startswith("OBJECT_NAME"):
            ephem['name'] = line.partition("=")[-1].strip()

        elif line.startswith("OBJECT_ID"):
            ephem['cospar_id'] = line.partition("=")[-1].strip()

        elif line.startswith("TIME_SYSTEM"):
            ephem['scale'] = line.partition("=")[-1].strip()

        elif line.startswith("REF_FRAME"):
            ephem['frame'] = line.partition('=')[-1].strip()

        elif line.startswith("CENTER_NAME"):
            ephem['center'] = line.partition('=')[-1].strip()

        elif line.startswith('INTERPOLATION_DEGREE'):
            ephem['order'] = int(line.partition("=")[-1].strip()) + 1

        elif line.startswith('INTERPOLATION'):
            ephem['method'] = line.partition("=")[-1].strip().lower()

        elif line.startswith('META_STOP'):
            if None in (ephem['frame'], ephem['center'], ephem['scale']):
                raise ValueError("Missing field")

            data_block = True

            if ephem['center'].lower() != "earth":
                ephem['frame'] = ephem['center'].title().replace(" ", "")

            continue

        if not data_block:
            continue

        # From now on, each non-empty line is a state vector
        date, *state_vector = line.split()
        date = Date.strptime(date, "%Y-%m-%dT%H:%M:%S.%f", scale=ephem['scale'])

        # Conversion from km to m and from km/s to m/s
        state_vector = np.array([float(x) for x in state_vector]) * 1000

        ephem['orbits'].append(Orbit(date, state_vector, 'cartesian', ephem['frame'], None))

    ephems = []
    for ephem_dict in ephem_dicts:
        if not ephem_dict['orbits']:
            raise ValueError("Empty ephemeris")
        ephem = Ephem(ephem_dict['orbits'], method=ephem_dict['method'], order=ephem_dict['order'])

        ephem.name = ephem_dict['name']
        ephem.cospar_id = ephem_dict['cospar_id']
        ephems.append(ephem)

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

    name, cospar_id, scale, frame, date, x, y, z, vx, vy, vz = [None] * 11

    maneuvers = []

    for line in string.splitlines():
        if not line or line.startswith("COMMENT"):
            continue
        elif line.startswith("OBJECT_NAME"):
            name = line.partition("=")[-1].strip()
        elif line.startswith("OBJECT_ID"):
            cospar_id = line.partition("=")[-1].strip()
        elif line.startswith("TIME_SYSTEM"):
            scale = line.partition("=")[-1].strip()
        elif line.startswith("REF_FRAME"):
            frame = line.partition('=')[-1].strip()
        elif line.startswith("EPOCH"):
            date = line.partition("=")[-1].strip()
            date = Date.strptime(date, "%Y-%m-%dT%H:%M:%S.%f", scale=scale)
        elif line.startswith("X_DOT"):
            vx = _float(line)
        elif line.startswith("Y_DOT"):
            vy = _float(line)
        elif line.startswith("Z_DOT"):
            vz = _float(line)
        elif line.startswith("X"):
            x = _float(line)
        elif line.startswith("Y"):
            y = _float(line)
        elif line.startswith("Z"):
            z = _float(line)
        elif line.startswith("MAN_EPOCH_IGNITION"):
            man = {}
            maneuvers.append(man)
            man_date = line.partition("=")[-1].strip()
            man['date'] = Date.strptime(man_date, "%Y-%m-%dT%H:%M:%S.%f", scale=scale)
        elif line.startswith("MAN_DURATION"):
            man['duration'] = timedelta(seconds=_float(line))
        elif line.startswith("MAN_REF_FRAME"):
            man['frame'] = line.partition('=')[-1].strip()
        elif line.startswith("MAN_DV_"):
            man.setdefault('dv', []).append(_float(line))

    if None in [scale, frame, x, y, z, vx, vy, vz] or not isinstance(date, Date):
        raise ValueError("Missing mandatory parameter")

    orb = Orbit(date, [x, y, z, vx, vy, vz], 'cartesian', frame, None)

    for man in maneuvers:
        if man['duration'].total_seconds() == 0:
            orb.maneuvers.append(Maneuver(man['date'], man['dv'], frame=man['frame']))

    orb.name = name
    orb.cospar_id = cospar_id

    return orb


def _dump_header(data, ccsds_type, version="1.0", **kwargs):

    return """CCSDS_{type}_VERS = {version}
CREATION_DATE = {creation_date:%Y-%m-%dT%H:%M:%S}
ORIGINATOR = {originator}

"""     .format(
        type=ccsds_type.upper(),
        creation_date=Date.now(),
        originator=kwargs.get("originator", "N/A"),
        version=version
    )


def _dump_meta(data, **kwargs):

    meta = """META_START
OBJECT_NAME          = {name}
OBJECT_ID            = {cospar_id}
CENTER_NAME          = {center}
REF_FRAME            = {frame}
"""     .format(
        name=kwargs.get("name", getattr(data, "name", "N/A")),
        cospar_id=kwargs.get("cospar_id", getattr(data, "cospar_id", "N/A")),
        center=data.frame.center.name.upper(),
        frame=data.frame.orientation.upper()
    )

    return meta


def _dump_oem(data, **kwargs):

    if isinstance(data, Ephem):
        data = [data]

    content = []
    for i, data in enumerate(data):

        data.form = 'cartesian'

        interp = data.method.upper()
        if data.method != data.LINEAR:
            interp += "\nINTERPOLATION_DEGREE = {}".format(data.order - 1)

        header = _dump_header(data, "OEM", version="2.0", **kwargs) if i == 0 else ""

        meta = _dump_meta(data, **kwargs)
        meta += """TIME_SYSTEM          = {orb.start.scale.name}
START_TIME           = {orb.start:%Y-%m-%dT%H:%M:%S.%f}
STOP_TIME            = {orb.stop:%Y-%m-%dT%H:%M:%S.%f}
INTERPOLATION        = {interp}
META_STOP

"""     .format(
            creation_date=Date.now(),
            originator=kwargs.get("originator", "N/A"),
            name=kwargs.get("name", "N/A"),
            cospar_id=kwargs.get("cospar_id", "N/A"),
            orb=data,
            interp=interp
        )

        text = []
        for orb in data:
            text.append("{date:%Y-%m-%dT%H:%M:%S.%f} {orb[0]:{fmt}} {orb[1]:{fmt}} {orb[2]:{fmt}} {orb[3]:{fmt}} {orb[4]:{fmt}} {orb[5]:{fmt}}".format(
                date=orb.date,
                orb=orb.base / 1000,
                fmt=" 10f"
            ))

        content.append(header + meta + "\n".join(text))

    return "\n\n".join(content)


def _dump_opm(data, **kwargs):

    cart = data.copy(form="cartesian")
    kep = data.copy(form="keplerian")

    header = _dump_header(data, "OPM", version="2.0", **kwargs)

    meta = _dump_meta(data, **kwargs)
    meta += """TIME_SYSTEM          = {orb.date.scale.name}
META_STOP

"""     .format(orb=cart)

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
""".format(cartesian=cart / 1000, kep_a=kep.a / 1000, kep_e=kep.e, angles=np.degrees(kep[2:]))

    if cart.maneuvers:
        for i, man in enumerate(cart.maneuvers):
            text += """
COMMENT  Maneuver {i}
MAN_EPOCH_IGNITION   = {man.date:%Y-%m-%dT%H:%M:%S.%f}
MAN_DURATION         = 0.000 [s]
MAN_DELTA_MASS       = 0.000 [kg]
MAN_REF_FRAME        = {man.frame}
MAN_DV_1             = {dv[0]:.6f} [km/s]
MAN_DV_2             = {dv[1]:.6f} [km/s]
MAN_DV_3             = {dv[2]:.6f} [km/s]
""".format(i=i + 1, man=man, dv=man._dv / 1000.)

    return header + meta + text
