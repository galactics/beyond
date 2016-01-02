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

    def _itrf_to_pef(self):
        m = iau1980.pole_motion(self.orbit.date)
        return m, m

    def _pef_to_tod(self):
        m = iau1980.sideral(self.orbit.date, model='apparent', eop_correction=False)
        return m, m + np.cross(iau1980.rate(self.orbit.date), self.orbit[:3])

    def _tod_to_mod(self):
        return iau1980.nutation(self.orbit.date)

    def _mod_to_gcrf(self):
        return iau1980.precesion(self.orbit.date)

    def transform(self, new_frame: str):

        old_frame = self.orbit.frame

        p_matrix = np.identity(3)
        v_matrix = np.identity(3)
        for a, b in self._tree.steps(old_frame, new_frame):
            oper = "_{}_to_{}".format(a.name.lower(), b.name.lower())
            roper = "_{}_to_{}".format(b.name.lower(), a.name.lower())

            if hasattr(self, oper):
                unit_p_matrix, unit_v_matrix = getattr(self, oper)()
            elif hasattr(self, roper):
                unit_p_matrix, unit_v_matrix = getattr(self, roper)().T
            else:
                raise ValueError("Unknown transformation: {}".format(oper))

            p_matrix = p_matrix @ unit_p_matrix
            v_matrix = v_matrix @ unit_v_matrix

        p = self.orbit[:3]
        v = self.orbit[3:]

        final = np.concatenate((p_matrix @ p, v_matrix @ v))
        return self.orbit.__class__(self.orbit.date, final, self.orbit.form, new_frame, **self.orbit.complements)

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
