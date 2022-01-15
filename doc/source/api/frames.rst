****************
Reference Frames
****************

.. _frames:

Frames
======

.. image:: /_static/frames.png

The preferred way to retrieve a frame is by using the :py:func:`~beyond.frames.frames.get_frame` function.

.. autofunction:: beyond.frames.frames.get_frame

However, in some cases this is done for you. See :py:attr:`StateVector.frame <beyond.orbits.statevector.StateVector.frame>` for example.

CIO Based Frames
----------------

.. autodata:: beyond.frames.frames.GCRF

.. autodata:: beyond.frames.frames.CIRF

.. autodata:: beyond.frames.frames.TIRF

.. autodata:: beyond.frames.frames.ITRF

IAU1980 based Frames
--------------------

.. autodata:: beyond.frames.frames.EME2000

.. autodata:: beyond.frames.frames.MOD

.. autodata:: beyond.frames.frames.TOD

.. autodata:: beyond.frames.frames.PEF

.. autodata:: beyond.frames.frames.TEME

Others
------

.. autodata:: beyond.frames.frames.G50

.. autodata:: beyond.frames.frames.WGS84

Local Orbital Reference Frame
-----------------------------

It is possible to attach a frame to a moving object by calling the method
:py:meth:`Orbit.as_frame() <beyond.orbits.orbit.Orbit.as_frame>` or
:py:meth:`Ephem.as_frame() <beyond.orbits.ephem.Ephem.as_frame>`.
Both are a simple shortcut to the :py:func:`~beyond.frames.frames.orbit2frame` function.

.. autofunction:: beyond.frames.frames.orbit2frame

.. automodule:: beyond.frames.local
    :members:

.. autodata:: beyond.frames.frames.Hill


Ground Stations
---------------

A ground station may be created using the :py:func:`~beyond.frames.stations.create_station` function. This
will ensure correct frames conversions.

.. autofunction:: beyond.frames.stations.create_station

.. autoclass:: beyond.frames.stations.TopocentricFrame
    :members:

Lagrange Points
---------------

.. autofunction:: beyond.frames.lagrange.lagrange

Creating new frames
-------------------

Creating new frames is done by creating :py:class:`~beyond.frames.center.Center` and :py:class:`~beyond.frames.orient.Orientation` objects, and feeding them to :py:class:`~beyond.frames.frames.Frame`.

.. autoclass:: beyond.frames.frames.Frame
    :members:

.. autoclass:: beyond.frames.center.Center
    :members:

.. autoclass:: beyond.frames.orient.Orientation
    :members:

.. autoclass:: beyond.frames.orient.LocalOrbitalOrientation
    :members:

.. autoclass:: beyond.frames.orient.TopocentricOrientation
    :members:


Earth Orientation Parameters
============================

IAU1980
-------

.. automodule:: beyond.frames.iau1980
    :members:

IAU2000
-------

.. automodule:: beyond.frames.iau2010
    :members:
