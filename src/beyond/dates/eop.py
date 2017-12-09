#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Retrieve and interpolate data for Earth Orientation and timescales conversions
"""

import warnings
from pathlib import Path
from inspect import isclass

from ..config import config

__all__ = ['register', 'get_eop', "TaiUtc", "Finals", "Finals2000A"]


class TaiUtc():
    """File listing all leap seconds throught history

    This file can be retrieved at http://maia.usno.navy.mil/ser7/tai-utc.dat
    """

    def __init__(self, path):

        self.path = Path(path)
        self.data = []

        with self.path.open() as fhandler:
            lines = fhandler.read().splitlines()

        for line in lines:
            if not line:
                continue

            line = line.split()
            mjd = int(float(line[4]) - 2400000.5)
            value = float(line[6])
            self.data.append(
                (mjd, value)
            )

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
    """History of Earth orientation correction for IAU2000 model

    This file can be retrived at http://maia.usno.navy.mil/ser7/
    """

    deltas = ('dx', 'dy')

    def __init__(self, path):

        self.path = Path(path)
        d1, d2 = self.deltas

        with self.path.open() as fp:
            lines = fp.read().splitlines()

        self.data = {}
        for line in lines:
            line = line.rstrip()
            mjd = int(float(line[7:15]))

            try:
                self.data[mjd] = {
                    'mjd': mjd,
                    # 'flag': line[16],
                    'x': float(line[18:27]),
                    d1: None,
                    # 'Xerror': float(line[27:36]),
                    'y': float(line[37:46]),
                    d2: None,
                    # 'Yerror': float(line[46:55]),
                    'lod': None,
                    'ut1_utc': float(line[58:68])
                }
            except ValueError:
                # Common values (X, Y, UT1-UTC) are not available anymore
                break
            else:
                try:
                    self.data[mjd][d1] = float(line[97:106])
                    self.data[mjd][d2] = float(line[116:125])
                except ValueError:
                    # dX and dY are not available for this date, so we take
                    # the last value available
                    self.data[mjd][d1] = \
                        self.data[mjd - 1][d1]
                    self.data[mjd][d2] = \
                        self.data[mjd - 1][d2]
                    pass
                try:
                    self.data[mjd]['lod'] = float(line[79:86])
                except ValueError:
                    # LOD is not available for this date so we take the last value available
                    self.data[mjd]['lod'] = \
                        self.data[mjd - 1]['lod']
                    pass

    def __getitem__(self, key):
        return self.data[key]

    def items(self):
        return self.data.items()

    def dates(self):
        return self.data.dates()


class Finals(Finals2000A):
    """History of Earth orientation correction for IAU1980 model

    This file can be retrived at http://maia.usno.navy.mil/ser7/
    """
    deltas = ('dpsi', 'deps')


class Eop:
    """Earth Orientation Parameters
    """

    def __init__(self, **kwargs):
        self.x = kwargs['x']
        self.y = kwargs['y']
        self.dx = kwargs['dx']
        self.dy = kwargs['dy']
        self.deps = kwargs['deps']
        self.dpsi = kwargs['dpsi']
        self.lod = kwargs['lod']
        self.ut1_utc = kwargs['ut1_utc']
        self.tai_utc = kwargs['tai_utc']

    def __repr__(self):
        return "{name}(x={x}, y={y}, dx={dx}, dy={dy}, deps={deps}, dpsi={dpsi}, lod={lod}, ut1_utc={ut1_utc}, tai_utc={tai_utc})".format(
            name=self.__class__.__name__,
            **self.__dict__
        )


class EnvError(Exception):
    pass


class EnvWarning(Warning):
    pass


databases = {}
DEFAULT_DBNAME = "default"
"""Default name used for EOP database lookup see :ref:`configuration <eop-dbname>`."""

PASS = "pass"
EXTRA = "extrapolate"
WARN = "warning"
ERROR = "error"

MIS_DEFAULT = ERROR
"""Default behaviour in case of missing value, see :ref:`configuration <eop-missing-policy>`."""


def get_db(dbname=None):
    """Retrieve the database
    """

    if dbname is None:
        dbname = config.get('eop', 'dbname', fallback=DEFAULT_DBNAME)

    if dbname not in databases.keys():
        raise EnvError("Unknown database '%s'" % dbname)

    if isclass(databases[dbname]):
        # Instanciation
        try:
            databases[dbname] = databases[dbname]()
        except Exception as e:
            # Keep the exception in cache in order to not retry instanciation
            # every single time the get_db() function is called, as instanciation
            # of database is generally a time consumming operation.
            # If it failed once, it will most probably fail again
            databases[dbname] = e

    if isinstance(databases[dbname], Exception):
        raise EnvError("Problem at database instanciation") from databases[dbname]

    return databases[dbname]


def get_eop(mjd: float, dbname: str=None) -> Eop:
    """Retrieve Earth Orientation Parameters and timescales differences
    for a given date

    Args:
        mjd: Date expressed as Mean Julian Date
        dbname: Name of the database to use
    Return:
        Eop: Interpolated data for this particuliar MJD
    """

    try:
        return get_db(dbname)[mjd]
    except (EnvError, KeyError) as e:
        if isinstance(e, KeyError):
            msg = "Missing EOP data for mjd = '%s'" % e
        else:
            msg = str(e)

        if policy() == WARN:
            warnings.warn(msg, EnvWarning)
        elif policy() == ERROR:
            raise

    return Eop(x=0, y=0, dx=0, dy=0, deps=0, dpsi=0, lod=0, ut1_utc=0, tai_utc=0)


def policy():
    pol = config.get("eop", "missing_policy", fallback=MIS_DEFAULT)
    if pol not in (PASS, EXTRA, WARN, ERROR):
        raise RuntimeError("Unknown config value for 'eop.missing_policy'")

    return pol


def register(name=DEFAULT_DBNAME):
    """Register an Eop Database

    The only requirement of this database is that it should have ``__getitem__``
    method accepting MJD as float.

    Example:

    .. code-block:: python

        @register()
        class SqliteEnvDatabase:
            # sqlite implementation
            # this database will be known as 'default'

        @register('json')
        class JsonEnvDatabase:
            # JSON implementation

        get_eop(58090.2)                    # get Eop from SqliteEnvDatabase
        get_eop(58090.2, dbname='default')  # same as above
        get_eop(58090.2, dbname='json')     # get Eop from JsonEnvDatabase
    """

    # I had a little trouble setting this function up, due to the fact that
    # I wanted it to be usable both as a simple decorator (``@register``)
    # and a decorator with arguments (``@register('mydatabase')``).
    # The current implementation allows this dual-use, but it's a bit hacky.

    # In the simple decorator mode, when the @register decorator is called
    # the argument passed is the class to decorate. So it *is* the decorated
    # function

    # In the decorator-with-arguments mode, the @register decorator should provide
    # a callable that will be the decorated function. This callable takes
    # the class you want to decorate

    if isinstance(name, str):
        # decorator with argument
        def wrapper(klass):
            databases[name] = klass
            return klass

        return wrapper

    else:
        # simple decorator mode
        klass = name
        name = DEFAULT_DBNAME

        databases[name] = klass
        return klass


@register
class SimpleEopDatabase():
    """Simple implementation of database

    Uses ``tai-utc.dat``, ``finals.all`` and ``finals2000A.all`` directly
    without caching nor interpolation.
    """

    def __init__(self):
        path = config.get('eop', 'folder', fallback=Path.cwd())

        # Data reading
        f = Finals(path / 'finals.all')
        f2 = Finals2000A(path / 'finals2000A.all')
        t = TaiUtc(path / "tai-utc.dat")

        # Extracting data from finals files
        self._finals = {}
        for date, values in f.items():
            self._finals[date] = values
            self._finals[date].update(f2[date])

        self._tai_utc = t.data.copy()

    def __getitem__(self, mjd):
        data = self.finals(mjd)
        data["tai_utc"] = self.tai_utc(mjd)

        return Eop(**data)

    def finals(self, mjd: float):
        return self._finals[int(mjd)].copy()

    def tai_utc(self, mjd: float):
        for date, value in reversed(self._tai_utc):
            if date <= mjd:
                return value
        else:
            raise KeyError(mjd)
