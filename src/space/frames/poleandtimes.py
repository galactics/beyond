#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime
import numpy as np
from pathlib import Path

import space.utils.interpol as interpol

__all__ = ['PolePosition', 'TimeScales']

obliquity_j2000 = 23.439291
TT_TAI = 32.184  # TT - TAI (seconds)


def rot1(x):
    return np.array([
        [1, 0, 0],
        [0, np.cos(x), np.sin(x)],
        [0, -np.sin(x), np.cos(x)]
    ])


def rot2(x):
    return np.array([
        [np.cos(x), 0, -np.sin(x)],
        [0, 1, 0],
        [np.sin(x), 0, np.cos(x)]
    ])


def rot3(x):
    return np.array([
        [np.cos(x), np.sin(x), 0],
        [-np.sin(x), np.cos(x), 0],
        [0, 0, 1]
    ])


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


def t_tt(date):
    """Transform to Julian Century (T_TT)

    Example:
        >>> import datetime
        >>> t_tt(datetime.datetime(2004, 4, 6, 7, 51, 28, 386009))
        0.04262363188899416
    """
    tai = date + datetime.timedelta(seconds=TimeScales.get(date)[-1])
    tt = tai + datetime.timedelta(seconds=TT_TAI)
    return (jd(tt) - 2451545.0) / 36525


def nutation(model, date):
    t = t_tt(date)
    if model == 1980:
        # Model 1980
        epsilon_bar = np.deg2rad(23.439291 - 0.0130042 * t - 1.64e-7 * t ** 2 + 5.04e-7 * t ** 3)
        pole = PolePosition.get(date)
        delta_epsilon = np.deg2rad(pole['deps'])
        delta_psi = np.deg2rad(pole['dpsi'])
        epsilon = epsilon_bar + delta_epsilon
        return rot1(-epsilon_bar) @ rot3(Delta_Psi) @ rot1(epsilon)


def day_boundaries(d):
    """
    Args:
        d (datetime.datetime)
    """
    start_d = d.replace(hour=0, minute=0, second=0, microsecond=0)
    stop_d = start_d + datetime.timedelta(days=1)
    return start_d, stop_d


class TimeScales:

    @classmethod
    def _get(cls, date):
        """
        Args:
            date (datetime.date)
        """
        ut1_utc = Finals2000A().data[date]['time']['UT1-UTC']
        tai_utc = TaiUtc.get(date)
        ut1_tai = ut1_utc - tai_utc
        return ut1_tai, ut1_utc, tai_utc

    @classmethod
    def get(cls, date):
        if type(date) is datetime.date or date.timestamp() % 86400 == 0:
            date = date.date() if type(date) is datetime.datetime else date
            return cls._get(date)
        else:
            dates = day_boundaries(date)
            start = cls._get(dates[0].date())
            stop = cls._get(dates[1].date())

            result = (
                interpol.linear(date, dates, (start[0], stop[0])),
                interpol.linear(date, dates, (start[1], stop[1])),
                start[-1]
            )
            return result


class PolePosition:

    @classmethod
    def _get(cls, date):
        """
        Args:
            date (datetime.date)
        """
        values = Finals2000A().data[date]['pole'].copy()
        values.update(Finals().data[date]['pole'])
        return values

    @classmethod
    def get(cls, date):
        if type(date) is datetime.date or date.timestamp() % 86400 == 0:
            # no need for interpolation
            date = date.date() if type(date) is datetime.datetime else date
            return cls._get(date)
        else:
            # linear interpolation

            dates = day_boundaries(date)

            start = cls._get(dates[0].date())
            stop = cls._get(dates[1].date())

            result = {}
            for k in start.keys():
                result[k] = interpol.linear(date, dates, (start[k], stop[k]))

            return result


class TaiUtc():

    path = Path(__file__).parent / "data" / "tai-utc.txt"
    _data = []

    @classmethod
    def _initialise(cls):
        if not cls._data:

            _date = lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date()
            with cls.path.open() as f:
                lines = f.read().splitlines()

            for line in lines:
                if line.startswith("#"):
                    continue

                start, stop, value = line.split()
                start, stop = _date(start), _date(stop)
                value = int(value)
                cls._data.append(
                    (start, stop, value)
                )

    @classmethod
    def get(cls, date):
        cls._initialise()
        tmp = cls()._data[0][2]
        for start, stop, value in cls()._data:
            if start <= date < stop:
                tmp = value
        return tmp


class Finals2000A():

    path = Path(__file__).parent / "data" / "finals2000A.all"
    _instance = None
    _deltas = ('dX', 'dY')

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.data = {}

            with cls._instance.path.open() as f:
                lines = f.read().splitlines()

            for line in lines:
                line = line.rstrip()
                mjd = int(float(line[7:15]))
                date = datetime.date.fromordinal(678576 + mjd)

                try:
                    cls._instance.data[date] = {
                        'mjd': mjd,
                        'pole': {
                            # 'flag': line[16],
                            'X': float(line[18:27]),
                            cls._deltas[0]: None,
                            # 'Xerror': float(line[27:36]),
                            'Y': float(line[37:46]),
                            cls._deltas[1]: None,
                            # 'Yerror': float(line[46:55])
                        },
                        'time': {
                            'UT1-UTC': float(line[58:68])
                        }
                    }
                except ValueError:
                    break
                else:
                    try:
                        cls._instance.data[date]['pole'][cls._deltas[0]] = float(line[97:106])
                        cls._instance.data[date]['pole'][cls._deltas[1]] = float(line[116:125])
                    except ValueError:
                        # dX and dY are not available for this date
                        pass

        return cls._instance


class Finals(Finals2000A):

    path = Path(__file__).parent / "data" / "finals.all"
    _instance = None
    _deltas = ('dpsi', 'deps')


if __name__ == '__main__':

    dates = [
        datetime.date(1992, 1, 1),
        datetime.date(1999, 1, 1),
        datetime.date(2014, 8, 12),
        datetime.date(2015, 2, 27),
        datetime.date.today(),
    ]

    for date in dates:
        print(date, TimeScales.get(date))
