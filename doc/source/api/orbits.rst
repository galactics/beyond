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

.. autodata:: beyond.orbits.forms.EQUI

StateVector
-----------

.. autoclass:: beyond.orbits.statevector.StateVector
    :members:
    :special-members: __new__
    :show-inheritance:

Orbit
-----

.. autoclass:: beyond.orbits.orbit.Orbit
    :members:
    :show-inheritance:

OrbitInfos
----------

.. autoclass:: beyond.orbits.statevector.Infos
    :members:

Ephem
-----

.. automodule:: beyond.orbits.ephem
    :members:

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
