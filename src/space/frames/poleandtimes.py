#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
from pathlib import Path
from collections import namedtuple

import space.utils.interpol as interpol

# __all__ = ['PolePosition', 'TimeScales']

ScalesDiff = namedtuple('ScalesDiff', ('ut1_tai', 'ut1_utc', 'tai_utc'))


def _day_boundaries(d):
    """
    Args:
        d (Date): Date as a MJD
    """
    return int(math.floor(d)), int(math.ceil(d))


class TimeScales:

    @classmethod
    def _get(cls, date):
        """
        Args:
            date (float)
        """
        ut1_utc = Finals2000A().data[date]['time']['UT1-UTC']
        tai_utc = TaiUtc.get(date)
        ut1_tai = ut1_utc - tai_utc
        return ScalesDiff(ut1_tai, ut1_utc, tai_utc)

    @classmethod
    def get(cls, date):
        if date == int(date):
            return cls._get(date)
        else:
            dates = _day_boundaries(date)
            start = cls._get(dates[0])
            stop = cls._get(dates[1])

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
            date (int): Date in MJD
        """
        values = Finals2000A().data[date]['pole'].copy()
        values.update(Finals().data[date]['pole'])
        return values

    @classmethod
    def get(cls, date):
        """
        Args:
            date (float): Date in MJD
        Return:
            dict

        X and Y in arcsecond
        dpsi, deps, dX and dY in milli-arcsecond
        LOD in millisecond
        """

        if date == int(date):
            # no need for interpolation
            return cls._get(date)
        else:
            # linear interpolation

            dates = _day_boundaries(date)

            start = cls._get(dates[0])
            stop = cls._get(dates[1])

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

            with cls.path.open() as f:
                lines = f.read().splitlines()

            for line in lines:
                if line.startswith("#") or not line:
                    continue

                start, stop, value, *_ = line.split()
                value = int(value)
                cls._data.append(
                    (int(start), int(stop), value)
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
    """

    """

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

                try:
                    cls._instance.data[mjd] = {
                        'mjd': mjd,
                        'pole': {
                            # 'flag': line[16],
                            'X': float(line[18:27]),
                            cls._deltas[0]: None,
                            # 'Xerror': float(line[27:36]),
                            'Y': float(line[37:46]),
                            cls._deltas[1]: None,
                            # 'Yerror': float(line[46:55]),
                            'LOD': None,
                        },
                        'time': {
                            'UT1-UTC': float(line[58:68])
                        }
                    }
                except ValueError:
                    # Common values (X, Y, UT1-UTC) are not available anymore
                    break
                else:
                    try:
                        cls._instance.data[mjd]['pole'][cls._deltas[0]] = float(line[97:106])
                        cls._instance.data[mjd]['pole'][cls._deltas[1]] = float(line[116:125])
                    except ValueError:
                        # dX and dY are not available for this date
                        pass
                    try:
                        cls._instance.data[mjd]['pole']['LOD'] = float(line[79:86])
                    except ValueError:
                        # LOD is not available for this date
                        pass

        return cls._instance


class Finals(Finals2000A):

    path = Path(__file__).parent / "data" / "finals.all"
    _instance = None
    _deltas = ('dpsi', 'deps')
