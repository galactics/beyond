# -*- coding: utf-8 -*-

import datetime as _datetime

from space.frames.poleandtimes import TimeScales


class Time:
    """Time object

    """

    __slots__ = ["_d", "_s", "_scale"]

    SCALES = ('UTC', 'UT1', 'TAI', 'TT')
    MJD_T0 = _datetime.datetime(1858, 11, 17)
    TT_TAI = 32.184  # TT - TAI (seconds)

    def __init__(self, *args, **kwargs):

        if 'scale' in kwargs:
            if kwargs['scale'].upper() in self.SCALES:
                self._scale = kwargs['scale'].upper()
            else:
                raise ValueError("Scale {} unknown".format(kwargs['scale']))
        else:
            self._scale = 'UTC'

        if len(args) == 1:
            if type(args[0]) is _datetime.datetime:
                self._d, self._s = self._convert_dt(args[0])
            elif type(args[0]) is self.__class__:
                self._d, self._s = args[0].d, args[0].s
        elif len(args) == 2 and (type(args[0]) == int and type(args[1]) in (int, float)):
            self._d, self._s = args
        elif len(args) in range(3, 8) and list(map(type, args)) == [int] * len(args):
            dt = _datetime.datetime(*args)
            self._d, self._s = self._convert_dt(dt)
        else:
            raise Exception("AAAArrrgghh")

    @property
    def d(self):
        return self._d

    @property
    def s(self):
        return self._s

    @property
    def scale(self):
        return self._scale

    @property
    def datetime(self):
        """Transform the Time object into a ``datetime.datetime`` object

        The resulting object is a timezone-naive instance with the same scale
        as the originating object.
        """
        return self.MJD_T0 + _datetime.timedelta(days=self._d, seconds=self._s)

    def change_scale(self, scale):
        scale = scale.upper()
        if scale == self.scale:
            return self

        if scale not in self.SCALES:
            raise ValueError("Scale {} unknown".format(scale))

        ut1_tai, ut1_utc, tai_utc = [_datetime.timedelta(seconds=x) for x in TimeScales.get(self.datetime)]

        if self.scale == 'UTC':
            if scale == 'UT1':
                delta = ut1_utc
            elif scale == 'TAI':
                delta = tai_utc
            elif scale == 'TT':
                delta = tai_utc + _datetime.timedelta(seconds=self.TT_TAI)

        new = self + delta
        new._scale = scale
        # return self.__class__(new.d, new.s, scale=scale)
        return new

    @classmethod
    def _convert_dt(cls, dt):
        delta = dt - cls.MJD_T0
        return delta.days, delta.seconds + delta.microseconds * 1e-6

    def __add__(self, other):
        if type(other) is float:
            # number of days
            days = int(other)
            sec = (other - days) / 86400.
        elif type(other) is _datetime.timedelta:
            days, sec = divmod(other.total_seconds() + self._s, 86400)
        return self.__class__(self._d + int(days), sec, scale=self.scale)

    def __str__(self):
        return "{} {}".format(self.datetime, self.scale)


class TestDatetime(_datetime.datetime):

    _scale = 'UTC'

    SCALES = ('UTC', 'UT1', 'TAI', 'TT')
    TT_TAI = 32.184  # TT - TAI (seconds)

    def __new__(cls, *args, **kwargs):

        scale = kwargs.pop('scale', False)
        obj = super().__new__(cls, *args, **kwargs)

        if scale:
            obj._scale = scale.upper()

        return obj

    @classmethod
    def _convert(cls, d, scale='UTC'):
        return cls(d.year, d.month, d.day, d.hour, d.minute, d.second, d.microsecond, scale=scale)

    def __str__(self):
        return "{} {}".format(super().__str__(), self.scale())

    def scale(self, value=None):

        if value is None:
            return self._scale
        else:
            value = value.upper()
            if value == self._scale:
                return self
            else:

                if value not in self.SCALES:
                    raise ValueError("")

                ut1_tai, ut1_utc, tai_utc = [_datetime.timedelta(seconds=x) for x in TimeScales.get(super())]

                if value == 'UT1':
                    delta = ut1_utc
                elif value == 'TAI':
                    delta = tai_utc
                elif value == 'TT':
                    delta = tai_utc + _datetime.timedelta(seconds=self.TT_TAI)
                else:
                    ValueError("")

                return self._convert(self + delta, scale=value)

    def julian_century(self):
        return (self.jd(self) - 2451545.0) / 36525.

    def t_tt(self):
        """Transform to Julian Century (T_TT)

        Example:
            >>> import datetime
            >>> t_tt(datetime.datetime(2004, 4, 6, 7, 51, 28, 386009))
            0.04262363188899416
        """
        tai = self + _datetime.timedelta(seconds=TimeScales.get(self).tai_utc)
        tt = tai + _datetime.timedelta(seconds=self.TT_TAI)
        return self.julian_century(tt)

    def change_scale(self, to):
        """Change the time scale used for a datetime object
        Args:
            to (str): The time scale to convert to
        Return:
            datetime
        """

    def jd(self):
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
        seconds = self.second + self.microsecond / 1e6

        leap = 60
        year, month = self.year, self.month
        if self.month in (1, 2):
            year -= 1
            month += 12
        B = 2 - year // 100 + year // 100 // 4
        C = ((seconds / leap + self.minute) / 60 + self.hour) / 24
        return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + self.day + B - 1524.5 + C

    def __add__(self, other):
        return self._convert(super().__add__(other))

    def __radd__(self, other):
        return self._convert(super().__radd__(other))

    # def __sub__(self, other):
    #     return self._convert(super().__sub__(other))

    # def __rsub__(self, other):
    #     return self._convert(super().__rsub__(other))
