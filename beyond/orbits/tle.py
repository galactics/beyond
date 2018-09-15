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

from string import ascii_uppercase
from datetime import datetime, timedelta
import warnings
import numpy as np

from .orbit import Orbit
from ..dates.date import Date


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
    """
    if text[0] in ('-', '+'):
        text = "%s.%s" % (text[0], text[1:])
    else:
        text = "+.%s" % text

    if "+" in text[1:] or "-" in text[1:]:
        value, exp_sign, expo = text.rpartition('+') if '+' in text[1:] else text.rpartition('-')
        v = float('{value}e{exp_sign}{expo}'.format(value=value, exp_sign=exp_sign, expo=expo))
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
    """

    if flt == 0.:
        return "{}-0".format("0" * precision)

    num, _, exp = "{:.{}e}".format(flt, precision - 1).partition('e')
    exp = int(exp)
    num = num.replace('.', '')

    return "%s%d" % (num, exp + 1)


class Tle:
    """TLE parsing
    """

    def __init__(self, text, **kwargs):
        """
        Args:
            text (str):
        """

        if isinstance(text, str):
            text = text.splitlines()

        self.name = ""
        if len(text) == 3:
            self.name = text.pop(0).strip()
            if self.name.startswith('0 '):
                self.name = self.name[2:]

        self._check_validity(text)

        first, second = text[0].split(), text[1].split()

        self.text = "\n".join((text[0].strip(), text[1].strip()))

        self.norad_id = int(first[1][:-1])
        self.classification = first[1][-1]

        year = int(first[2][:2])
        year += 1900 if year >= 57 else 2000  # This condition works until 2057
        self.cospar_id = "%d-%s" % (year, first[2][2:])

        epoch = datetime(2000 + int(first[3][:2]), 1, 1) + timedelta(days=float(first[3][2:]) - 1)
        self.epoch = Date(epoch)
        self.ndot = float(first[4])
        self.ndotdot = _float(first[5])
        self.bstar = _float(first[6])

        self.i = np.deg2rad(float(second[2]))   # inclination
        self.Ω = np.deg2rad(float(second[3]))   # right ascencion of the acending node
        self.e = _float(second[4])              # excentricity
        self.ω = np.deg2rad(float(second[5]))   # argument of periapsis
        self.M = np.deg2rad(float(second[6]))   # mean anomaly
        self.n = float(second[7][:11]) * 2 * np.pi / 86400.  # mean motion (rev/day converted to s⁻¹)

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
            ValueError
        """

        if not text[0].lstrip().startswith('1 ') or not text[1].lstrip().startswith('2 '):
            raise ValueError("Line number check failed")

        for line in text:
            line = line.strip()
            if str(cls._checksum(line)) != line[-1]:
                raise ValueError("Checksum validation failed")

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
            'bstar': self.bstar,
            'ndot': self.ndot,
            'ndotdot': self.ndotdot,
            'tle': self.text
        }
        return Orbit(self.epoch, self.to_list(), "TLE", "TEME", 'Sgp4', **data)

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

        name = "0 %s\n" % name if name is not None else ""
        norad_id = norad_id if norad_id is not None else "99999"

        if cospar_id is not None:
            y, _, i = cospar_id.partition('-')
            cospar_id = y[2:] + i
        else:
            cospar_id = "00001A"

        orbit = orbit.copy(form='TLE', frame='TEME')

        date = orbit.date.datetime
        i, Ω, e, ω, M, n = orbit

        line1 = "1 {norad_id}U {cospar_id:<8} {date:%y}{day:012.8f} {ndot:>10} {ndotdot:>8} {bstar:>8} 0  999".format(
            norad_id=norad_id,
            cospar_id=cospar_id,
            date=date,
            day=int("{:%j}".format(date)) + date.hour / 24. + date.minute / 1440 + date.second / 86400 + date.microsecond / 86400000000.,
            ndot="{: 0.8f}".format(orbit.complements['ndot']).replace("0.", "."),
            ndotdot=_unfloat(orbit.complements['ndotdot']),
            bstar=_unfloat(orbit.complements['bstar']),
        )
        line2 = "2 {norad_id} {i:8.4f} {Ω:8.4f} {e} {ω:8.4f} {M:8.4f} {n:11.8f}99999".format(
            norad_id=norad_id,
            i=np.degrees(i),
            Ω=np.degrees(Ω),
            e="{:.7f}".format(e)[2:],
            ω=np.degrees(ω),
            M=np.degrees(M),
            n=n * 86400 / (2 * np.pi)
        )

        line1 += str(cls._checksum(line1))
        line2 += str(cls._checksum(line2))

        return cls("%s%s\n%s" % (name, line1, line2))

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
            if line.startswith('1 '):
                cache.append(line)
            elif line.startswith('2 '):
                cache.append(line)
                try:
                    yield cls("\n".join(cache))
                except ValueError as e:
                    if error in ('raise', 'warn'):
                        if error == "raise":
                            raise
                        else:
                            warnings.warn(str(e))

                cache = []
            else:
                # In the 3LE format, the first line (numbered 0, or unumbered) contains the name
                # of the satellite
                # In the TLE format, this line doesn't exists.
                cache = [line]
