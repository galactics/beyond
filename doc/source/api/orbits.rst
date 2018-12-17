Orbits
======

Forms
-----

.. autoclass:: beyond.orbits.forms.Form
    :show-inheritance:

Available forms are

.. autodata:: beyond.orbits.forms.CART

.. autodata:: beyond.orbits.forms.KEPL

.. autodata:: beyond.orbits.forms.SPHE

.. autodata:: beyond.orbits.forms.TLE

.. autodata:: beyond.orbits.forms.KEPL_M

.. autodata:: beyond.orbits.forms.KEPL_C


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
    :special-members: __init__

Maneuver
--------

.. autoclass:: beyond.orbits.man.Maneuver
    :members:
    :special-members: __init__