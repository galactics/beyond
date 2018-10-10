#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module define the Frames available for computation and their relations
to each other.

The relations may be circular, thanks to the use of the Node class.

.. code-block:: text

                   ,-------.        ,----.
                   |EME2000|..bias..|GCRF|
                   `-------'        `----'
                       |              |
                   Precesion          |
                       |              |
                     ,---.        Prececion
                     |MOD|            +
                     `---'         Nutation
                       |     + model corrections
                    Nutation          |
              + model corrections     |
                       |              |
    ,----.           ,---.         ,----.
    |TEME|--Equinox--|TOD|         |CIRF|
    `----'           `---'         `----'
                       |              |
                 Sideral time   Sideral time
                       |              |
                     ,---.         ,----.
                     |PEF|         |TIRF|
                     `---'         `----'
                        \\            /
                    IAU 1980       IAU 2010
           Earth Orientation       Earth Orientation
                  Parameters       Parameters
                           \\     /
         ,-----.            ,----.
         |WGS84|--identity--|ITRF|
         `-----'            `----'
"""

import sys
import warnings
import numpy as np

from ..errors import UnknownFrameError
from ..constants import Earth
from ..utils.matrix import rot3
from ..utils.node import Node
from . import iau1980, iau2010
from .local import to_qsw, to_tnw

CIO = ['ITRF', 'TIRF', 'CIRF', 'GCRF']
IAU1980 = ['TOD', 'MOD']
OTHER = ['EME2000', 'TEME', 'WGS84', 'PEF']

__all__ = CIO + IAU1980 + OTHER + ['get_frame']


class FrameCache(dict):
    """This class is here to emulate module behaviour for dynamically
    created frames.

    It's useful when pickle is involved (e.g. multiprocessing)
    """
    def __getattr__(self, name):
        if name not in self:
            raise AttributeError(name)
        return self[name]


dynamic = FrameCache()
"""This dictionnary contains all the frames. Those defined here, and those created on the fly
by the developper.
"""

sys.modules[__name__ + ".dynamic"] = dynamic


def get_frame(frame):
    """Frame factory

    Args:
        frame (str): name of the desired frame
    Return:
        ~beyond.frames.frames.Frame
    """
    if frame not in dynamic.keys():
        raise UnknownFrameError(frame)

    return dynamic[frame]


class _MetaFrame(type, Node):
    """This MetaClass is here to join the behaviours of ``type`` and ``Node``
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


class Frame(metaclass=_MetaFrame):
    """Frame base class
    """

    center = Earth

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
        m = np.identity(6)

        if x is not None:
            m[:3, :3] = x
        if y is not None:
            m[3:, 3:] = y

        return m

    def transform(self, new_frame):
        """Change the frame of the orbit

        Args:
            new_frame (str)
        Return:
            numpy.ndarray
        """

        steps = self.__class__.steps(new_frame)

        orbit = self.orbit

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
                    offset = - offset
                else:
                    raise NotImplementedError("Unknown transformation {} to {}".format(_from, _to))

            if getattr(_from, "_rotation_before_translation", False):
                # In case of topocentric frame, the rotation is done before the translation
                orbit = offset + (rotation @ orbit)
            else:
                orbit = rotation @ (offset + orbit)

        return orbit


class TEME(Frame):
    """True Equator Mean Equinox"""

    orientation = "TEME"

    def _to_TOD(self):
        equin = iau1980.equinox(self.date, eop_correction=False, terms=4, kinematic=False)
        m = rot3(-np.deg2rad(equin))
        return self._convert(m, m), np.zeros(6)


class GTOD(Frame):
    """Greenwich True Of Date"""
    orientation = "GTOD"


class WGS84(Frame):
    """World Geodetic System 1984"""

    orientation = "WGS84"

    def _to_ITRF(self):
        return np.identity(6), np.zeros(6)


