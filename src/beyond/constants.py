#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Constants necessary to computations

All units should be SI
"""

from numpy import sqrt


c = 299792458
"""Speed of light in m.s⁻1"""

g0 = 9.80665
"""Standart Earth gravity in m.s⁻²"""

G = 6.6740831e-11
"""Gravitational constant in m³.kg⁻¹.s⁻² or N.m².kg⁻²"""


class Body:

    def __init__(self, name, mass, equatorial_radius, *, flattening=1, eccentricity=0):
        self.name = name
        self.mass = mass
        self.equatorial_radius = equatorial_radius
        self.flattening = flattening

    def __repr__(self):
        return "<Body '%s'>" % self.name

    def __getattr__(self, name):
        attrs = {
            'm': 'mass',
            'r': 'equatorial_radius',
            'f': 'flattening',
            chr(956): 'mu',
            'µ': 'mu',
            'e': 'eccentricity',
        }

        try:
            return getattr(self, attrs[name])
        except KeyError:
            raise AttributeError(name)

    @property
    def mu(self):
        return self.mass * G

    @property
    def eccentricity(self):
        return sqrt(self.f * 2 - self.f ** 2)

    def polar_radius(self):
        return self.r * (1 - self.f)


Earth = Body(
    name="Earth",
    mass=5.97237e24,
    equatorial_radius=6378136.3,
    flattening=1 / 298.257223563
)

Moon = Body(
    name="Moon",
    mass=7.342e22,
    equatorial_radius=1738100,
    flattening=0.0012
)

Sun = Body(
    name="Sun",
    mass=1.98855e30,
    equatorial_radius=695700000,
    flattening=9e-6,
)
