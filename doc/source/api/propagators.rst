Propagators
===========

SGP4
----

The `SGP4 <https://en.wikipedia.org/wiki/Simplified_perturbations_models>`__
is the historical model for :ref:`TLE` propagation. It allows low-precision
orbit extrapolation, but is sufficient enought for amateurs and wide-beams
antenna pointing.

There is currently two implementation available:

    * Brandon Rhodes' `sgp4 <https://github.com/brandon-rhodes/python-sgp4/>`__
    * a rewrite from scratch of the SGP4 model specifically done for this library


Brandon Rhodes'
^^^^^^^^^^^^^^^

This module provide a interface to the `sgp4` module, which is a direct adaptation
of the C++ SGP4 reference implementation. As the reference, it implements both SGP4
and SDP4 models in one interface. For these reasons, this module is to be prefered
over the rewrite.

.. automodule:: beyond.propagators.sgp4
    :members:


Rewrite
^^^^^^^

.. automodule:: beyond.propagators.sgp4beta
    :members:

Folloing are gravitional constants used in the SGP4 propagator, the default
beeing WGS72.

.. autoclass:: beyond.propagators.sgp4beta.WGS72Old
.. autoclass:: beyond.propagators.sgp4beta.WGS72
.. autoclass:: beyond.propagators.sgp4beta.WGS84

Kepler
------

Basic Keplerian propagator, computing the position of the next iteration by integrating
of the acceleration components applied to the satellite by numerous bodies (Earth, Moon, Sun, etc.).
This propagator is currently in development.