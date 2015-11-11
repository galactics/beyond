#!/usr/bin/env python
# -*- coding: utf-8 -*-

from space.utils.tree import Node
from space.frames.poleandtimes import nutation


class Frame(Node):

    def add(self, frame):
        """Dynamically add a sub-frame to an existing one.

        The most common example is setting a station on the surface of the
        Earth.
        """

        if self.subtree is None:
            self.subtree = []
        self.subtree.append(frame)


class TopocentricFrame(Frame):

    def __init__(self, name, coordinates, body='earth'):
        self.coordinates = coordinates
        self.body = body
        super().__init__(name)


class FrameTranform:

    TEME = Frame('TEME')
    """True Equator Mean Equinox"""

    GTOD = Frame('GTOD')
    """Greenwich True Of Date"""

    TOD = Frame('TOD', [GTOD])
    """True (Equator) Of Date"""

    MOD = Frame('MOD', [TEME, TOD])
    """Mean (Equator) Of Date"""

    WGS84 = Frame('WGS84')
    """World Geodetic System 1984"""

    ITRF = Frame('ITRF', [WGS84])
    """International Terrestrial Reference Frame"""

    TIRF = Frame('TIRF', [ITRF])
    """Terrestrial Intermediate Reference Frame"""

    CIRF = Frame('CIRF', [TIRF])
    """Celestial Intermediate Reference Frame"""

    GCRF = Frame('GCRF', [CIRF])
    """Geocentric Celestial Reference Frame"""

    EME2000 = Frame('EME2000', [MOD, GCRF])

    _top = EME2000

    @classmethod
    def TOD_to_MOD(cls, date):
        return nutation(1980, date)

    @classmethod
    def register(cls, frame, parent=None):
        if parent is None:
            if isinstance(frame, TopocentricFrame) and frame.body.lower() == 'earth':
                parent = cls.WGS84
            else:
                raise ValueError("Please specify a parent frame")
        elif type(parent) is str:
            parent = cls._top.walk(parent)[0]

        parent.add(frame)
