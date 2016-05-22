Propagators
===========

SGP4
----

The `SGP4 <https://en.wikipedia.org/wiki/Simplified_perturbations_models>`__
is the historical model for :ref:`TLE` propagation. It allows low-precision
orbit extrapolation, but is sufficient enought for amateurs and wide-beams
antenna pointing.

.. automodule:: space.propagators.sgp4
    :members:

Folloing are gravitional constants used in the SGP4 propagator, the default
beeing WGS72.

.. autoclass:: space.propagators.sgp4.WGS72Old
.. autoclass:: space.propagators.sgp4.WGS72
.. autoclass:: space.propagators.sgp4.WGS84