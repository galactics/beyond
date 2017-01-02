#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Retrieve and interpolate data for pole position and timescales conversions
"""

import math

from collections import namedtuple

from ..config import config, ConfigError

__all__ = ['get_timescales', 'get_pole']


ScalesDiff = namedtuple('ScalesDiff', ('ut1_utc', 'tai_utc'))


def linear(x: float, x_list: tuple, y_list: tuple):
    """Linear interpolation

    Args:
        x (float): Coordinate of the interpolated value
        x_list (tuple): x-coordinates of data
        y_list (tuple): y-coordinates of data
    Return:
        float

    Example:
        >>> x_list = [1, 2]
        >>> y_list = [12, 4]
        >>> linear(1.75, x_list, y_list)
        6.0

    """
    x0, x1 = x_list
    y0, y1 = y_list
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def _day_boundaries(day: float) -> tuple:
    """
    Args:
        day: Date as a MJD

    Example:
        >>> _day_boundaries(57687.71847184054)
        (57687, 57688)
    """
    return int(math.floor(day)), int(math.ceil(day))


def _get_timescales(date: int):
    """Retrieve raw timescale data from different file classes
    """
    try:
        ut1_utc = Finals2000A()[date]['time']['UT1-UTC']
        tai_utc = TaiUtc()[date]
    except ConfigError:
        ut1_utc = 0
        tai_utc = 0

    return ScalesDiff(ut1_utc, tai_utc)


def get_timescales(date: float) -> tuple:
    """Get the various time-scale differences from environment data

    Args:
        date (float): Date in MJD
    Return:
        tuple: 2-element (UT1-UTC, TAI-UTC)
    """

    if date == int(date):
        return _get_timescales(int(date))
    else:
        dates = _day_boundaries(date)
        start = _get_timescales(dates[0])
        stop = _get_timescales(dates[1])

        result = ScalesDiff(
            linear(date, dates, (start[0], stop[0])),
            start[1]
        )
        return result


def _get_pole(date: int):
    """
    Args:
        date (int): Date in MJD
    """
    try:
        values = Finals2000A()[date]['pole'].copy()
        values.update(Finals()[date]['pole'])
    except ConfigError:
        values = {
            'X': 0.,
            'Y': 0.,
            'dX': 0.,
            'dY': 0.,
            'dpsi': 0.,
            'deps': 0.,
            'LOD': 0.,
        }
    return values


def get_pole(date: float):
    """Get the pole-motion informations from environment data

    Args:
        date (float): Date in MJD
    Return:
        dict

    X and Y in arcsecond, dpsi, deps, dX and dY in milli-arcsecond and LOD
    in millisecond.
    """

    if date == int(date):
        # no need for interpolation
        return _get_pole(int(date))
    else:
        # linear interpolation
        dates = _day_boundaries(date)
        start = _get_pole(dates[0])
        stop = _get_pole(dates[1])

        result = {}
        for k in start.keys():
            result[k] = linear(date, dates, (start[k], stop[k]))

        return result


class TaiUtc():
    """File listing all leap seconds throught history

    This file can be retrieved at http://maia.usno.navy.mil/ser7/tai-utc.dat
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:

            cls._instance = super().__new__(cls)

            cls._instance.path = config['folder'] / "env" / "tai-utc.dat"
            cls._instance.data = []

            with cls._instance.path.open() as fhandler:
                lines = fhandler.read().splitlines()

            for line in lines:
                if not line:
                    continue

                line = line.split()
                mjd = float(line[4]) - 2400000.5
                value = float(line[6])
                cls._instance.data.append(
                    (mjd, value)
                )

        return cls._instance

    def __getitem__(self, date):
        for mjd, value in reversed(self.data):
            if mjd <= date:
                return value

    def get_last_next(self, date):
        """Provide the last and next leap-second events relative to a date

        Args:
            date (float): Date in MJD
        Return:
            tuple:
        """
        l, n = (None, None), (None, None)

        for mjd, value in reversed(self.data):
            if mjd <= date:
                l = (mjd, value)
                break
            n = (mjd, value)

        return l, n


class Finals2000A():
    """History of pole motion correction for IAU2000 model

    This file can be retrived at http://maia.usno.navy.mil/ser7/finals2000A.all
    """

    filename = 'finals2000A'
    _instance = None
    _deltas = ('dX', 'dY')

    def __new__(cls):
        if cls._instance is None:
            filename = cls.filename + "." + config['env']['pole_motion_source']
            path = config['folder'] / "env" / filename

            cls._instance = super().__new__(cls)
            cls._instance.path = path

            with cls._instance.path.open() as fhandler:
                lines = fhandler.read().splitlines()

            cls._instance.data = {}
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
                        # dX and dY are not available for this date, so we take
                        # the last value available
                        cls._instance.data[mjd]['pole'][cls._deltas[0]] = \
                            cls._instance.data[mjd - 1]['pole'][cls._deltas[0]]
                        cls._instance.data[mjd]['pole'][cls._deltas[1]] = \
                            cls._instance.data[mjd - 1]['pole'][cls._deltas[1]]
                    try:
                        cls._instance.data[mjd]['pole']['LOD'] = float(line[79:86])
                    except ValueError:
                        # LOD is not available for this date so we take the last value available
                        cls._instance.data[mjd]['pole']['LOD'] = \
                            cls._instance.data[mjd - 1]['pole']['LOD']

        return cls._instance

    def __getitem__(self, key):
        return self.data[key]


class Finals(Finals2000A):
    """History of pole motion correction for IAU1980 model

    This file can be retrived at http://maia.usno.navy.mil/ser7/finals.all
    """

    filename = "finals"
    _instance = None
    _deltas = ('dpsi', 'deps')
