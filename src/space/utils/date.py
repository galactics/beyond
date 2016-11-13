# -*- coding: utf-8 -*-

"""Date module
"""

import datetime as _datetime

from ..env.poleandtimes import get_timescales
from .node import Node

__all__ = ['Date']


class _Scale(Node):

    HEAD = None
    """Define the top Node of the tree. This one will be used as reference to search for the path
    linking two Nodes together
    """

    def __repr__(self):
        return "<Scale '%s'>" % self.name

    def __str__(self):
        return self.name

    @classmethod
    def get(cls, name):
        return cls.HEAD[name]

    def _scale_ut1_minus_utc(self, date):
        ut1_utc, tai_utc = get_timescales(date.mjd)
        return ut1_utc

    def _scale_tai_minus_utc(self, date):
        ut1_utc, tai_utc = get_timescales(date.mjd)
        return tai_utc

    def _scale_tt_minus_tai(self, date):
        return 32.184

    def _scale_tai_minus_gps(self, date):
        return 19.

    def offset(self, date, new_scale):
        """Compute the offset necessary in order to convert from one time scale to another

        Args:
            date (Date):
            new_scale (str): Name of the desired scale
        Return:
            datetime.timedelta: offset to apply
        """

        delta = 0
        for one, two in self.HEAD.steps(self.name, new_scale):
            one = one.name.lower()
            two = two.name.lower()
            # find the operation
            oper = "_scale_{}_minus_{}".format(two, one)
            # find the reverse operation
            roper = "_scale_{}_minus_{}".format(one, two)
            if hasattr(self, oper):
                delta += getattr(self, oper)(date)
            elif hasattr(self, roper):
                delta -= getattr(self, roper)(date)
            else:  # pragma: no cover
                raise ValueError("Unknown convertion {} => {}".format(one, two))

        return _datetime.timedelta(seconds=delta)


UT1 = _Scale('UT1')
GPS = _Scale('GPS')
UTC = _Scale('UTC', [UT1])
TAI = _Scale('TAI', [UTC, GPS])
TT = _Scale('TT', [TAI])
_Scale.HEAD = TT


class Date:
    """Date object

    All computations and in-memory saving are made in
    `MJD <https://en.wikipedia.org/wiki/Julian_day>`__.

    In the current implementation, the Date object does not handle the
    leap second.
    """

    __slots__ = ["d", "s", "scale", "_cache"]

    MJD_T0 = _datetime.datetime(1858, 11, 17)
    JD_MJD = 2400000.5

    def __init__(self, *args, **kwargs):

        scale = kwargs.get('scale', 'UTC')

        if type(scale) is str:
            scale = _Scale.get(scale.upper())

        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, _datetime.datetime):
                # Python datetime.datetime object
                d, s = self._convert_dt(arg)
            elif isinstance(arg, self.__class__):
                # Date object²
                d = arg.d
                s = arg.s
                scale = arg.scale
            elif isinstance(arg, (float, int)):
                # Julian Day
                if isinstance(arg, int):
                    d = arg
                    s = 0.
                else:
                    d = int(arg)
                    s = (arg - d) * 86400
            else:
                raise TypeError("Unknown argument")
        elif len(args) == 2 and (isinstance(args[0], int) and isinstance(args[1], (int, float))):
            # Julian day and seconds in the day
            d, s = args
        elif len(args) in range(3, 8) and list(map(type, args)) == [int] * len(args):
            # Same constructor as datetime.datetime
            # (year, month, day[, hour[, minute[, second[, microsecond]]]])
            dt = _datetime.datetime(*args)
            d, s = self._convert_dt(dt)
        else:
            raise ValueError("Unknown arguments")

        # As Date acts like an immutable object, we can't set its attributes normally
        # like when we do ``self.d = d``
        super().__setattr__('d', d)
        super().__setattr__('s', s)
        super().__setattr__('scale', scale)
        super().__setattr__('_cache', {})

    def __setattr__(self, *args):  # pragma: no cover
        raise TypeError("Can not modify attributes of immutable object")

    def __delattr__(self, *args):  # pragma: no cover
        raise TypeError("Can not modify attributes of immutable object")

    def __add__(self, other):
        if isinstance(other, _datetime.timedelta):
            days, sec = divmod(other.total_seconds() + self.s, 86400)
        else:
            raise TypeError("Unknown operation with {} type".format(type(other)))

        return self.__class__(self.d + int(days), sec, scale=self.scale)

    def __sub__(self, other):
        if isinstance(other, _datetime.timedelta):
            other = _datetime.timedelta(seconds=-other.total_seconds())
        elif isinstance(other, _datetime.datetime):
            return self.datetime - other
        elif isinstance(other, self.__class__):
            return self.datetime - other.datetime
        else:
            raise TypeError("Unknown operation with {} type".format(type(other)))

        return self.__add__(other)

    def __gt__(self, other):  # pragma: no cover
        return self.mjd > other.mjd

    def __ge__(self, other):  # pragma: no cover
        return self.mjd >= other.mjd

    def __lt__(self, other):  # pragma: no cover
        return self.mjd < other.mjd

    def __le__(self, other):  # pragma: no cover
        return self.mjd <= other.mjd

    def __eq__(self, other):  # pragma: no cover
        return self.d == other.d and self.s == other.s and self.scale == other.scale

    def __repr__(self):  # pragma: no cover
        return "<{} '{}'>".format(self.__class__.__name__, self)

    def __str__(self):  # pragma: no cover
        if 'str' not in self._cache.keys():
            self._cache['str'] = "{} {}".format(self.datetime.isoformat(), self.scale)
        return self._cache['str']

    def __format__(self, fmt):  # pragma: no cover
        if fmt:
            return self.datetime.__format__(fmt)
        else:
            return str(self)

    @classmethod
    def _convert_dt(cls, dt):
        tz = _datetime.timedelta(0) if dt.tzinfo is None else dt.utcoffset
        delta = dt - cls.MJD_T0 - tz
        return delta.days, delta.seconds + delta.microseconds * 1e-6

    @property
    def datetime(self):
        """Transform the Date object into a ``datetime.datetime`` object

        The resulting object is a timezone-naive instance with the same scale
        as the originating object.
        """

        if 'dt' not in self._cache.keys():
            self._cache['dt'] = self.MJD_T0 + _datetime.timedelta(days=self.d, seconds=self.s)
        return self._cache['dt']

    @classmethod
    def strptime(cls, data, format, scale='UTC'):  # pragma: no cover
        """Convert a string representation of a date to a Date object
        """
        return Date(_datetime.datetime.strptime(data, format), scale=scale)

    @classmethod
    def now(cls, scale="UTC"):
        """
        Args:
            scale (str)
        Return:
            Date: Current time in the choosen scale
        """
        return cls(_datetime.datetime.utcnow()).change_scale(scale)

    def change_scale(self, new_scale):
        result = self + self.scale.offset(self, new_scale)

        return Date(result.d, result.s, scale=new_scale)

    @property
    def julian_century(self):
        """Compute the julian_century of the Date object relatively to its
        scale

        Return:
            float
        """
        return (self.jd - 2451545.0) / 36525.

    @property
    def jd(self):
        """Compute the Julian Date, which is the number of days from the
        January 1, 4712 B.C., 12:00.

        Return:
            float
        """
        return self.d + self.JD_MJD + self.s / 86400.

    @property
    def mjd(self):
        """Date in terms of MJD

        Return:
            float
        """
        return self.d + self.s / 86400.
