***********************
Frames and Pole motions
***********************

Frames
======

.. image:: /_static/frames.png

.. autoclass:: beyond.frames.frames.Frame
    :members:

CIO Based Frames
----------------

.. autoclass:: beyond.frames.frames.GCRF
    :members:

.. autoclass:: beyond.frames.frames.CIRF
    :members:

.. autoclass:: beyond.frames.frames.TIRF
    :members:

.. autoclass:: beyond.frames.frames.ITRF
    :members:

IAU1980 based Frames
--------------------

.. autoclass:: beyond.frames.frames.EME2000
    :members:

.. autoclass:: beyond.frames.frames.MOD
    :members:

.. autoclass:: beyond.frames.frames.TOD
    :members:

.. autoclass:: beyond.frames.frames.PEF
    :members:

.. autoclass:: beyond.frames.frames.TEME
    :members:

Ground Station
--------------

Ground Station may be created using the :py:func:`~beyond.frames.stations.create_station` function. This
will ensure correct frames conversions.

.. autofunction:: beyond.frames.stations.create_station

.. autoclass:: beyond.frames.stations.TopocentricFrame
    :members:

Local Orbital Reference Frame
-----------------------------

It is possible to attach a frame to a moving object by calling the method
:py:meth:`Orbit.as_frame() <beyond.orbits.orbit.Orbit.as_frame>` or
:py:meth:`Ephem.as_frame() <beyond.orbits.ephem.Ephem.as_frame>`.
Both are a simple shortcut to the :py:func:`~beyond.frames.frames.orbit2frame` function.

.. autofunction:: beyond.frames.frames.orbit2frame

.. automodule:: beyond.frames.local
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
