# -*- coding: utf-8 -*-

import datetime as _datetime

from space.frames.poleandtimes import TimeScales


class Date:
    """Date object

    All computations and in-memory saving are made in
    <MJD `https://en.wikipedia.org/wiki/Julian_day`>.

    In the current implementation, the Date object does not handle the
    leap second.
    """

    __slots__ = ["d", "s", "scale", "_cache"]

    SCALES = ('UTC', 'TAI', 'TT')
    MJD_T0 = _datetime.datetime(1858, 11, 17)
    TT_TAI = _datetime.timedelta(seconds=32.184)  # TT - TAI

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

    def __setattr__(self, *args):
        raise TypeError("Can not modify attributes of immutable object")

    def __delattr__(self, *args):
        raise TypeError("Can not modify attributes of immutable object")

    def __add__(self, other):
        if type(other) is float:
            # number of days
            days = int(other)
            sec = (other - days) / 86400.
        elif type(other) is _datetime.timedelta:
            days, sec = divmod(other.total_seconds() + self.s, 86400)
        return self.__class__(self.d + int(days), sec, scale=self.scale)

    def __str__(self):
        if 'str' not in self._cache.keys():
            self._cache['str'] = "{} {}".format(self.datetime.isoformat(), self.scale)
        return self._cache['str']

    @classmethod
    def _convert_dt(cls, dt):
        # TODO: Handle timezone aware datetime objects (ie: convert to UTC)
        delta = dt - cls.MJD_T0
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
    def now(cls, scale="UTC"):
        return cls(_datetime.datetime.now(), scale=scale)

    def change_scale(self, scale):
        """Create an object representing the same time as ``self`` but in a
        different scale
        """
        scale = scale.upper()
        if scale == self.scale:
            return self

        if scale not in self.SCALES:
            raise ValueError("Scale {} unknown".format(scale))

        ut1_tai, ut1_utc, tai_utc = [_datetime.timedelta(seconds=x) for x in TimeScales.get(self.datetime)]

        if self.scale == 'UTC':
            delta = tai_utc
            if scale == 'TT':
                delta += tai_utc + self.TT_TAI
        if self.scale == 'TAI':
            if scale == 'UTC':
                delta = - tai_utc
            elif scale == 'TT':
                delta = self.TT_TAI
        if self.scale == 'TT':
            delta = - self.TT_TAI
            if scale == "UTC":
                delta -= tai_utc

        new = self + delta
        return self.__class__(new.d, new.s, scale=scale)

    @property
    def julian_century(self):
        return (self.jd - 2451545.0) / 36525.

    @property
    def jd(self):
        """Compute the Julian Date, which is the number of days from the
        January 1, 4712 B.C., 12:00.

        Return:
            float
        """
        return self.d + 2400000.5 + self.s / 86400.
