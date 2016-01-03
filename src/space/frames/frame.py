#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from space.utils.node import Node
from . import iau1980


class Frame(Node):

    def __str__(self):
        return self.name

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
        FrameTransform.register(self)


class FrameTransform:

    TEME = Frame('TEME')
    """True Equator Mean Equinox"""

    GTOD = Frame('GTOD')
    """Greenwich True Of Date"""

    WGS84 = Frame('WGS84')
    """World Geodetic System 1984"""

    ITRF = Frame('ITRF', [WGS84])
    """International Terrestrial Reference Frame"""

    PEF = Frame('PEF', [TEME, ITRF])
    """Pseudo Earth Fixed"""

    TOD = Frame('TOD', [PEF])
    """True (Equator) Of Date"""

    MOD = Frame('MOD', [TOD])
    """Mean (Equator) Of Date"""

    TIRF = Frame('TIRF')
    """Terrestrial Intermediate Reference Frame"""

    CIRF = Frame('CIRF', [TIRF])
    """Celestial Intermediate Reference Frame"""

    GCRF = Frame('GCRF', [CIRF])
    """Geocentric Celestial Reference Frame"""

    EME2000 = Frame('EME2000', [MOD, GCRF])

    _tree = EME2000

    def __init__(self, orbit):
        self.orbit = orbit

    @classmethod
    def _convert_matrix(cls, x=None, y=None):
        x = np.identity(3) if x is None else x
        y = np.identity(3) if y is None else y

        m = np.identity(6)
        m[:3, :3] = x
        m[3:, 3:] = y
        return m

    def _itrf_to_pef(self):
        m = iau1980.pole_motion(self.orbit.date)
        return self._convert_matrix(m, m), np.zeros(6)

    def _pef_to_tod(self):
        m = iau1980.sideral(self.orbit.date, model='apparent', eop_correction=False)
        offset = np.zeros(6)
        offset[3:] = np.cross(iau1980.rate(self.orbit.date), self.orbit[:3])
        return self._convert_matrix(m, m), offset

    def _tod_to_mod(self):
        return iau1980.nutation(self.orbit.date)

    def _mod_to_gcrf(self):
        return iau1980.precesion(self.orbit.date)

    def transform(self, new_frame: str):

        matrix = np.identity(6)
        orb = self.orbit.base

        for a, b in self._tree.steps(self.orbit.frame, new_frame):
            oper = "_{}_to_{}".format(a.name.lower(), b.name.lower())
            roper = "_{}_to_{}".format(b.name.lower(), a.name.lower())

            if hasattr(self, oper):
                unit_matrix, offset = getattr(self, oper)()
            elif hasattr(self, roper):
                unit_matrix, offset = getattr(self, roper)()
                unit_matrix = unit_matrix.T
                offset = - offeset
            else:
                raise ValueError("Unknown frame transformation: {} => {}".format(a, b))


            orb = unit_matrix @ (orb + offset)

        # final = matrix @ self.orbit
        return self.orbit.__class__(self.orbit.date, orb, self.orbit.form, new_frame, **self.orbit.complements)

    @classmethod
    def register(cls, frame, parent=None):
        if parent is None:
            if isinstance(frame, TopocentricFrame) and frame.body.lower() == 'earth':
                parent = cls.WGS84
            else:
                raise ValueError("Please specify a parent frame")
        elif type(parent) is str:
            parent = cls._tree.walk(parent)[0]

        parent.add(frame)
