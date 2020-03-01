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

.. autodata:: beyond.orbits.forms.KEPL_E


Orbit
-----

.. autoclass:: beyond.orbits.orbit.Orbit
    :members:
    :special-members: __new__
    :show-inheritance:

OrbitInfos
----------

.. autoclass:: beyond.orbits.orbit.OrbitInfos
    :members:

Ephem
-----

.. automodule:: beyond.orbits.ephem
    :members:


Listeners
---------

Listeners allow to watch for state transition during the propagation of an orbit.
For example, the :abbr:`AOS (Acquisition Of Signal)` and :abbr:`LOS (Loss Of Signal)` of a satellite as
seen from a station.

.. automodule:: beyond.orbits.listeners
    :members:
    :special-members: __init__

Maneuvers
---------

.. autoclass:: beyond.orbits.man.ImpulsiveMan
    :members:
    :special-members: __init__

.. autoclass:: beyond.orbits.man.KeplerianImpulsiveMan
    :members:
    :special-members: __init__

.. autoclass:: beyond.orbits.man.ContinuousMan
    :members:
    :special-members: __init__

Cov
---

.. autoclass:: beyond.orbits.cov.Cov
    :members:
    :special-members: __new__
