
"""

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

import numpy as np
from string import ascii_uppercase
from datetime import datetime, timedelta

from space.utils.date import Date
from space.orbits.orbit import Orbit
from space.propagators.sgp4 import Sgp4


def _float(text):
    """Fonction to convert the 'decimal point assumed' format of TLE to actual
    float
    """
    if text.startswith("-"):
        text = "-.%s" % text[1:]
    else:
        text = ".%s" % text

    if "+" in text or "-" in text:
        value, sign, expo = text.rpartition('+') if '+' in text else text.rpartition('-')
        v = float('{value}e{sign}{expo}'.format(value=value, sign=sign, expo=expo))
    else:
        v = float(text)

    return v


class Tle:
    """TLE parsing
    """

    def __init__(self, text):
        """
        Args:
            text (str):
        """

        if type(text) is str:
            text = text.splitlines()

        self.name = ""
        if len(text) == 3:
            self.name = text.pop(0).strip()

        self._check_validity(text)

        first, second = text[0].split(), text[1].split()

        self.norad_id = int(first[1][:-1])
        self.classification = first[1][-1]
        year = int(first[2][:2])
        year += 1900 if self.norad_id < 26052 else 2000
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

    @classmethod
    def _check_validity(cls, text):

        tr_table = str.maketrans({c: None for c in (ascii_uppercase + "+ .")})
        for line in text:
            no_letters = line.translate(tr_table).replace("-", "1")
            checksum = str(sum([int(l) for l in no_letters[:-1]]))[-1]
            if checksum != line[-1]:
                raise ValueError("Checksum validation failed")

    def to_list(self):
        return [self.i, self.Ω, self.e, self.ω, self.M, self.n]

    def orbit(self):
        """Convert TLE to Orbit object, in order to make computations on it

        Return:
            ~space.orbits.orbit.Orbit:
        """
        data = {'bstar': self.bstar, 'ndot': self.ndot, 'ndotdot': self.ndotdot}
        return Orbit(self.epoch, self.to_list(), "TLE", "TEME", Sgp4, **data)
