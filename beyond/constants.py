#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Constants necessary to computations

All units are in `SI <https://en.wikipedia.org/wiki/International_System_of_Units>`__
"""

from numpy import sqrt
from .errors import BeyondError


c = 299792458
"""Speed of light in m.s⁻¹"""

g0 = 9.80665
"""Standard Earth gravity in m.s⁻²"""

G = 6.6740831e-11
"""Gravitational constant in m³.kg⁻¹.s⁻² or N.m².kg⁻²"""


class Body:
    """Generic class for the description of physical characteristics of celestial body"""

    def __init__(self, name, mass, equatorial_radius, *, flattening=1, **kwargs):
        self.name = name
        """Name of the celestial body"""
        self.mass = mass
        """Mass of the celestial body"""
        self.equatorial_radius = equatorial_radius
        """Equatorial radius of the celestial body"""
        self.flattening = flattening
        """Flattening of the celestial body"""
        self.propagator = kwargs.get("propagator")
        """Propagator, not set by default"""

        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f"<Body '{self.name}'>"

    def __getattr__(self, name):
        attrs = {
            "m": "mass",
            "r": "equatorial_radius",
            "f": "flattening",
            chr(956): "mu",
            "µ": "mu",
            "e": "eccentricity",
        }

        try:
            return getattr(self, attrs[name])
        except KeyError:
            raise AttributeError(name)

    @property
    def mu(self):
        """Standard gravitational parameter of the body"""
        return self.mass * G

    @property
    def eccentricity(self):
        """Eccentricity of the body"""
        return sqrt(self.f * 2 - self.f ** 2)

    def polar_radius(self):
        """Polar radius of the body"""
        return self.r * (1 - self.f)

    def propagate(self, date):
        """Gives the statevector of the celestial body

        Warning:
            A propagator should be attached to this body, as there is none provided
            by default. This can be done by setting :py:attr:`Body.propagator`.
            See :py:mod:`~beyond.env.solarsystem` or :py:mod:`~beyond.env.jpl`
            and their respective ``get_body()`` functions.

        Args:
            date (Date) :
        Return:
            StateVector:
        Raise:
            BeyondError: when no propagator is attached to the object
        """

        if self.propagator is None:
            raise BeyondError("No propagator attached to this body")

        return self.propagator.propagate(date)


Earth = Body(
    name="Earth",
    mass=5.97237e24,
    equatorial_radius=6378136.3,
    flattening=1 / 298.257223563,
    J2=1.08262668355315130e-3,
    J3=-2.532243534e-6,
)
"""Earth physical characteristics"""

Moon = Body(name="Moon", mass=7.342e22, equatorial_radius=1738100, flattening=0.0012)
"""Moon physical characteristics"""

Sun = Body(name="Sun", mass=1.98855e30, equatorial_radius=695700000, flattening=9e-6)
"""Sun physical characteristics"""

Mars = Body(name="Mars", mass=6.4171e23, equatorial_radius=3396200.0)
"""Mars physical characteristics"""
