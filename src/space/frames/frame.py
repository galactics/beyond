#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from abc import abstractmethod

from space.constants import e_e, r_e
from space.utils.matrix import rot2, rot3
from space.utils.node import Node2
from space.frames import iau1980

CIO = ['ITRF', 'TIRF', 'CIRF', 'GCRF']
IAU1980 = ['TOD', 'MOD']
other = ['EME2000', 'TEME', 'WGS84', 'PEF', 'MODbis']
topo = ['Station', 'dynamic']

__all__ = CIO + IAU1980 + other + topo

dynamic = {}
"""For dynamically created Frames, such as ground stations
"""


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
            # print(_from, "=>", _to)
            try:
                matrix = getattr(_from(self.date, orbit), "_to_{}".format(_to))()
            except AttributeError:
                matrix = getattr(_to(self.date, orbit), "_to_{}".format(_from))().T
            orbit = matrix @ orbit

        return orbit[:6]


class TEME(_Frame):
    """True Equator Mean Equinox"""

    def _to_TOD(self):
        equin = iau1980.equinox(self.date, eop_correction=False, terms=4, kinematic=False)
        m = rot3(-np.deg2rad(equin))
        return self._convert(m, m)


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

    def _to_MODbis(self):
        m = iau1980.nutation(self.date)
        return self._convert(m, m)

    def _to_MOD(self):
        m = iau1980.nutation(self.date, eop_correction=False)
        return self._convert(m, m)

    def _to_PEF(self):
        m = iau1980.sideral(self.date, model='apparent', eop_correction=False)
        offset = np.identity(7)
        offset[3:6, -1] = - np.cross(iau1980.rate(self.date), self.orbit[:3])
        return self._convert(m, m).T @ offset


class MOD(_Frame):
    """Mean (Equator) Of Date"""

    def _to_EME2000(self):
        m = iau1980.precesion(self.date)
        return self._convert(m, m)

    def _to_TOD(self):
        m = iau1980.nutation(self.date, eop_correction=False)
        return self._convert(m, m).T


class MODbis(_Frame):
    """Mean (Equator) Of Date"""

    def _to_GCRF(self):
        m = iau1980.precesion(self.date)
        return self._convert(m, m)


class EME2000(_Frame):

    def _to_MOD(self):
        m = iau1980.precesion(self.date)
        return self._convert(m, m).T


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


def Station(name, latlonalt, parent_frame):

    def _geodetic_to_xyz(lat, lon, alt):

        C = r_e / np.sqrt(1 - (e_e * np.sin(lat)) ** 2)
        S = r_e * (1 - e_e ** 2) / np.sqrt(1 - (e_e * np.sin(lat)) ** 2)
        r_d = (C + alt) * np.cos(lat)
        r_k = (S + alt) * np.sin(lat)

        norm = np.sqrt(r_d ** 2 + r_k ** 2)
        return norm * np.array([
            np.cos(lat) * np.cos(lon),
            np.cos(lat) * np.sin(lon),
            np.sin(lat)
        ])

    latlonalt = list(latlonalt)
    latlonalt[:2] = np.radians(latlonalt[:2])
    coordinates = _geodetic_to_xyz(*latlonalt)

    def _convert(self):
        lat, lon, _ = latlonalt
        m = rot2(np.pi / 2. - lat) @ rot3(lon)
        offset = np.identity(7)
        offset[0:3, -1] = - coordinates
        return (self._convert(m, m) @ offset).T

    mtd = '_to_%s' % parent_frame.__name__
    dct = {
        mtd: _convert,
        'latlonalt': latlonalt,
        'coordinates': coordinates
    }
    cls = _MetaFrame(name, (_Frame,), dct)
    cls + parent_frame
    dynamic[name] = cls

    return cls


ITRF + PEF + TOD + MOD + EME2000
TOD + MODbis + GCRF
TOD + TEME
EME2000 + GCRF
# ITRF + TopocentricFrame
#ITRF + TIRF + CIRF + GCRF