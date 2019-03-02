# -*- coding: utf-8 -*-

"""Date module
"""

from datetime import datetime, timedelta, date
from numpy import sin, radians

from ..errors import DateError, UnknownScaleError
from .eop import EopDb
from ..utils.node import Node

__all__ = ['Date', 'timedelta']


class Timescale(Node):
    """Definition of a time scale and its interactions with others
    """

    def __repr__(self):  # pragma: no cover
        return "<Scale '%s'>" % self.name

    def __str__(self):
        return self.name

    def _scale_ut1_minus_utc(self, mjd, eop):
        """Definition of Universal Time relatively to Coordinated Universal Time
        """
        return eop.ut1_utc

    def _scale_tai_minus_utc(self, mjd, eop):
        """Definition of International Atomic Time relatively to Coordinated Universal Time
        """
        return eop.tai_utc

    def _scale_tt_minus_tai(self, mjd, eop):
        """Definition of Terrestrial Time relatively to International Atomic Time
        """
        return 32.184

    def _scale_tai_minus_gps(self, mjd, eop):
        """Definition of International Atomic Time relatively to GPS time
        """
        return 19.

    def _scale_tdb_minus_tt(self, mjd, eop):
        """Definition of the Barycentric Dynamic Time scale relatively to Terrestrial Time
        """
        jd = mjd + Date.JD_MJD
        jj = Date._julian_century(jd)
        m = radians(357.5277233 + 35999.05034 * jj)
        delta_lambda = radians(246.11 + 0.90251792 * (jd - 2451545.))
        return 0.001657 * sin(m) + 0.000022 * sin(delta_lambda)

    def offset(self, mjd, new_scale, eop):
        """Compute the offset necessary in order to convert from one time-scale to another

        Args:
            mjd (float):
            new_scale (str): Name of the desired scale
        Return:
            float: offset to apply in seconds
        """

        delta = 0
        for one, two in self.steps(new_scale):
            one = one.name.lower()
            two = two.name.lower()
            # find the operation
            oper = "_scale_{}_minus_{}".format(two, one)
            # find the reverse operation
            roper = "_scale_{}_minus_{}".format(one, two)
            if hasattr(self, oper):
                delta += getattr(self, oper)(mjd, eop)
            elif hasattr(self, roper):
                delta -= getattr(self, roper)(mjd, eop)
            else:  # pragma: no cover
                raise DateError("Unknown convertion {} => {}".format(one, two))

        return delta


UT1 = Timescale('UT1')  # Universal Time
GPS = Timescale('GPS')  # GPS Time
TDB = Timescale('TDB')  # Barycentric Dynamical Time
UTC = Timescale('UTC')  # Coordinated Universal Time
TAI = Timescale('TAI')  # International Atomic Time
TT = Timescale('TT')    # Terrestrial Time

GPS + TAI + UTC + UT1
TDB + TT + TAI


_cache = {
    "UT1": UT1,
    "GPS": GPS,
    "TDB": TDB,
    "UTC": UTC,
    "TAI": TAI,
    "TT": TT,
}


def get_scale(name):
    if name in _cache.keys():
        return _cache[name]
    else:
        raise UnknownScaleError(name)


class Date:
    """Date object

    All computations and in-memory saving are made in
    `MJD <https://en.wikipedia.org/wiki/Julian_day>`__ and
    `TAI <https://en.wikipedia.org/wiki/International_Atomic_Time>`__.
    In the current implementation, the Date object does not handle the
    leap second.

    The constructor can take:

        * the same arguments as the standard library's datetime object (year, month, day, hour,
          minute, second, microsecond)
        * MJD as :py:class:`float`
        * MJD as :py:class:`int` for days and :py:class:`float` for seconds
        * a :py:class:`Date` or :py:class:`datetime` object

    Keyword Arguments:
        scale (str) : One of the following scales : "UT1", "UTC", "GPS", "TDB", "TAI", "TT"

    Examples:

        .. code-block:: python

            Date(2016, 11, 17, 19, 16, 40)
            Date(2016, 11, 17, 19, 16, 40, scale="TAI")
            Date(57709.804455)  # MJD
            Date(57709, 69540.752649)
            Date(datetime(2016, 11, 17, 19, 16, 40))  # built-in datetime object
            Date.now()

    Date objects interact with :py:class:`timedelta` as datetime do.

    Attributes:
        eop: Value of the Earth Orientation Parameters for this particular date (see
            :ref:`eop`)
        scale: Scale in which this date is represented
    """

    __slots__ = ["_d", "_s", "_offset", "scale", "_cache", "eop"]

    MJD_T0 = datetime(1858, 11, 17)
    """Origin of MJD"""

    JD_MJD = 2400000.5
    """Offset between JD and MJD"""

    REF_SCALE = 'TAI'
    """Scale used as reference internally"""

    DEFAULT_SCALE = "UTC"
    """Default scale"""

    def __init__(self, *args, scale=DEFAULT_SCALE, **kwargs):

        if type(scale) is str:
            scale = get_scale(scale.upper())

        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, datetime):
                # Python datetime.datetime object
                d, s = self._convert_dt(arg)
            elif isinstance(arg, Date):
                # Date object
                d = arg.d
                s = arg.s
                scale = arg.scale
            elif isinstance(arg, (float, int)):
                # Modified Julian Day
                if isinstance(arg, int):
                    d = arg
                    s = 0.
                else:
                    d = int(arg)
                    s = (arg - d) * 86400
            else:
                raise TypeError("Unknown type '{}'".format(type(arg)))
        elif len(args) == 2 and (isinstance(args[0], int) and isinstance(args[1], (int, float))):
            # Julian day and seconds in the day
            d, s = args
        elif len(args) in range(3, 8) and list(map(type, args)) == [int] * len(args):
            # Same constructor as datetime.datetime
            # (year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
            dt = datetime(*args, **kwargs)
            d, s = self._convert_dt(dt)
        else:
            raise TypeError("Unknown type sequence {}".format(", ".join(str(type(x)) for x in args)))

        mjd = d + s / 86400.

        # Retrieve EOP for the given date and store
        eop = EopDb.get(mjd)

        # Retrieve the offset from REF_SCALE for the current date
        offset = scale.offset(mjd, self.REF_SCALE, eop)

        d += int((s + offset) // 86400)
        s = (s + offset) % 86400.

        # As Date acts like an immutable object, we can't set its attributes normally
        # like when we do ``self._d = _d``. Furthermore, those attribute represent the date with
        # respect to REF_SCALE
        super().__setattr__('_d', d)
        super().__setattr__('_s', s)
        super().__setattr__('_offset', offset)
        super().__setattr__('scale', scale)
        super().__setattr__('eop', eop)
        super().__setattr__('_cache', {})

    def __getstate__(self):  # pragma: no cover
        """Used for pickling"""
        return {
            'd': self._d,
            's': self._s,
            'offset': self._offset,
            'scale': self.scale,
            'eop': self.eop,
        }

    def __setstate__(self, state):  # pragma: no cover
        """Used for unpickling"""
        super().__setattr__('_d', state['d'])
        super().__setattr__('_s', state['s'])
        super().__setattr__('_offset', state['offset'])
        super().__setattr__('scale', state['scale'])
        super().__setattr__('eop', state['eop'])
        super().__setattr__('_cache', {})

    def __setattr__(self, *args):  # pragma: no cover
        raise TypeError("Can not modify attributes of immutable object")

    def __delattr__(self, *args):  # pragma: no cover
        raise TypeError("Can not modify attributes of immutable object")

    def __add__(self, other):
        if isinstance(other, timedelta):
            days, sec = divmod(other.total_seconds() + self.s, 86400)
        else:
            raise TypeError("Unknown operation with {}".format(type(other)))

        return self.__class__(self.d + int(days), sec, scale=self.scale)

    def __sub__(self, other):
        if isinstance(other, timedelta):
            other = timedelta(seconds=-other.total_seconds())
        elif isinstance(other, datetime):
            return self.datetime - other
        elif isinstance(other, Date):
            return self._datetime - other._datetime
        else:
            raise TypeError("Unknown operation with {}".format(type(other)))

        return self.__add__(other)

    def __gt__(self, other):
        return self._mjd > other._mjd

    def __ge__(self, other):
        return self._mjd >= other._mjd

    def __lt__(self, other):
        return self._mjd < other._mjd

    def __le__(self, other):
        return self._mjd <= other._mjd

    def __eq__(self, other):
        return self._mjd == other._mjd

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

    def __hash__(self):
        return hash((self._d, self._s))

    @classmethod
    def _convert_dt(cls, dt):
        if dt.tzinfo is None:
            delta = dt - cls.MJD_T0
        else:
            tz = dt.utcoffset()
            delta = dt.replace(tzinfo=None) - cls.MJD_T0 - tz

        return delta.days, delta.seconds + delta.microseconds * 1e-6

    def _convert_to_scale(self):
        """Convert the inner value (defined with respect to REF_SCALE) into the given scale
        of the object
        """
        d = self._d
        s = (self._s - self._offset) % 86400.
        d -= int((s + self._offset) // 86400)
        return d, s

    @property
    def d(self):
        return self._convert_to_scale()[0]

    @property
    def s(self):
        return self._convert_to_scale()[1]

    @property
    def datetime(self):
        """Conversion of the Date object into a ``datetime.datetime``

        The resulting object is a timezone-naive instance with the same scale
        as the originating Date object.
        """
        if 'dt_scale' not in self._cache.keys():
            self._cache['dt_scale'] = self._datetime - timedelta(seconds=self._offset)
        return self._cache['dt_scale']

    @property
    def _datetime(self):
        """Conversion of the Date object into a :py:class:`datetime.datetime`.

        The resulting object is a timezone-naive instance in the REF_SCALE time-scale
        """
        if 'dt' not in self._cache.keys():
            self._cache['dt'] = self.MJD_T0 + timedelta(days=self._d, seconds=self._s)
        return self._cache['dt']

    @classmethod
    def strptime(cls, data, format, scale=DEFAULT_SCALE):  # pragma: no cover
        """Convert a string representation of a date to a Date object
        """
        return cls(datetime.strptime(data, format), scale=scale)

    @classmethod
    def now(cls, scale=DEFAULT_SCALE):
        """
        Args:
            scale (str)
        Return:
            Date: Current time in the chosen scale
        """
        return cls(datetime.utcnow()).change_scale(scale)

    def strftime(self, fmt):  # pragma: no cover
        """Format the date following the given format
        """
        return self.datetime.strftime(fmt)

    def change_scale(self, new_scale):
        """
        Args:
            new_scale (str)
        Return:
            Date
        """
        offset = self.scale.offset(self._mjd, new_scale, self.eop)
        result = self.datetime + timedelta(seconds=offset)

        return self.__class__(result, scale=new_scale)

    @classmethod
    def _julian_century(cls, jd):
        return (jd - 2451545.0) / 36525.

    @property
    def julian_century(self):
        """Compute the julian_century of the Date object relatively to its
        scale

        Return:
            float
        """
        return self._julian_century(self.jd)

    @property
    def jd(self):
        """Compute the Julian Date, which is the number of days from the
        January 1, 4712 B.C., 12:00.

        Return:
            float
        """
        return self.mjd + self.JD_MJD

    @property
    def _mjd(self):
        """
        Return:
            float: Date in terms of MJD in the REF_SCALE timescale
        """
        return self._d + self._s / 86400.

    @property
    def mjd(self):
        """Date in terms of MJD

        Return:
            float
        """
        return self.d + self.s / 86400.

    @classmethod
    def range(cls, start=None, stop=None, step=None, inclusive=False):
        """Generator of a date range

        Args:
            start (Date):
            stop (Date or datetime.timedelta)!
            step (timedelta):
        Keyword Args:
            inclusive (bool): If ``False``, the stopping date is not included.
                This is the same behavior as the built-in :py:func:`range`.
        Yield:
            Date:
        """

        def sign(x):
            """Inner function for determining the sign of a float
            """
            return (-1, 1)[x >= 0]

        if not step:
            raise ValueError("Null step")

        # Convert stop from timedelta to Date object
        if isinstance(stop, timedelta):
            stop = start + stop

        if sign((stop - start).total_seconds()) != sign(step.total_seconds()):
            raise ValueError("start/stop order not coherent with step")

        date = start

        if step.total_seconds() > 0:
            oper = "__le__" if inclusive else "__lt__"
        else:
            oper = "__ge__" if inclusive else "__gt__"

        while getattr(date, oper)(stop):
            yield date
            date += step


# This part is here to allow matplotlib to display Date objects directly
# in the plot, without any other conversion by the developer
# If matplotlib is importable, then a converter class is registered
# for converting all Date objects on the fly
try:
    import matplotlib.dates as mdates
    import matplotlib.units as munits
except ImportError:  # pragma: no cover
    pass
else:  # pragma: no cover

    class DateConverter(mdates.DateConverter):

        @staticmethod
        def convert(values, unit, axis):
            try:
                iter(values)
            except TypeError:
                if isinstance(values, (datetime, date)):
                    values = mdates.date2num(values)
                else:
                    values = mdates.date2num(values.datetime)
            else:
                values = [mdates.date2num(v.datetime) for v in values]

            return values

    munits.registry.setdefault(Date, DateConverter())