class PEF(Frame):
    """Pseudo Earth Fixed"""

    orientation = "PEF"

    def _to_TOD(self):
        m = iau1980.sideral(self.date, model='apparent', eop_correction=False)
        offset = np.zeros(6)
        offset[3:] = np.cross(iau1980.rate(self.date), self.orbit[:3])
        return self._convert(m, m), offset


class TOD(Frame):
    """True (Equator) Of Date"""

    orientation = "TOD"

    def _to_MOD(self):
        m = iau1980.nutation(self.date, eop_correction=False)
        return self._convert(m, m), np.zeros(6)


class MOD(Frame):
    """Mean (Equator) Of Date"""

    orientation = "MOD"

    def _to_EME2000(self):
        m = iau1980.precesion(self.date)
        return self._convert(m, m), np.zeros(6)


class EME2000(Frame):
    """EME2000 inertial frame (also known as J2000)"""

    orientation = "EME2000"


class ITRF(Frame):
    """International Terrestrial Reference Frame"""

    orientation = "ITRF"

    def _to_PEF(self):
        m = iau1980.earth_orientation(self.date)
        return self._convert(m, m), np.zeros(6)

    def _to_TIRF(self):
        m = iau2010.earth_orientation(self.date)
        return self._convert(m, m), np.zeros(6)


class TIRF(Frame):
    """Terrestrial Intermediate Reference Frame"""

    orientation = "TIRF"

    def _to_CIRF(self):
        m = iau2010.sideral(self.date)
        offset = np.zeros(6)
        offset[3:] = np.cross(iau2010.rate(self.date), self.orbit[:3])
        return self._convert(m, m), offset


class CIRF(Frame):
    """Celestial Intermediate Reference Frame"""

    orientation = "CIRF"

    def _to_GCRF(self):
        m = iau2010.precesion_nutation(self.date)
        return self._convert(m, m), np.zeros(6)


class GCRF(Frame):
    """Geocentric Celestial Reference Frame"""

    orientation = "GCRF"


def orbit2frame(name, ref_orbit, orientation=None, center=None):
    """Create a frame based on a Orbit or Ephem object.

    Args:
        name (str): Name to give the created frame
        ref_orbit (Orbit or Ephem):
        orientation (str): Orientation of the created frame
    Return:
        Frame:

    If orientation is ``None``, the new frame will keep the orientation of the
    reference frame of the Orbit and move along with the orbit.
    Other acceptable values are ``"QSW"`` and ``"TNW"``.
    See :py:func:`~beyond.frames.local.to_qsw` and :py:func:`~beyond.frames.local.to_tnw`
    for informations regarding these orientations.
    """

    if orientation is None:
        orientation = ref_orbit.frame.orientation
    elif orientation.upper() not in ("QSW", "TNW"):
        raise ValueError("Unknown orientation '%s'" % orientation)

    if center is None:
        center = Earth

    def _to_parent_frame(self):
        """Conversion from orbit frame to parent frame
        """
        offset = ref_orbit.propagate(self.date).base.copy()

        if orientation.upper() in ("QSW", "TNW"):

            # propagation of the reference orbit to the date of the
            # converted orbit
            orb = ref_orbit.propagate(self.date)

            m = to_qsw(orb) if orientation.upper() == "QSW" else to_tnw(orb)

            # we transpose the matrix because it represents the conversion
            # from inertial to local frame, and we'd like the other way around
            rotation = Frame._convert(m, m).T
        else:
            # The orientation is the same as the parent reference frame
            rotation = np.identity(6)

        return rotation, offset

    # define the name of the method of conversion
    mtd = '_to_%s' % ref_orbit.frame.__name__

    # dictionnary which defines attributes of the created class
    dct = {
        mtd: _to_parent_frame,
        "orientation": orientation,
        "center": center
    }

    # Creation of the class
    cls = _MetaFrame(name, (Frame,), dct)

    # Link to the parent
    cls + ref_orbit.frame
    return cls


WGS84 + ITRF + PEF + TOD + MOD + EME2000
TOD + TEME
# EME2000 + GCRF
ITRF + TIRF + CIRF + GCRF
