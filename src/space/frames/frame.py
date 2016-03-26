#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module define the Frames available for computation and their relations
to each other.

The relations may be circular, thanks to the use of the Node2 class.

.. code-block:: text

    The dotted relations are not implemented yet.

       ,-------.
       |EME2000|
       `-------'
       /      :
      /       :
    ,---.   ,----.
    |MOD|   |GCRF|
    `---'   `----'
      |       :
    ,---.   ,----.
    |TOD|   |CIRF|
    `---'   `----'
      |       :
    ,---.   ,----.   ,-----.
    |PEF|   |TIRF|   |WGS84|
    `--- \  `----'  /`-----'
      |   \   :    /
    ,----. \,----./
    |TEME|  |ITRF|
    `----'  `----'
"""

import numpy as np
from abc import abstractmethod
from datetime import timedelta

from space.constants import e_e, r_e
from space.utils.matrix import rot2, rot3
from space.utils.node import Node2
from space.frames import iau1980

CIO = ['ITRF', 'TIRF', 'CIRF', 'GCRF']
IAU1980 = ['TOD', 'MOD']
other = ['EME2000', 'TEME', 'WGS84', 'PEF']
topo = ['Station', 'dynamic']

__all__ = CIO + IAU1980 + other + topo + ['get_frame']

dynamic = {}
"""For dynamically created Frames, such as ground stations
"""


def get_frame(frame):
    """Frame factory

    Args:
        frame (str): name of the desired frame
    Return:
        ~space.frames.frame._Frame
    """
    if frame in __all__:
        return eval(frame)
    elif frame in dynamic.keys():
        return dynamic[frame]
    else:
        raise ValueError("Unknown Frame : '{}'".format(frame))


class _MetaFrame(type, Node2):
    """This MetaClass is here to join the behaviours of ``type`` and ``Node2``
    """
    def __init__(self, name, bases, dct):
        super(_MetaFrame, self).__init__(name, bases, dct)
        super(type, self).__init__(name)

    def __repr__(self):
        return "<Frame '{}'>".format(self.name)


class _Frame(metaclass=_MetaFrame):
    """Frame base class
    """

    def __init__(self, date, orbit):
        """
        Args:
            date (~space.utils.Date)
            orbit (numpy.ndarray)
        """
        self.date = date
        self.orbit = orbit

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Frame obj '{}'>".format(self.__class__.__name__)

    @classmethod
    def _convert(cls, x=None, y=None):
        x = np.identity(3) if x is None else x
        y = np.identity(3) if y is None else y

        m = np.identity(7)
        m[:3, :3] = x
        m[3:6, 3:6] = y
        return m

    def transform(self, new_frame):
        """Change the frame of the orbit

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
                rotation, offset = getattr(_from(self.date, orbit), "_to_{}".format(_to))()
            except AttributeError:
                rotation, offset = getattr(_to(self.date, orbit), "_to_{}".format(_from))()
                rotation = rotation.T
                offset[:6, -1] = - offset[:6, -1]
            orbit = rotation @ offset @ orbit

        return orbit[:6]


class TEME(_Frame):
    """True Equator Mean Equinox"""

    def _to_TOD(self):
        equin = iau1980.equinox(self.date, eop_correction=False, terms=4, kinematic=False)
        m = rot3(-np.deg2rad(equin))
        return self._convert(m, m), np.identity(7)


class GTOD(_Frame):
    """Greenwich True Of Date"""
    pass


class WGS84(_Frame):
    """World Geodetic System 1984"""

    def _to_ITRF(self):
        return np.identity(7), np.identity(7)


class PEF(_Frame):
    """Pseudo Earth Fixed"""

    def _to_TOD(self):
        m = iau1980.sideral(self.date, model='apparent', eop_correction=False)
        offset = np.identity(7)
        offset[3:6, -1] = np.cross(iau1980.rate(self.date), self.orbit[:3])
        return self._convert(m, m), offset


class TOD(_Frame):
    """True (Equator) Of Date"""

    def _to_MOD(self):
        m = iau1980.nutation(self.date, eop_correction=False)
        return self._convert(m, m), np.identity(7)


class MOD(_Frame):
    """Mean (Equator) Of Date"""

    def _to_EME2000(self):
        m = iau1980.precesion(self.date)
        return self._convert(m, m), np.identity(7)


class EME2000(_Frame):
    pass


class ITRF(_Frame):
    """International Terrestrial Reference Frame"""

    def _to_PEF(self):
        m = iau1980.pole_motion(self.date)
        return self._convert(m, m), np.identity(7)


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

    @classmethod
    def visibility(cls, orb, start, stop, step, events=False):
        """Visibility from a topocentric frame
        """

        if type(stop) is timedelta:
            stop = start + stop

        date = start
        visibility, max_found = False, False
        previous = cls._vis(orb, date)
        while date < stop:
            cursor = cls._vis(orb, date)
            if cursor.phi >= 0:

                if events and not visibility:
                    aos = cls._bisect(orb, date - step, date)
                    aos.info = "AOS"
                    yield aos
                    visibility = True

                if events and cursor.r_dot >= 0 and not max_found:
                    _max = cls._bisect(orb, date - step, date, 'r_dot')
                    _max.info = "MAX"
                    yield _max
                    max_found = True

                cursor.info = ""
                yield cursor
            elif events and visibility:
                los = cls._bisect(orb, date - step, date)
                los.info = "LOS"
                yield los
                visibility, max_found = False, False
            previous = cursor
            date += step

    @classmethod
    def _vis(cls, orb, date):
        orb = orb.propagate(date)
        orb.change_frame(cls.__name__)
        orb.change_form('spherical')

        return orb
    @classmethod
    def _bisect(cls, orb, start, stop, element='phi'):

        MAX = 50
        n = 0

        get = lambda x: getattr(x, element)
        eps = 1e-4 if element == 'phi' else 1e-3

        step = (stop - start) / 2
        prev_value = cls._vis(orb, start)
        date = start
        while n <= MAX and date <= stop:
            date = start + step
            value = cls._vis(orb, date)
            if -eps < get(value) <= eps:
                return value
            elif np.sign(get(value)) == np.sign(get(prev_value)):
                prev_value = value
                start = date
            else:
                step /= 2
            n += 1
        else:
            if n > MAX:
                raise RuntimeError('Too much iterations : %d' % n)
            else:
                raise RuntimeError('Time limit exceeded : {:%H:%M:%S:%f} >= {:%H:%M:%S}'.format(date, stop))


def Station(name, latlonalt, parent_frame=WGS84):
    """Create a ground station instance

    Args:
        name (str): Name of the station
        latlonalt (tuple of float): coordinates of the station
        parent_frame (_Frame): Planetocentric rotating frame of reference of coordinates.
    Return:
        TopocentricFrame
    """

    def _geodetic_to_xyz(lat, lon, alt):
        """Conversion from latitude, longitue and altitude coordinates to
        cartesian with respect to an ellipsoid

        Args:
            lat (float): Latitude in radians
            lon (float): Longitue in radians
            alt (float): Altitude to sea level in meters

        Return:
            numpy.array: 3D element (in meters)
        """
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
        """Conversion from Topocentric Frame to parent frame
        """
        lat, lon, _ = self.latlonalt
        m = rot3(-lon) @ rot2(lat - np.pi / 2.)
        offset = np.identity(7)
        offset[0:3, -1] = self.coordinates
        return self._convert(m, m), offset

    mtd = '_to_%s' % parent_frame.__name__
    dct = {
        mtd: _convert,
        'latlonalt': latlonalt,
        'coordinates': coordinates,
        'parent_frame': parent_frame,
    }
    cls = _MetaFrame(name, (TopocentricFrame,), dct)
    cls + parent_frame
    dynamic[name] = cls

    return cls


WGS84 + ITRF + PEF + TOD + MOD + EME2000
TOD + TEME
# EME2000 + GCRF
#ITRF + TIRF + CIRF + GCRF