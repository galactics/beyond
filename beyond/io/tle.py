"""Module for handling TLE reading and writing

.. code-block:: text

    ISS (ZARYA)
    1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
    2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537

    First Line
    1   01–01   Line number                                                                      1
    2   03–07   Satellite number                                                                 25544
    3   08–08   Classification (U=Unclassified)                                                  U
    4   10–11   International Designator (Last two digits of launch year)                        98
    5   12–14   International Designator (Launch number of the year)                             067
    6   15–17   International Designator (piece of the launch)                                   A
    7   19–20   Epoch Year (last two digits of year)                                             08
    8   21–32   Epoch (day of the year and fractional portion of the day)                        264.51782528
    9   34–43   First Time Derivative of the Mean Motion divided by two [10]                     −.00002182
    10  45–52   Second Time Derivative of Mean Motion divided by six (decimal point assumed)     00000-0
    11  54–61   BSTAR drag term (decimal point assumed) [10]                                     -11606-4
    12  63–63   The number 0 (originally this should have been "Ephemeris type")                 0
    13  65–68   Element set number. Incremented when a new TLE is generated for this object.[10] 292
    14  69–69   Checksum (modulo 10)                                                             7

    Second Line
    1   01–01   Line number                                         2
    2   03–07   Satellite number                                    25544
    3   09–16   Inclination (degrees)                               51.6416
    4   18–25   Right ascension of the ascending node (degrees)     247.4627
    5   27–33   Eccentricity (decimal point assumed)                0006703
    6   35–42   Argument of perigee (degrees)                       130.5360
    7   44–51   Mean Anomaly (degrees)                              325.0288
    8   53–63   Mean Motion (revolutions per day)                   15.72125391
    9   64–68   Revolution number at epoch (revolutions)            56353
    10  69–69   Checksum (modulo 10)                                7
"""

import logging
import numpy as np
from string import ascii_uppercase
from datetime import datetime, timedelta

from ..orbits import Orbit
from ..dates.date import Date
from ..errors import ParseError

log = logging.getLogger(__name__)


class TleParseError(ParseError):
    pass


def _float(text):
    """Fonction to convert the 'decimal point assumed' format of TLE to actual
    float

    >>> _float('0000+0')
    0.0
    >>> _float('+0000+0')
    0.0
    >>> _float('34473-3')
    0.00034473

    >>> _float('-60129-4')
    -6.0129e-05
    >>> _float('+45871-4')
    4.5871e-05
    >>> _float('24814+0')
    0.24814
    """

    text = text.strip()

    if text[0] in ("-", "+"):
        text = f"{text[0]}.{text[1:]}"
    else:
        text = f"+.{text}"

    if "+" in text[1:] or "-" in text[1:]:
        value, exp_sign, expo = (
            text.rpartition("+") if "+" in text[1:] else text.rpartition("-")
        )
        v = float(f"{value}e{exp_sign}{expo}")
    else:
        v = float(text)

    return v


def _unfloat(flt, precision=5):
    """Function to convert float to 'decimal point assumed' format

    >>> _unfloat(0)
    '00000-0'
    >>> _unfloat(3.4473e-4)
    '34473-3'
    >>> _unfloat(-6.0129e-05)
    '-60129-4'
    >>> _unfloat(4.5871e-05)
    '45871-4'
    >>> _unfloat(0.24814)
    '24814+0'
    """

    if flt == 0.0:
        return f"{'0' * precision}-0"

    num, _, exp = f"{flt:.{precision - 1}e}".partition("e")
    exp = int(exp)
    num = num.replace(".", "")

    return f"{num}{exp+1:+d}"


