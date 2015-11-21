#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime
from pathlib import Path
from collections import namedtuple

import space.utils.interpol as interpol

# __all__ = ['PolePosition', 'TimeScales']

ScalesDiff = namedtuple('ScalesDiff', ('ut1_tai', 'ut1_utc', 'tai_utc'))


def _day_boundaries(d):
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
            dates = _day_boundaries(date)
            start = cls._get(dates[0].date())
            stop = cls._get(dates[1].date())

            result = ScalesDiff(
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

            dates = _day_boundaries(date)

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

    date_list = [
        datetime.date(1992, 1, 1),
        datetime.date(1999, 1, 1),
        datetime.date(2014, 8, 12),
        datetime.date(2015, 2, 27),
        datetime.date.today(),
    ]

    for date in date_list:
        print(date, TimeScales.get(date))
