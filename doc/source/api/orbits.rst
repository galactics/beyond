Orbits
======

Forms
-----

.. autoclass:: beyond.orbits.forms.Form
    :show-inheritance:

Available forms are

.. autoattribute:: beyond.orbits.forms.FormTransform.CART

    Cartesian form (x, y, z, vx, vy, vz)

.. autoattribute:: beyond.orbits.forms.FormTransform.KEPL

    Keplerian form

    * a : semi-major axis
    * e : excentricity
    * i : inclination
    * Ω : right-ascencion of ascending node
    * ω : Arguement of perigee
    * ν : True anomaly

    see `wikipedia <https://en.wikipedia.org/wiki/Orbital_elements>`__ for details

.. autoattribute:: beyond.orbits.forms.FormTransform.SPHE

    Spherical form

    * r : radial distance / altitude
    * θ : azimuth / longitude
    * φ : elevation / latitude
    * r_dot : first derivative of radial distance / altitude
    * θ_dot : first derivative of azimuth / longitude
    * φ_dot : first derivative of elevation / latitude

.. autoattribute:: beyond.orbits.forms.FormTransform.TLE

    TLE special form

    * i : inclination
    * Ω : right-ascencion of ascending node
    * e : excentricity
    * ω : arguement of perigee
    * M : mean anomaly
    * n : mean motion

    see :py:class:`~beyond.orbits.tle.Tle` for details

.. autoattribute:: beyond.orbits.forms.FormTransform.KEPL_M

    Same as Keplerian, but replaces True anomaly with `Mean anomaly <https://en.wikipedia.org/wiki/Mean_anomaly>`__

.. autoattribute:: beyond.orbits.forms.FormTransform.KEPL_C

    Special case for near-circular orbits

    * a : semi-major axis
    * ex : e * cos(ω)
    * ey : e * sin(ω)
    * i : inclination
    * Ω : right-ascencion of ascending node
    * λ : ω + M

Orbit
-----

.. automodule:: beyond.orbits.orbit
    :members:
    :undoc-members:
    :special-members: __new__
    :show-inheritance:

Ephem
-----

.. automodule:: beyond.orbits.ephem
    :members:


.. _tle:

TLE
---

The `TLE <https://en.wikipedia.org/wiki/Two-line_element_set>`__ representation
is a de-facto standard for orbit description.

.. automodule:: beyond.orbits.tle
    :members:
    :undoc-members:
    :show-inheritance:

Listeners
---------

Listeners allow to watch for state transition during the propagation of an orbit.
For example, the :abbr:`AOS (Acquisition Of Signal)` and :abbr:`LOS (Loss Of Signal)` of a satellite as
seen from a station.

.. automodule:: beyond.orbits.listeners
    :members: