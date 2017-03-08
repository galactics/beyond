#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module define the Frames available for computation and their relations
to each other.

The relations may be circular, thanks to the use of the Node2 class.

.. code-block:: text
    
                   ,-------.        ,----.
                   |EME2000|..bias..|GCRF|
                   `-------'        `----'
                       |              |
                   precesion          |
                       |              |
                     ,---.        prececion
                     |MOD|            +
                     `---'         nutation
                       |              |
                    nutation          |
                       |              |
    ,----.           ,---.         ,----.
    |TEME|--equinox--|TOD|         |CIRF|
    `----'           `---'         `----'
                       |              |
                    sideral        sideral
                       |              |
                     ,---.         ,----.
                     |PEF|         |TIRF|
                     `---'         `----'
                        \            /
           model corrections      model corrections
                     IAU1980      IAU2010
                           \      /
         ,-----.            ,----.
         |WGS84|--identity--|ITRF|
         `-----'            `----'
"""

import sys
import warnings
import numpy as np

from ..constants import e_e, r_e
from ..utils.date import Date
from ..utils.matrix import rot2, rot3
from ..utils.node import Node2
from . import iau1980, iau2010
from .local import to_qsw, to_tnw


CIO = ['ITRF', 'TIRF', 'CIRF', 'GCRF']
IAU1980 = ['TOD', 'MOD']
OTHER = ['EME2000', 'TEME', 'WGS84', 'PEF']
TOPO = ['create_station']

__all__ = CIO + IAU1980 + OTHER + TOPO + ['get_frame']


class _FrameCache(dict):
    """This class is here to emulate module behaviour for dynamically
    created frames.

    It's useful when pickle is involved (e.g. multiprocessing)
    """
    def __getattr__(self, name):
        if name not in self:
            raise AttributeError(name)
        return self[name]


dynamic = _FrameCache()
"""This dictionnary contains all the frames. Those defined here, and those created on the fly
by the developper.
"""

sys.modules[__name__ + ".dynamic"] = dynamic



def get_frame(frame):
    """Frame factory

    Args:
        frame (str): name of the desired frame
    Return:
        ~beyond.frames.frame._Frame
    """
    if frame in dynamic.keys():
        return dynamic[frame]
    else:
        raise ValueError("Unknown Frame : '{}'".format(frame))


class _MetaFrame(type, Node2):
    """This MetaClass is here to join the behaviours of ``type`` and ``Node2``
    """

    def __init__(cls, name, bases, dct):
        super(_MetaFrame, cls).__init__(name, bases, dct)
        super(type, cls).__init__(name)

        if cls.__name__ in dynamic:
            warnings.warn("A frame with the name '%s' is already registered. Overriding" % cls.__name__)

        cls.__module__ = __name__ + ".dynamic"

        # Making the frame available to the get_frame function
        dynamic[cls.__name__] = cls

    def __repr__(cls):  # pragma: no cover
        return "<Frame '{}'>".format(cls.name)


class _Frame(metaclass=_MetaFrame):
    """Frame base class
    """

    def __init__(self, date, orbit):
        """
        Args:
            date (~beyond.utils.Date)
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

            from_obj = _from(self.date, orbit)
            direct = "_to_%s" % _to

            if hasattr(from_obj, direct):
                rotation, offset = getattr(from_obj, direct)()
            else:
                to_obj = _to(self.date, orbit)
                inverse = "_to_%s" % _from
                if hasattr(to_obj, inverse):
                    rotation, offset = getattr(to_obj, inverse)()
                    rotation = rotation.T
                    offset[:6, -1] = - offset[:6, -1]
                else:
                    raise NotImplementedError("Unknown transformation {} to {}".format(_from, _to))

            if issubclass(_from, TopocentricFrame):
                # In case of topocentric frame, the rotation is done before the translation
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
    """EME2000 inertial frame (also known as J2000)"""
    pass


class ITRF(_Frame):
    """International Terrestrial Reference Frame"""

    def _to_PEF(self):
        m = iau1980.pole_motion(self.date)
        return self._convert(m, m), np.identity(7)

    def _to_TIRF(self):
        m = iau2010.pole_motion(self.date)
        return self._convert(m, m), np.identity(7)


class TIRF(_Frame):
    """Terrestrial Intermediate Reference Frame"""

    def _to_CIRF(self):
        m = iau2010.sideral(self.date)
        offset = np.identity(7)
        offset[3:6, -1] = np.cross(iau2010.rate(self.date), self.orbit[:3])
        return self._convert(m, m), offset


class CIRF(_Frame):
    """Celestial Intermediate Reference Frame"""

    def _to_GCRF(self):
        m = iau2010.precesion_nutation(self.date)
        return self._convert(m, m), np.identity(7)


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

        date = start
        visibility, max_found = False, False

        for date in Date.range(start, stop, step):

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

    @classmethod
    def _vis(cls, orb, date):
        """shortcut to onvert orb to topocentric frame in spherical form at a
        given date
        """
        orb = orb.propagate(date)
        orb.frame = cls.__name__
        orb.form = 'spherical'

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

        prev_step = (stop - start)
        step = prev_step / 2
        eps = 1e-3

        start_attr = getattr(cls._vis(orb, start), element)
        prev = start_attr
        date_cursor = start + step

        MAX_ITER = 60

        for i in range(MAX_ITER):
            orb_cursor = cls._vis(orb, date_cursor)
            attr = getattr(orb_cursor, element)

            if abs(attr) <= eps:
                # We have a winner !
                break

            if np.sign(attr) != np.sign(prev):
                # reverse direction
                step *= -1
                if prev_step == -step:
                    # decrease the step if this direction was already searched through
                    step /= 2

            prev = attr
            prev_step = step
            date_cursor += step
        else:
            raise RuntimeError("Too many iterations", MAX_ITER)

        return orb_cursor

def _geodetic_to_cartesian(lat, lon, alt):
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


def create_station(name, latlonalt, parent_frame=WGS84, orientation='N'):
    """Create a ground station instance

    Args:
        name (str): Name of the station

        latlonalt (tuple of float): coordinates of the station, as follow:

            * Latitude in degrees
            * Longitude in degrees
            * Altitude to sea level in meters

        parent_frame (_Frame): Planetocentric rotating frame of reference of
            coordinates.
        orientation (str or float): Heading of the station
            Acceptables values are 'N', 'S', 'E', 'W' or any angle in radians

    Return:
        TopocentricFrame
    """

    if isinstance(orientation, str):
        orient = {'N': np.pi, 'S': 0., 'E': np.pi / 2., 'W': 3 * np.pi / 2.}
        orientation = orient[orientation]

    latlonalt = list(latlonalt)
    latlonalt[:2] = np.radians(latlonalt[:2])
    coordinates = _geodetic_to_cartesian(*latlonalt)

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


def orbit2frame(name, ref_orbit, orientation=None):
    """Create a frame based on a Orbit or Ephem object.

    If orientation is ``None``, the new frame will keep the orientation of the
    reference frame of the Orbit and move along with the orbit
    """

    def _convert(self):
        """Conversion from orbit frame to parent frame
        """
        offset = np.identity(7)
        offset[0:6, -1] = ref_orbit.propagate(self.date).base

        if orientation is None:
            # The orientation is the same as the parent reference frame
            rotation = np.identity(7)
        elif orientation.upper() in ("QSW", "TNW"):

            # propagation of the reference orbit to the date of the
            # converted orbit
            orb = ref_orbit.propagate(self.date)

            m = to_qsw(orb) if orientation.upper() == "QSW" else to_tnw(orb)

            # we transpose the matrix because it represent the conversion
            # from inertial to local frame, and we'd like the other way around
            rotation = _Frame._convert(m, m).T
        else:
            raise ValueError("Unknown orientation '%s'" % orientation)

        return rotation, offset

    # define the name of the method of conversion
    mtd = '_to_%s' % ref_orbit.frame.__name__

    # dictionnary which defines attributes of the created class
    dct = {
        mtd: _convert
    }

    # Creation of the class
    cls = _MetaFrame(name, (_Frame,), dct)

    # Link to the parent
    cls + ref_orbit.frame
    return cls


WGS84 + ITRF + PEF + TOD + MOD + EME2000
TOD + TEME
# EME2000 + GCRF
ITRF + TIRF + CIRF + GCRF
