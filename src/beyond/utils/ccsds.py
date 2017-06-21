"""This module provides ways to handle the CCSDS Orbit Data Message formats

It is based ond the CCSDS ODM Blue Book from Nov. 2009 (502.0-B-2)
"""

import numpy as np

from .date import Date
from ..orbits import Orbit, Ephem


class CCSDS:
    """Class handling the CCSDS Orbit Data Message formats
    """

    @classmethod
    def load(cls, filepath):  # pragma: no cover
        """Read a file
        """
        with open(filepath) as fh:
            content = cls.loads(fh.read())

        return content

    @classmethod
    def loads(cls, text):
        """
        Args:
            text (str):
        Return:
            Orbit or Ephem
        Raise:
            ValueError: when the text is not a recognizable CCSDS format
        """
        if text.startswith("CCSDS_OEM_VERS"):
            content = cls._read_oem(text)
        elif text.startswith("CCSDS_OPM_VERS"):
            content = cls._read_opm(text)
        else:
            raise ValueError("Unknown CCSDS type")
        return content

    @classmethod
    def dump(cls, data, filepath, **kwargs):  # pragma: no cover
        """Write a file
        """
        with open(filepath, 'w') as fp:
            fp.write(cls.dumps(data, **kwargs))

    @classmethod
    def dumps(cls, data, **kwargs):
        """Create a string CCSDS representation of the object
        """
        if isinstance(data, Ephem):
            content = cls._dump_oem(data, **kwargs)
        elif isinstance(data, Orbit):
            content = cls._dump_opm(data, **kwargs)
        else:
            raise TypeError("Unknown object type")

        return content

    @classmethod
    def _float(cls, line):
        """Conversion of state vector field, with automatic unit handling
        """
        field = line.partition('=')[-1].strip()
        if "[" in field:
            # There is a unit field
            value, sep, unit = field.partition("[")
            unit = sep + unit

            # As defined in the CCSDS Orbital Data Message Blue Book, the une should
            # be the same as defined in table 3-3 which are for km and km/s for position and
            # velocity respectively. Thus, there should be no other conversion to make
            if unit in ("[km]", "[km/s]"):
                multiplier = 1000
            else:
                raise ValueError("Unknown unit for this field", unit)
        else:
            value = field
            # if no unit is provided, the default is km, and km/s
            multiplier = 1000

        return float(value) * multiplier

    @classmethod
    def _read_oem(cls, string):
        """
        Args:
            string (str): String containing the OEM
        Return:
            Ephem:
        """

        method, order, frame, scale = None, None, None, None
        data_block = False
        ephem = []

        for line in string.splitlines():

            if not line or line.startswith("COMMENT"):  # pragma: no cover
                continue

            elif line.startswith("TIME_SYSTEM"):
                scale = line.partition("=")[-1].strip()

            elif line.startswith("REF_FRAME"):
                frame = line.partition('=')[-1].strip()

            elif line.startswith('INTERPOLATION_DEGREE'):
                order = int(line.partition("=")[-1].strip()) + 1

            elif line.startswith('INTERPOLATION'):
                method = line.partition("=")[-1].strip().lower()

            elif line.startswith('META_STOP'):
                if None in (frame, scale):
                    raise ValueError("Missing field")

                data_block = True
                continue

            if not data_block:
                continue

            # From now ow, each non-empty line is a state vector
            date, *state_vector = line.split()
            date = Date.strptime(date, "%Y-%m-%dT%H:%M:%S.%f", scale=scale)

            # Conversion from km to m and from km/s to m/s
            state_vector = np.array([float(x) for x in state_vector]) * 1000

            ephem.append(Orbit(date, state_vector, 'cartesian', frame, None))

        if not ephem:
            raise ValueError("Empty ephemeris")

        return Ephem(ephem, method=method, order=order)

    @classmethod
    def _read_opm(cls, string):
        """Read of OPM string
        Args:
            string (str): Text containing the OPM
        Return:
            Orbit:
        """

        scale, frame, date, x, y, z, vx, vy, vz = [None] * 9

        for line in string.splitlines():
            if not line or line.startswith("COMMENT"):
                continue
            elif line.startswith("TIME_SYSTEM"):
                scale = line.partition("=")[-1].strip()
            elif line.startswith("REF_FRAME"):
                frame = line.partition('=')[-1].strip()
            elif line.startswith("EPOCH"):
                date = line.partition("=")[-1].strip()
                date = Date.strptime(date, "%Y-%m-%dT%H:%M:%S.%f", scale=scale)
            elif line.startswith("X_DOT"):
                vx = cls._float(line)
            elif line.startswith("Y_DOT"):
                vy = cls._float(line)
            elif line.startswith("Z_DOT"):
                vz = cls._float(line)
            elif line.startswith("X"):
                x = cls._float(line)
            elif line.startswith("Y"):
                y = cls._float(line)
            elif line.startswith("Z"):
                z = cls._float(line)

        if None in [scale, frame, x, y, z, vx, vy, vz] or not isinstance(date, Date):
            raise ValueError("Missing mandatory parameter")

        return Orbit(date, [x, y, z, vx, vy, vz], 'cartesian', frame, None)

    @classmethod
    def _dump_header(cls, data, ccsds_type, **kwargs):

        header = """CCSDS_{type}_VERS = 2.0
CREATION_DATE = {creation_date:%Y-%m-%dT%H:%M:%S}
ORIGINATOR = {originator}

META_START
OBJECT_NAME          = {name}
OBJECT_ID            = {cospar_id}
CENTER_NAME          = {orb.frame.center.name}
REF_FRAME            = {orb.frame}
"""     .format(
            creation_date=Date.now(),
            originator=kwargs.get("originator", "???"),
            name=kwargs.get("name", "???"),
            cospar_id=kwargs.get("cospar_id", "???"),
            orb=data,
            type=ccsds_type.upper()
        )

        return header

    @classmethod
    def _dump_oem(cls, data, **kwargs):
        data.form = 'cartesian'

        interp = data.method.title()
        if data.method != data.LINEAR:
            interp += "\nINTERPOLATION_DEGREE = {}".format(data.order - 1)

        header = cls._dump_header(data, "OEM", **kwargs)
        header += """TIME_SYSTEM          = {orb.start.scale.name}
START_TIME           = {orb.start:%Y-%m-%dT%H:%M:%S.%f}
STOP_TIME            = {orb.stop:%Y-%m-%dT%H:%M:%S.%f}
INTERPOLATION        = {interp}
META_STOP

"""     .format(
            creation_date=Date.now(),
            originator=kwargs.get("originator", "???"),
            name=kwargs.get("name", "???"),
            cospar_id=kwargs.get("cospar_id", "???"),
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

        return header + "\n".join(text)

    @classmethod
    def _dump_opm(cls, data, **kwargs):

        cart = data.copy(form="cartesian")
        kep = data.copy(form="keplerian")

        header = cls._dump_header(data, "OPM", **kwargs) + """TIME_SYSTEM          = {orb.date.scale.name}
META_STOP

""".format(orb=cart)

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

        return header + text
