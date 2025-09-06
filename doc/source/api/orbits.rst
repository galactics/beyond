Orbits
======

.. image::
    /_static/orb.png

Abstract classes
----------------

.. autoclass:: beyond.orbits.statevector.AbstractStateVector
    :members:
    :special-members: __new__

.. autoclass:: beyond.orbits.orbit.AbstractOrbit
    :members:
    :special-members: __new__

Concrete classes
----------------

.. autoclass:: beyond.orbits.statevector.StateVector
    :members:
    :special-members: __new__
    :show-inheritance:

.. autoclass:: beyond.orbits.orbit.Orbit
    :members:
    :show-inheritance:

.. autoclass:: beyond.orbits.orbit.MeanOrbit
    :members:
    :show-inheritance:

Converting between osculating and mean orbits
---------------------------------------------

Osculating parameters are a weird bunch. They allow to get a general idea of
the shape of the orbit. It is as if we tried to precisely measure the altitude of
a lake by only taking one point of measurement with strong waves. Therefore,
it is necessary to use averaging techniques to better describe the shape and
dynamics of the orbit.

.. image:: /_static/osculating.svg
    :align: center

Both :py:class:`~beyond.orbits.statevector.StateVector` and :py:class:`~beyond.orbits.orbit.Orbit` represent
osculating states. The only difference between them is that :py:class:`~beyond.orbits.orbit.Orbit` has a
propagator attached.

Methods :py:meth:`~beyond.orbits.orbit.Orbit.as_statevector` and :py:meth:`~beyond.orbits.statevector.AbstractStateVector.as_orbit` don't perform any computation, and simply create a new instance (of StateVector and Orbit, respectively), with exactly the same data as the original object.

Methods :py:meth:`~beyond.orbits.orbit.MeanOrbit.to_osculating` and :py:meth:`~beyond.orbits.statevector.StateVector.to_mean_orbit` compute the new object with the help of a propagator.

.. image:: /_static/orbit_transformations.png
    :align: center

Forms
-----

When using a :py:class:`~beyond.orbits.statevector.StateVector` or :py:class:`~beyond.orbits.orbit.Orbit` object it is possible
to change its form by naming the desired new form.::

    >>> print(repr(orb))
    Orbit =
      date = 2020-10-04T04:38:08.250720 UTC
      form = tle
      frame = TEME
      propag = Sgp4
      coord =
        i = 0.9013630748877075
        Ω = 2.951400634341467
        e = 0.0001204
        ω = 1.769838910680086
        M = 0.9752533341001394
        n = 0.0011263401984422173

    >>> orb.form = "keplerian_circular"
    >>> print(repr(orb))
    Orbit =
      date = 2020-10-04T04:38:08.250720 UTC
      form = keplerian_circular
      frame = TEME
      propag = Sgp4
      coord =
        a = 6798290.45301548
        ex = -2.3806801365162165e-05
        ey = 0.00011802286307643835
        i = 0.9013630748877075
        Ω = 2.951400634341467
        u = 2.74529160645093

Some forms have aliases:

    * ``circular`` points to ``keplerian_circular``
    * ``mean`` points to ``keplerian_mean``
    * ``mean_circular`` points to ``keplerian_mean_circular``
    * ``eccentric`` points to ``keplerian_eccentric``

It is also possible to access individual element of a :py:class:`~beyond.orbits.statevector.StateVector` or
:py:class:`~beyond.orbits.orbit.Orbit` object by attribute or key. Some elements have aliases,
particularly those with Greek letters name::

    >>> orb.Omega  # is equivalent to orb.Ω
    2.951400634341467
    >>> orb["Omega"]
    2.951400634341467
    >>> orb.aol  # is equivalent to orb.u
    2.74529160645093

.. autoclass:: beyond.orbits.forms.Form
    :show-inheritance:

.. autodata:: beyond.orbits.forms.CART

.. autodata:: beyond.orbits.forms.KEPL

.. autodata:: beyond.orbits.forms.SPHE

.. autodata:: beyond.orbits.forms.TLE

.. autodata:: beyond.orbits.forms.KEPL_M

.. autodata:: beyond.orbits.forms.KEPL_C

.. autodata:: beyond.orbits.forms.KEPL_E

.. autodata:: beyond.orbits.forms.KEPL_MC

.. autodata:: beyond.orbits.forms.EQUI

.. autodata:: beyond.orbits.forms.CYL

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
