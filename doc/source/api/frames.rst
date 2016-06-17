***********************
Frames and Pole motions
***********************

Frames
======

.. image:: /_static/frames.png

.. autoclass:: space.frames.frame._Frame
    :members:

CIO Based Frames
----------------

.. autoclass:: space.frames.frame.GCRF
    :members:

.. autoclass:: space.frames.frame.CIRF
    :members:

.. autoclass:: space.frames.frame.TIRF
    :members:

.. autoclass:: space.frames.frame.ITRF
    :members:

IAU1980 based Frames
--------------------

.. autoclass:: space.frames.frame.EME2000
    :members:

.. autoclass:: space.frames.frame.MOD
    :members:

.. autoclass:: space.frames.frame.TOD
    :members:

.. autoclass:: space.frames.frame.PEF
    :members:

.. autoclass:: space.frames.frame.TEME
    :members:

Ground Station
--------------

Ground Station may be created using the :py:func:`~space.frames.frame.create_station` function. This
will ensure correct frames conversions.

.. autofunction:: space.frames.frame.create_station

.. autoclass:: space.frames.frame.TopocentricFrame
    :members:

.. Local orbital Frames
    --------------------

    .. automodule:: space.frames.local
        :members:
        :undoc-members:
        :show-inheritance:

Pole motion models
==================

IAU1980
-------

.. automodule:: space.frames.iau1980
    :members:

IAU2000
-------

.. automodule:: space.frames.iau2010
    :members:
