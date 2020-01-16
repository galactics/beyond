Propagators
===========

All propagators follow the :py:class:`Propagator` interface.

.. autoclass:: beyond.propagators.base.Propagator
    :members:

.. autoclass:: beyond.propagators.base.NumericalPropagator

.. autoclass:: beyond.propagators.base.AnalyticalPropagator

Kepler
------

Basic analytical Keplerian propagator, computing the position by only taking the evolution of
the mean anomaly into account.

.. automodule:: beyond.propagators.kepler
    :members:

J2
--

Analytical propagator, taking the central body effect on the orbit, and the J2 term

.. automodule:: beyond.propagators.j2
    :members:

SGP4
----

The `SGP4 <https://en.wikipedia.org/wiki/Simplified_perturbations_models>`__
is the historical model for :ref:`TLE` propagation. It allows low-precision
orbit extrapolation, but is sufficient enough for amateurs and wide-beams
antenna pointing.

There is currently two implementation available:

    * Brandon Rhodes' `sgp4 <https://github.com/brandon-rhodes/python-sgp4/>`__
    * a rewrite from scratch of the SGP4 model specifically done for this library


Brandon Rhodes'
^^^^^^^^^^^^^^^

This module provide a interface to the `sgp4` module, which is a direct adaptation
of the C++ SGP4 reference implementation. As the reference, it implements both SGP4
and SDP4 models in one interface. For these reasons, this module is to be preferred
over the rewrite.

.. automodule:: beyond.propagators.sgp4
    :members:


Rewrite
^^^^^^^

.. automodule:: beyond.propagators.sgp4beta
    :members:

Following are gravitational constants used in the SGP4 propagator, the default
being WGS72.

.. autoclass:: beyond.propagators.sgp4beta.WGS72Old
.. autoclass:: beyond.propagators.sgp4beta.WGS72
.. autoclass:: beyond.propagators.sgp4beta.WGS84

KeplerNum
---------

Basic numerical Keplerian propagator, computing the position of the next iteration by integrating
of the acceleration components applied to the satellite by numerous bodies (Earth, Moon, Sun, etc.).
This propagator is currently in development.

This propagator is able do handle maneuvers, as exposed in the :ref:`maneuvers` example.

.. automodule:: beyond.propagators.keplernum
    :members:
    :special-members: __init__
    :show-inheritance:
