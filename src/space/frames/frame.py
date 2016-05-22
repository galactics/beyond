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

import warnings
import numpy as np
from datetime import timedelta

from space.constants import e_e, r_e
from space.utils.matrix import rot2, rot3
from space.utils.node import Node2
from space.frames import iau1980

CIO = ['ITRF', 'TIRF', 'CIRF', 'GCRF']
IAU1980 = ['TOD', 'MOD']
other = ['EME2000', 'TEME', 'WGS84', 'PEF']
topo = ['create_station']

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
    if frame in dynamic.keys():
        return dynamic[frame]
    else:
        raise ValueError("Unknown Frame : '{}'".format(frame))


class _MetaFrame(type, Node2):
    """This MetaClass is here to join the behaviours of ``type`` and ``Node2``
    """

    def __init__(self, name, bases, dct):
        super(_MetaFrame, self).__init__(name, bases, dct)
        super(type, self).__init__(name)

        if self.__name__ in dynamic:
            warnings.warn("A frame with the name '%s' is already registered. Overriding" % self.__name__)

        # Making the frame available to the get_frame function
        dynamic[self.__name__] = self

    def __repr__(self):  # pragma: no cover
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

    def __str__(self):  # pragma: no cover
        return self.name

    def __repr__(self):  # pragma: no cover
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

            try:
                rotation, offset = getattr(_from(self.date, orbit), "_to_{}".format(_to))()
            except AttributeError:
                rotation, offset = getattr(_to(self.date, orbit), "_to_{}".format(_from))()
                rotation = rotation.T
                offset[:6, -1] = - offset[:6, -1]
            if issubclass(_from, TopocentricFrame):
                orbit = offset @ rotation @ orbit
            else:
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
    """Base class for ground station
    """

    @classmethod
    def visibility(cls, orb, start, stop, step, events=False):
        """Visibility from a topocentric frame

        Args:
            orb (Orbit): Orbit to compute visibility from the station with
            start (Date): starting date of the visibility search
            stop (Date or datetime.timedelta) end of the visibility search
            step (datetime.timedelta): step of the computation
            events (bool): If True, compute AOS, LOS and MAX elevation for
                each pass

        Yield:
            Orbit: In-visibility point of the orbit. This Orbit is already
            in the frame of the station and in spherical form.
        """

        if type(stop) is timedelta:
            stop = start + stop

        date = start
        visibility, max_found = False, False

        while date < stop:

            # Propagate orbit at the current date, and convert it to the station
            # frame and spherical form
            cursor = cls._vis(orb, date)

            # If the elevation is positive we have the satellite in visibility
            if cursor.phi >= 0:

                if events and not visibility and date != start:
                    # The date condition is there to discard the computation
                    # of AOS if the computation starts during a pass
                    aos = cls._bisect(orb, date - step, date)
                    aos.info = "AOS"
                    yield aos

                visibility = True

                if events and cursor.r_dot >= 0 and not max_found:
                    if date != start:
                        # If we start to compute after the MAX elevation, the
                        # current _bisect algorithm can't detect it and will
                        # raise an exception, so we discard this case
                        _max = cls._bisect(orb, date - step, date, 'r_dot')
                        _max.info = "MAX"
                        yield _max
                    max_found = True

                cursor.info = ""
                yield cursor
            elif events and visibility:
                # If a visibility has started, and the satellite is below the
                # horizon, we can compute the LOS
                los = cls._bisect(orb, date - step, date)
                los.info = "LOS"
                yield los

                # Re-initialization of pass variables
                visibility, max_found = False, False

            date += step

    @classmethod
    def _vis(cls, orb, date):
        """shortcut to onvert orb to topocentric frame in spherical form at a
        given date
        """
        orb = orb.propagate(date)
        orb.change_frame(cls.__name__)
        orb.change_form('spherical')

        return orb

    @classmethod
    def _bisect(cls, orb, start, stop, element='phi'):
        """Find, between two dates, the zero-crossing of an orbit parameter

        Args:
            orb (Orbit)
            start (Date)
            stop (Date)
            element (str)
        Return:
            Orbit
        """

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
        else:  # pragma: no cover
            # Hopefully this part is never executed
            if n > MAX:
                raise RuntimeError('Too much iterations : %d' % n)
            else:
                # If you arrive her it's certainly because there was no zero
                # crossing between the two dates
                raise RuntimeError('Time limit exceeded : {:%H:%M:%S:%f} >= {:%H:%M:%S}'.format(date, stop))


def create_station(name, latlonalt, parent_frame=WGS84, orientation='N'):
    """Create a ground station instance

    Args:
        name (str): Name of the station

        latlonalt (tuple of float): coordinates of the station, as follow:

            * Latitude in radians
            * Longitude in radians
            * Altitude to sea level in meters

        parent_frame (_Frame): Planetocentric rotating frame of reference of
            coordinates.
        orientation (str or float): Heading of the station
            Acceptables values are 'N', 'S', 'E', 'W' or any angle in radians

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

    if type(orientation) is str:
        orient = {'N': np.pi, 'S': 0., 'E': np.pi / 2., 'W': 3 * np.pi / 2.}
        orientation = orient[orientation]

    latlonalt = list(latlonalt)
    latlonalt[:2] = np.radians(latlonalt[:2])
    coordinates = _geodetic_to_xyz(*latlonalt)

    def _convert(self):
        """Conversion from Topocentric Frame to parent frame
        """
        lat, lon, _ = self.latlonalt
        m = rot3(-lon) @ rot2(lat - np.pi / 2.) @ rot3(self.orientation)
        offset = np.identity(7)
        offset[0:3, -1] = self.coordinates
        return self._convert(m, m), offset

    mtd = '_to_%s' % parent_frame.__name__
    dct = {
        mtd: _convert,
        'latlonalt': latlonalt,
        'coordinates': coordinates,
        'parent_frame': parent_frame,
        'orientation': orientation
    }
    cls = _MetaFrame(name, (TopocentricFrame,), dct)
    cls + parent_frame

    return cls


WGS84 + ITRF + PEF + TOD + MOD + EME2000
TOD + TEME
# EME2000 + GCRF
# ITRF + TIRF + CIRF + GCRF