class Tle:
    """TLE parsing"""

    def __init__(self, text, **kwargs):
        """
        Args:
            text (str):
        """

        # Replace split by parsing by string index

        if isinstance(text, str):
            text = text.splitlines()

        self.name = ""
        if len(text) == 3:
            self.name = text.pop(0).strip()
            if self.name.startswith("0 "):
                self.name = self.name[2:]

        self._check_validity(text)
        self.text = "\n".join(text)

        first, second = text[0], text[1]

        self.norad_id = int(first[2:7])
        self.classification = first[7]

        if first[9:17].strip():
            year = int(first[9:11])
            year += 1900 if year >= 57 else 2000  # This condition works until 2057
            self.cospar_id = f"{year}-{first[11:17].strip()}"
        else:
            self.cospar_id = ""

        year = int(first[18:20])
        year += 1900 if year >= 57 else 2000  # This condition works until 2057
        epoch = datetime(year, 1, 1) + timedelta(days=float(first[20:32]) - 1)
        self.epoch = Date(epoch)
        self.ndot = float(first[33:43]) * 2
        self.ndotdot = _float(first[44:52]) * 6
        self.bstar = _float(first[53:61])
        self.element_nb = int(first[65:68])
        self.revolutions = int(second[63:68])
        self.type = int(first[62:63])

        self.i = np.deg2rad(float(second[8:16]))  # inclination
        self.Ω = np.deg2rad(
            float(second[17:25])
        )  # right ascension of the ascending node
        self.e = _float(second[26:33])  # eccentricity
        self.ω = np.deg2rad(float(second[34:42]))  # argument of periapsis
        self.M = np.deg2rad(float(second[43:51]))  # mean anomaly
        self.n = (
            float(second[52:63]) * 2 * np.pi / 86400.0
        )  # mean motion (rev/day converted to rad/s)

        # To store additional data (such as source, date of creation, etc.)
        self.kwargs = kwargs

    def __str__(self):
        return self.text

    @classmethod
    def _check_validity(cls, text):
        """Check the validity of a TLE

        Args:
            text (tuple of str)
        Raise:
            TleParseError
        """

        if not text[0].lstrip().startswith("1 ") or not text[1].lstrip().startswith(
            "2 "
        ):
            raise TleParseError("Line number check failed")

        for i, line in enumerate(text):
            line = line.strip()

            if len(line) != 69:
                raise TleParseError(
                    f"Invalid TLE size on line {i + 1}. Expected {69}, got {len(line)}."
                )

            check = str(cls._checksum(line))
            if check != line[68]:
                raise TleParseError(
                    "TLE checksum validation failed on line {}. Expected {}, got {}.".format(
                        i + 1, check, line[68]
                    )
                )

    @classmethod
    def _checksum(cls, line):
        """Compute the checksum of a full line

        Args:
            line (str): Line to compute the checksum from
        Return:
            int: Checksum (modulo 10)
        """
        tr_table = str.maketrans({c: None for c in ascii_uppercase + "+ ."})
        no_letters = line[:68].translate(tr_table).replace("-", "1")
        return sum([int(l) for l in no_letters]) % 10

    def to_list(self):
        """Convert the tle to a list representation, with the order as it can be found in the TLE
        representation.
        """
        return [self.i, self.Ω, self.e, self.ω, self.M, self.n]

    def orbit(self):
        """Convert TLE to Orbit object, in order to make computations on it

        Return:
            ~beyond.orbits.orbit.Orbit:
        """
        data = {
            "bstar": self.bstar,
            "ndot": self.ndot,
            "ndotdot": self.ndotdot,
            "tle": self,
            "name": self.name,
            "cospar_id": self.cospar_id,
            "norad_id": self.norad_id,
            "element_nb": self.element_nb,
            "revolutions": self.revolutions,
            "type": self.type,
        }
        return Orbit(self.to_list(), self.epoch, "TLE", "TEME", "Sgp4", **data)

    @classmethod
    def from_orbit(cls, orbit, name=None, norad_id=None, cospar_id=None):
        """Convert an orbit to it's TLE representation

        Args:
            orbit (Orbit)
            norad_id (str or int):
            cospar_id (str):
        Return:
            str: TLE representation
        """

        if name is not None:
            name = f"0 {name}\n"
        elif hasattr(orbit, "name"):
            name = f"0 {orbit.name}\n"
        else:
            name = ""

        if norad_id is None:
            if hasattr(orbit, "norad_id"):
                norad_id = orbit.norad_id
            else:
                norad_id = "99999"

        if cospar_id is not None:
            y, _, i = cospar_id.partition("-")
            cospar_id = y[2:] + i
        elif hasattr(orbit, "cospar_id"):
            y, _, i = orbit.cospar_id.partition("-")
            cospar_id = y[2:] + i
        else:
            cospar_id = ""

        orbit = orbit.copy(form="TLE", frame="TEME")

        date = orbit.date.datetime
        i, Ω, e, ω, M, n = orbit

        line1 = "1 {norad_id}U {cospar_id:<8} {date:%y}{day:012.8f} {ndot:>10} {ndotdot:>8} {bstar:>8} 0 {elnb:>4}".format(
            norad_id=norad_id,
            cospar_id=cospar_id,
            date=date,
            day=int("{:%j}".format(date))
            + date.hour / 24.0
            + date.minute / 1440
            + date.second / 86400
            + date.microsecond / 86400000000.0,
            ndot=f"{orbit.ndot / 2: 0.8f}".replace("0.", "."),
            ndotdot=_unfloat(orbit.ndotdot / 6),
            bstar=_unfloat(orbit.bstar),
            elnb=orbit.element_nb,
        )
        line2 = "2 {norad_id} {i:8.4f} {Ω:8.4f} {e} {ω:8.4f} {M:8.4f} {n:11.8f}{revolutions:>5}".format(
            norad_id=norad_id,
            i=np.degrees(i),
            Ω=np.degrees(Ω),
            e="{:.7f}".format(e)[2:],
            ω=np.degrees(ω),
            M=np.degrees(M),
            n=n * 86400 / (2 * np.pi),
            revolutions=orbit.revolutions,
        )

        line1 += str(cls._checksum(line1))
        line2 += str(cls._checksum(line2))

        return cls(f"{name}{line1}\n{line2}")

    @classmethod
    def from_string(cls, text, comments="#", error="warn"):
        """Generator of TLEs from a string

        Args:
            text (str): A text containing many TLEs
            comments (str): If a line starts with this character, it is ignored
            error (str): How to handle errors while parsing the text. Could be
                'raise', 'warn' or 'ignore'.
        Yields:
            Tle:
        """

        cache = []
        for line in text.splitlines():

            # If the line is empty or begins with a comment mark, we skip it.
            if not line.strip() or line.startswith(comments):
                continue

            # The startswith conditions include a blank space in order to not take into account
            # lines containing only a COSPAR ID, which happens when an object is detected but the
            # JSpOc doesn't know what is the source yet.
            if line.startswith("1 "):
                cache.append(line)
            elif line.startswith("2 "):
                cache.append(line)
                try:
                    yield cls("\n".join(cache))
                except ValueError as e:
                    if error == "raise":
                        raise TleParseError(str(e))
                    elif error == "warn":
                        log.warning(str(e))

                cache = []
            else:
                # In the 3LE format, the first line (numbered 0, or unnumbered) contains the name
                # of the satellite
                # In the TLE format, this line doesn't exists.
                cache = [line]
