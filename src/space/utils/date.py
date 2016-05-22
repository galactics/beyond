# -*- coding: utf-8 -*-

import datetime as _datetime

from space.env.poleandtimes import TimeScales
from .node import Node

__all__ = ['Date']


class _Scale(Node):
    pass


class Date:
    """Date object

    All computations and in-memory saving are made in
    `MJD <https://en.wikipedia.org/wiki/Julian_day>`__.

    In the current implementation, the Date object does not handle the
    leap second.
    """

    __slots__ = ["d", "s", "scale", "_cache"]

    MJD_T0 = _datetime.datetime(1858, 11, 17)

    UT1 = _Scale('UT1')
    GPS = _Scale('GPS')
    UTC = _Scale('UTC', [UT1])
    TAI = _Scale('TAI', [UTC, GPS])
    TT = _Scale('TT', [TAI])

    # Used to find the relations between scales, also contains
    # the list of all scales
    SCALES = TT

    def __init__(self, *args, **kwargs):

        if 'scale' in kwargs:
            if kwargs['scale'].upper() in self.SCALES:
                scale = kwargs['scale'].upper()
            else:
                raise ValueError("Scale {} unknown".format(kwargs['scale']))
        else:
            scale = 'UTC'

        if len(args) == 1:
            arg = args[0]
            if type(arg) is _datetime.datetime:
                # Python datetime.datetime object
                d, s = self._convert_dt(arg)
            elif type(arg) is self.__class__:
                # Date object
                d = arg.d
                s = arg.s
                scale = arg.scale
            elif type(arg) in (float, int):
                # Julian Day
                if type(arg) is int:
                    d = arg
                    s = 0.
                else:
                    d = int(arg)
                    s = (arg - d) * 86400
            else:
                raise TypeError("Unknown argument")
        elif len(args) == 2 and (type(args[0]) == int and type(args[1]) in (int, float)):
            # Julian day and seconds in the day
            d, s = args
        elif len(args) in range(3, 8) and list(map(type, args)) == [int] * len(args):
            # Same constructor as datetime.datetime
            # (year, month, day[, hour[, minute[, second[, microsecond]]]])
            dt = _datetime.datetime(*args)
            d, s = self._convert_dt(dt)
        else:
            raise ValueError("Unknown arguments")

        super().__setattr__('d', d)
        super().__setattr__('s', s)
        super().__setattr__('scale', scale)
        super().__setattr__('_cache', {})

    def __setattr__(self, *args):  # pragma: no cover
        raise TypeError("Can not modify attributes of immutable object")

    def __delattr__(self, *args):  # pragma: no cover
        raise TypeError("Can not modify attributes of immutable object")

    def __add__(self, other):
        if type(other) is _datetime.timedelta:
            days, sec = divmod(other.total_seconds() + self.s, 86400)
        else:
            raise TypeError("Unknown operation with {} type".format(type(other)))

        return self.__class__(self.d + int(days), sec, scale=self.scale)

    def __sub__(self, other):
        if type(other) is _datetime.timedelta:
            other = _datetime.timedelta(seconds=-other.total_seconds())
        elif type(other) is _datetime.datetime:
            return self.datetime - other
        elif type(other) is self.__class__:
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

    def _scale_ut1_minus_utc(self):
        ut1_tai, ut1_utc, tai_utc = TimeScales.get(self.mjd)
        return ut1_utc

    def _scale_tai_minus_utc(self):
        ut1_tai, ut1_utc, tai_utc = TimeScales.get(self.mjd)
        return tai_utc

    def _scale_tt_minus_tai(self):
        return 32.184

    def _scale_tai_minus_gps(self):
        return 19.

    def change_scale(self, new_scale):
        """Create an object representing the same time as ``self`` but in a
        different scale

        Args:
            new_scale (str)
        Return:
            Date
        """

        delta = 0
        for one, two in self.SCALES.steps(self.scale, new_scale):
            one = one.name.lower()
            two = two.name.lower()
            # find the operation
            oper = "_scale_{}_minus_{}".format(two, one)
            # find the reverse operation
            roper = "_scale_{}_minus_{}".format(one, two)
            if hasattr(self, oper):
                delta += getattr(self, oper)()
            elif hasattr(self, roper):
                delta -= getattr(self, roper)()
            else:  # pragma: no cover
                raise ValueError("Unknown convertion {} => {}".format(one, two))

        delta = _datetime.timedelta(seconds=delta)
        result = self + delta

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
        return self.d + 2400000.5 + self.s / 86400.

    @property
    def mjd(self):
        """Date in terms of MJD

        Return:
            float
        """
        return self.d + self.s / 86400.
