***********************
Frames and Pole motions
***********************

Frames
======

.. image:: /_static/frames.png

.. autoclass:: beyond.frames.frame._Frame
    :members:

CIO Based Frames
----------------

.. autoclass:: beyond.frames.frame.GCRF
    :members:

.. autoclass:: beyond.frames.frame.CIRF
    :members:

.. autoclass:: beyond.frames.frame.TIRF
    :members:

.. autoclass:: beyond.frames.frame.ITRF
    :members:

IAU1980 based Frames
--------------------

.. autoclass:: beyond.frames.frame.EME2000
    :members:

.. autoclass:: beyond.frames.frame.MOD
    :members:

.. autoclass:: beyond.frames.frame.TOD
    :members:

.. autoclass:: beyond.frames.frame.PEF
    :members:

.. autoclass:: beyond.frames.frame.TEME
    :members:

Ground Station
--------------

Ground Station may be created using the :py:func:`~beyond.frames.frame.create_station` function. This
will ensure correct frames conversions.

.. autofunction:: beyond.frames.frame.create_station

.. autoclass:: beyond.frames.frame.TopocentricFrame
    :members:

.. Local orbital Frames
    --------------------

    .. automodule:: beyond.frames.local
        :members:
        :undoc-members:
        :show-inheritance:

Pole motion models
==================

IAU1980
-------

.. automodule:: beyond.frames.iau1980
    :members:

IAU2000
-------

.. automodule:: beyond.frames.iau2010
    :members:
