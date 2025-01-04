from abc import ABCMeta, abstractmethod
from collections import UserList


class MeasureSet(UserList):
    @property
    def start(self):
        return self[0].date

    @property
    def stop(self):
        return self[-1].date

    @property
    def dates(self):
        return list({x.date: None for x in self}.keys())

    @property
    def all_dates(self):
        return [x.date for x in self]

    @property
    def types(self):
        return list({x.__class__.__name__: None for x in self}.keys())

    @property
    def sources(self):
        return list({x.frame: None for x in self}.keys())

    @property
    def paths(self):
        return list({x.path: None for x in self if hasattr(x, "path")}.keys())

    def sort(self, **kwargs):
        kwargs.setdefault("key", lambda x: x.date)
        return super().sort(**kwargs)

    def filter(self, *, type=None, src=None, path=None):
        mes = []
        for m in self:
            if (
                None not in (type, src, path)
                and m.type == type
                and m.frame == src
                and m.path == path
            ):
                mes.append(m)
            elif type is not None and m.type == type:
                mes.append(m)
            elif src is not None and m.frame == src:
                mes.append(m)
            elif path is not None and m.path == path:
                mes.append(m)

        return self.__class__(mes)


class Residual:
    def __init__(self, frame, date, value):
        self.frame = frame
        self.date = date
        self.value = value

    def __add__(self, other):
        v = other.value if isinstance(other, Residual) else other
        return self.value + v

    def __radd__(self, other):
        v = other.value if isinstance(other, Residual) else other
        return self.value + v

    def __sub__(self, other):
        v = other.value if isinstance(other, Residual) else other
        return self.value - v

    def __rsub__(self, other):
        v = other.value if isinstance(other, Residual) else other
        return v - self.value


class Measure(metaclass=ABCMeta):
    def __init__(self, date, value):
        self.date = date
        self.value = value

    @abstractmethod
    def from_orbit(self, orb):
        pass

    @property
    def type(self):
        return self.__class__.__name__

    def __sub__(self, other):
        if self.__class__ != other.__class__:
            raise TypeError(
                "Impossible to compute residuals for different measures types {} != {}".format(
                    self.__class__, other.__class__
                )
            )

        if self.date != other.date:
            raise ValueError("Unmatched dates")

        if self.frame != other.frame:
            raise ValueError("Unmatched frames")

        return Residual(self.frame, self.date, self.value - other.value)


class StationMeasure(Measure):
    def __init__(self, path, date, value):
        super().__init__(date, value)
        self.path = tuple(path)

    @property
    def frame(self):
        return self.path[0]


class Azimut(StationMeasure):
    def from_orbit(self, orb):
        return self.__class__(
            self.path, orb.date, orb.copy(frame=self.frame, form="spherical").theta
        )


class Elevation(StationMeasure):
    def from_orbit(self, orb):
        return self.__class__(
            self.path, orb.date, orb.copy(frame=self.frame, form="spherical").phi
        )


class Range(StationMeasure):
    def from_orbit(self, orb):
        return self.__class__(
            self.path,
            orb.date,
            orb.copy(frame=self.frame, form="spherical").r * (len(self.path) - 1),
        )


class Doppler(StationMeasure):
    def from_orbit(self, orb):
        return self.__class__(
            self.path, orb.date, orb.copy(frame=self.frame, form="spherical").r_dot
        )


class PVT(Measure):
    def __init__(self, frame, date, value):
        self.frame = frame
        self.date = date
        self.value = value

    def from_orbit(self, orb):
        orb = orb.copy(frame=self.frame, form="cartesian")
        attr = self.__class__.__name__.lower()
        value = getattr(orb, attr)
        return self.__class__(self.frame, self.date, value)

    def residual(self, ref):
        name = f"Residual{self.__class__.__name__}"
        dct = {"type": self.__class__.__name__}
        klass = type(name, (Residual,), dct)

        return klass(self.frame, self.date, self.value - ref.value)


class X(PVT):
    pass


class Y(PVT):
    pass


class Z(PVT):
    pass


class Vx(PVT):
    pass


class Vy(PVT):
    pass


class Vz(PVT):
    pass
