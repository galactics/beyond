# -*- coding: utf-8 -*-

import datetime

from space.frames.poleandtimes import TimeScales

TT_TAI = 32.184  # TT - TAI (seconds)


def t_tt(date):
    """Transform to Julian Century (T_TT)

    Example:
        >>> import datetime
        >>> t_tt(datetime.datetime(2004, 4, 6, 7, 51, 28, 386009))
        0.04262363188899416
    """
    tai = date + datetime.timedelta(seconds=TimeScales.get(date).tai_utc)
    tt = tai + datetime.timedelta(seconds=TT_TAI)
    return julian_century(tt)


def julian_century(date):
    return (jd(date) - 2451545.0) / 36525.


def change_scale(date, to):
    """Change the time scale used for a datetime object
    Args:
        date (datetime.datetime)
        to (str): The time scale to convert to
    Return:
        datetime
    """
    to = to.upper()

    if to not in ('TAI', 'UT1', 'TT'):
        raise ValueError("")

    ut1_tai, ut1_utc, tai_utc = [datetime.timedelta(seconds=x) for x in TimeScales.get(date)]

    if to == 'UT1':
        delta = ut1_utc
    elif to == 'TAI':
        delta = tai_utc
    elif to == 'TT':
        delta = tai_utc + datetime.timedelta(seconds=TT_TAI)

    return date + delta


def jd(d):
    """From a date, compute the Julian Date, which is the number of days from
    the January 1, 4712 B.C., 12:00.

    Args:
        d (datetime.datetime)
    Return:
        float

    Example:
        >>> import datetime
        >>> jd(datetime.datetime(1980, 1, 6))
        2444244.5
        >>> jd(datetime.datetime(2000, 1, 1, 12))
        2451545.0
        >>> jd(datetime.datetime(1949, 12, 31, 22, 9, 46, 862000))
        2433282.4234590507
        >>> jd(datetime.datetime(2004, 4, 6, 7, 52, 32, 570009))
        2453101.8281547455
    """
    seconds = d.second + d.microsecond / 1e6

    leap = 60
    year, month = d.year, d.month
    if d.month in (1, 2):
        year -= 1
        month += 12
    B = 2 - year // 100 + year // 100 // 4
    C = ((seconds / leap + d.minute) / 60 + d.hour) / 24
    return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + d.day + B - 1524.5 + C
