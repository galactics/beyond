#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Retrieve and interpolate data for Earth Orientation and timescales conversions
"""

import math
import sqlite3
import warnings
from pathlib import Path
from contextlib import contextmanager

from ..config import config
from ..utils.memoize import memoize

__all__ = ['EnvDatabase', 'TaiUtc', 'Finals', 'Finals2000A']


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
            mjd = float(line[4]) - 2400000.5
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


class EnvDatabase:

    _instance = None
    _cursor = None

    PASS = "pass"
    EXTRA = "extrapolate"
    WARN = "warning"
    ERROR = "error"

    MIS_DEFAULT = ERROR  # Default behaviour in case of missing value

    def __new__(cls):
        if cls._instance is None:

            cls._instance = super().__new__(cls)
            self = cls._instance
            self.path = config.folder / "env.db"

            pol = config.get("env", "eop_missing_policy", fallback=cls.MIS_DEFAULT)
            if pol not in (cls.PASS, cls.EXTRA, cls.WARN, cls.ERROR):
                raise RuntimeError("Unknown config value for 'env.eop_missing_policy'")
            self._policy = pol

        return cls._instance

    def uri(self, create=False):
        return "{uri}?mode={mode}".format(
            uri=self.path.as_uri(),
            mode="rwc" if create else "rw"
        )

    @contextmanager
    def connect(self, create=False):
        with sqlite3.connect(self.uri(create=create), uri=True) as connect:
            yield connect.cursor()

    @property
    def cursor(self):
        if self._cursor is None:
            try:
                connect = sqlite3.connect(self.uri(), uri=True)
            except sqlite3.DatabaseError as e:
                raise EnvError("{} : {}".format(e, self.path))
            self._cursor = connect.cursor()
        return self._cursor

    @classmethod
    def get(cls, mjd: float):
        """Retrieve Earth Orientation Parameters and timescales differences
        for a given date

        Args:
            mjd: Date expressed as Mean Julian Date
        Return:
            Eop:
        """

        self = cls()

        try:
            return self._get(mjd)
        except EnvError as e:
            if self._policy == self.WARN:
                warnings.warn(str(e), EnvWarning)
            elif self._policy == self.ERROR:
                raise e

        return Eop(x=0, y=0, dx=0, dy=0, deps=0, dpsi=0, lod=0, ut1_utc=0, tai_utc=0)

    @memoize
    def _get(self, mjd: float):

        if isinstance(mjd, int) or mjd.is_integer():
            data = self._get_finals(int(mjd)).copy()
        else:
            mjd0 = int(math.floor(mjd))
            mjd1 = int(math.ceil(mjd))
            data_start = self._get_finals(mjd0)
            data_stop = self._get_finals(mjd1)

            data = {}
            for field in data_start.keys():
                y0 = data_start[field]
                y1 = data_stop[field]
                data[field] = y0 + (y1 - y0) * (mjd - mjd0) / (mjd1 - mjd0)

        data['tai_utc'] = self._get_tai_utc(int(mjd))

        return Eop(**data)

    @memoize
    def _get_finals(self, mjd: int):

        self.cursor.execute("SELECT * FROM finals WHERE mjd = ?", (mjd, ))
        raw_data = self.cursor.fetchone()

        # In the case of a missing value, we take the last available
        if raw_data is None and self._policy in (self.WARN, self.EXTRA):

            self.cursor.execute("SELECT * FROM finals WHERE mjd <= ? ORDER BY mjd DESC LIMIT 1", (mjd, ))
            raw_data = self.cursor.fetchone()

            if raw_data is not None and self._policy == self.WARN:
                warnings.warn("Missing EOP data. Extrapolating from previous")

        if raw_data is None:
            raise EnvError("Missing EOP data for mjd = %d." % mjd)

        # removal of MJD
        keys = ("x", "y", "dx", "dy", "deps", "dpsi", "lod", "ut1_utc")
        return dict(zip(keys, raw_data[1:]))

    @memoize
    def _get_tai_utc(self, mjd: int):
        self.cursor.execute("SELECT * FROM tai_utc WHERE mjd <= ? ORDER BY mjd DESC LIMIT 1", (mjd, ))
        raw_data = self.cursor.fetchone()

        if raw_data is None:
            raise EnvError("No TAI-UTC data for mjd = '%d'" % mjd)

        # only return the tai-utc data, not the mjd
        return raw_data[1]

    @classmethod
    def get_range(cls):
        """Get the first and last date available for Earth Orientation Parameters

        Return:
            tuple
        """
        self = cls()
        self.cursor.execute("SELECT MIN(mjd) AS min, MAX(mjd) AS max FROM finals")
        raw_data = self.cursor.fetchone()

        if raw_data is None:
            raise EnvError("No data for range")

        return raw_data

    @classmethod
    def get_framing_leap_seconds(cls, mjd: float):
        """
        Args:
            mjd (float):
        Return:
            tuple: previous and next leap second relative to mjd

        If no data is available, return None
        """
        self = cls()
        self.cursor.execute("SELECT * FROM tai_utc ORDER BY mjd DESC")

        l, n = (None, None), (None, None)

        for mjd_i, value in self.cursor:
            if mjd_i <= mjd:
                l = (mjd_i, value)
                break
            n = (mjd_i, value)

        return l, n

    @classmethod
    def insert(cls, *, finals=None, finals2000a=None, tai_utc=None):
        """Insert values extracted from Finals, Finals2000A and tai-utc files
        into the environment database
        """

        self = cls()

        if None in (finals, finals2000a, tai_utc):
            raise TypeError("All three arguments are required")

        if not self.path.exists():
            self.create_tables()  # file doesn't exists
        else:
            # The file exists, but we can't connect
            try:
                self.connect()
            except sqlite3.OperationalError:
                self.create_tables()  # file exists

        data = {}
        for date in finals.data.keys():
            data[date] = finals.data[date].copy()
            data[date].update(finals2000a.data[date])

        self._insert_eops(data)
        self._insert_tai_utc(tai_utc.data)

    def _insert_eops(self, eops: dict):
        """Insert EOP values into the database, for later use

        Prime sources for these values are :py:class:`Finals` and
        :py:class:`Finals2000A` files

        Args:
            eops (dict): The keys are the date of the value in MJD (int) and the
                values are dictionaries containing the x, y, dx, dy, deps, dpsi,
                lod and ut1_utc data
        """
        with self.connect() as cursor:
            for mjd, eop in eops.items():
                cursor.execute(
                    "INSERT OR REPLACE INTO finals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        mjd, eop['x'], eop["y"], eop["dx"], eop["dy"],
                        eop["deps"], eop["dpsi"], eop["lod"], eop["ut1_utc"],
                    )
                )

    def _insert_tai_utc(self, tai_utcs: dict):
        """Insert TAI-UTC values into the database
        """

        with self.connect() as cursor:

            try:
                cursor.execute("DELETE FROM tai_utc")
            except sqlite3.OperationalError:
                pass

            for mjd, tai_utc in tai_utcs:
                cursor.execute("INSERT INTO tai_utc VALUES (?, ?)", (mjd, tai_utc))

    def create_tables(self):
        """Create the base tables to store all the data
        """
        with self.connect(create=True) as cursor:
            cursor.executescript("""
                CREATE TABLE `finals` (
                    `mjd`       INTEGER NOT NULL UNIQUE,
                    `x`         REAL NOT NULL,
                    `y`         REAL NOT NULL,
                    `dx`        REAL NOT NULL,
                    `dy`        REAL NOT NULL,
                    `dpsi`      REAL NOT NULL,
                    `deps`      REAL NOT NULL,
                    `lod`       REAL NOT NULL,
                    `ut1_utc`   REAL NOT NULL,
                    PRIMARY KEY(`mjd`)
                );
                CREATE TABLE `tai_utc` (
                    `mjd`   INTEGER NOT NULL,
                    `tai_utc`   INTEGER NOT NULL,
                    PRIMARY KEY(`mjd`)
                );""")
