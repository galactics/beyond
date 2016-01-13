#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from space.utils.matrix import rot3
from space.utils.node import Node2
from space.frames import iau1980

CIO = ['ITRF', 'TIRF', 'CIRF', 'GCRF']
IAU1980 = ['TOD', 'MOD']

__all__ = CIO + IAU1980 + ['EME2000', 'TEME', 'WGS84', 'PEF']


class _MetaFrame(type, Node2):
    def __init__(self, name, bases, dct):
        super(_MetaFrame, self).__init__(name, bases, dct)
        super(type, self).__init__(name)

    def __repr__(self):
        return "<Frame '{}'>".format(self.name)


class _Frame(metaclass=_MetaFrame):

    def __init__(self, date, orbit):
        self.date = date
        self.orbit = orbit

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Frame '{}'>".format(self.__class__.__name__)

    @classmethod
    def _convert(cls, x=None, y=None):
        x = np.identity(3) if x is None else x
        y = np.identity(3) if y is None else y

        m = np.identity(7)
        m[:3, :3] = x
        m[3:6, 3:6] = y
        return m

    def transform(self, new_frame):
        """Change the frame of the given orbit

        Args:
            new_frame (str)
        Return:
            numpy.ndarray
        """
        steps = self.__class__.steps(new_frame)

        orbit = np.ones(7)
        orbit[:6] = self.orbit
        for _from, _to in steps:
            matrix = getattr(_from(self.date, orbit), "_to_{}".format(_to))()
            orbit = matrix @ orbit

        return orbit[:6]


class TEME(_Frame):
    """True Equator Mean Equinox"""

    def _to_TOD(self):
        equin = iau1980.equinox(self.date, eop_correction=False, terms=4, kinematic=False)
        m = rot3(-np.deg2rad(equin))
        return self._convert(m, m)

    def _to_PEF(self):
        sid = iau1980.sideral(self.date)
        return self._convert(sid, sid)


class GTOD(_Frame):
    """Greenwich True Of Date"""
    pass


class WGS84(_Frame):
    """World Geodetic System 1984"""
    pass


class PEF(_Frame):
    """Pseudo Earth Fixed"""

    def _to_TOD(self):
        m = iau1980.sideral(self.date, model='apparent', eop_correction=False)
        offset = np.identity(7)
        offset[3:6, -1] = np.cross(iau1980.rate(self.date), self.orbit[:3])
        return self._convert(m, m) @ offset

    def _to_ITRF(self):
        m = iau1980.pole_motion(self.date)
        return self._convert(m.T, m.T)

class TOD(_Frame):
    """True (Equator) Of Date"""

    def _to_MOD(self):
        m = iau1980.nutation(self.date)
        return self._convert(m, m)

    def _to_PEF(self):
        m = iau1980.sideral(self.date, model='apparent', eop_correction=False)
        offset = np.identity(7)
        offset[3:6, -1] = - np.cross(iau1980.rate(self.date), self.orbit[:3])
        return self._convert(m, m).T @ offset


class MOD(_Frame):
    """Mean (Equator) Of Date"""
    def _to_GCRF(self):
        m = iau1980.precesion(self.date)
        return self._convert(m, m)


class EME2000(_Frame):
    pass


class ITRF(_Frame):
    """International Terrestrial Reference Frame"""

    def _to_PEF(self):
        m = iau1980.pole_motion(self.date)
        return self._convert(m, m)


class TIRF(_Frame):
    """Terrestrial Intermediate Reference Frame"""
    pass


class CIRF(_Frame):
    """Celestial Intermediate Reference Frame"""
    pass


class GCRF(_Frame):
    """Geocentric Celestial Reference Frame"""
    pass


class TopocentricFrame(_Frame):

    def __new__(cls, name, coordinates, parent_frame):

        obj = super().__new__(name, coordinates, parent_frame)
        self.name = name
        self.coordinates = coordinates
        parent_frame + self


ITRF + PEF + TOD + MOD + EME2000
MOD + GCRF
TOD + TEME + PEF
ITRF + TIRF + CIRF + GCRF