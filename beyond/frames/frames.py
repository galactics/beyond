#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This module define the Reference Frames available for computation and their relations
to each other.
"""

import sys
import logging
import numpy as np

from ..config import config
from ..errors import UnknownFrameError, UnknownBodyError
from ..constants import Earth
from ..utils.matrix import rot3, expand
from . import orient, center
from .local import to_local

CIO = ["ITRF", "TIRF", "CIRF", "GCRF"]
IAU1980 = ["TOD", "MOD"]
OTHER = ["EME2000", "TEME", "WGS84", "PEF", "G50"]

__all__ = CIO + IAU1980 + OTHER + ["get_frame"]

log = logging.getLogger(__name__)


class FrameCache(dict):
    """This class is here to emulate module behavior for dynamically
    created frames.

    It's useful when pickle is involved (e.g. multiprocessing)
    """

    def __getattr__(self, name):
        if name not in self:
            raise AttributeError(name)
        return self[name]


dynamic = FrameCache()
"""This dictionary contains all the frames. Those defined here, and those created on the fly
by the developer.
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
        if config.get("env", "jpl", "dynamic_frames", fallback=False):
            from ..env.jpl import create_frames, JplConfigError

            try:
                create_frames()
            except (JplConfigError, UnknownBodyError) as e:
                raise UnknownFrameError(frame) from e
        else:
            raise UnknownFrameError(frame)

    return dynamic[frame]


class Frame:
    """Frame base class
    """

    center = Earth

    def __init__(self, name, orientation, center, exists_warning=True):
        """
        Args:
            date (~beyond.utils.Date)
            orbit (numpy.ndarray)
        """
        self.name = name
        self.orientation = orientation
        self.center = center

        if exists_warning and name in dynamic:
            log.warning(
                "A frame with the name '%s' is already registered. Overriding" % name
            )

        dynamic[name] = self

    def __str__(self):  # pragma: no cover
        return self.name

    def __repr__(self):  # pragma: no cover
        return "<{} '{}' at {}>".format(
            self.__class__.__name__, self.name, hex(id(self))
        )

    def transform(self, orbit, new_frame):

        new_orb = orbit.copy(form="cartesian")

        offset = self.center.convert_to(
            orbit.date, new_frame.center, new_frame.orientation
        )
        m = self.orientation.convert_to(orbit.date, new_frame.orientation)

        new_orb[:] = m @ new_orb + offset
        new_orb._frame = new_frame
        new_orb.form = orbit.form
        return new_orb


EME2000 = Frame("EME2000", orient.EME2000, center.Earth)
"""EME2000 inertial frame (also known a J2000)"""

MOD = Frame("MOD", orient.MOD, center.Earth)
"""Mean (Equator) of Date"""

TOD = Frame("TOD", orient.TOD, center.Earth)
"""True (Equator) of Date"""

TEME = Frame("TEME", orient.TEME, center.Earth)
"""True Equator Mean Equinox"""

PEF = Frame("PEF", orient.PEF, center.Earth)
"""Pseudo Earth Fixed"""

ITRF = Frame("ITRF", orient.ITRF, center.Earth)
"""International Terrestrial Reference Frame"""

WGS84 = ITRF
"""World Geodetic System 1984

This is equivalent to ITRF, with an error below the centimeter"""
dynamic["WGS84"] = ITRF

TIRF = Frame("TIRF", orient.TIRF, center.Earth)
"""Terrestrial intermediate Reference Frame"""

CIRF = Frame("CIRF", orient.CIRF, center.Earth)
"""Celestial Intermediate Reference Frame"""

GCRF = Frame("GCRF", orient.GCRF, center.Earth)
"""Geocentric Celestial Reference Frame"""

G50 = Frame("G50", orient.G50, center.Earth)
"""Gamma 50 Reference Frame"""


def orbit2frame(name, ref_orbit, orientation=None, parent=EME2000, exists_warning=True):
    """Create a frame based on a Orbit or Ephem object.

    Args:
        name (str): Name to give the created frame
        ref_orbit (Orbit or Ephem):
        orientation (str): Orientation of the created frame. If orientation is ``None``,
            the new frame will keep the orientation of the reference frame of the Orbit
            and move along with the orbit. Other acceptable values are ``"QSW"`` (and its
            aliases "LVLH" and "RSW") or ``"TNW"``.
        parent (Frame) : Inertial frame to which to attach the LOF
        exists_warning (bool): Disable the warning when creating a frame with an already
            taken name by setting this value to False
    Return:
        Frame:

    See :py:mod:`~beyond.frames.local` for informations regarding orientations.
    """

    if orientation is None:
        orientation = ref_orbit.frame.orientation
    else:
        if orientation.upper() in ("RSW", "LVLH"):
            orientation = "QSW"
        elif orientation.upper() not in ("QSW", "TNW"):
            raise ValueError("Unknown orientation '%s'" % orientation)

        orientation = orient.LocalOrbitalOrientation(
            name, ref_orbit, orientation, parent
        )

    center_obj = center.Center(name, body=parent.center.body)
    center_obj.add_link(
        ref_orbit.frame.center, ref_orbit.frame.orientation, ref_orbit,
    )

    return Frame(name, orientation, center_obj, exists_warning)
