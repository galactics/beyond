.. _configuration:

Configuration
=============

The configuration of the library is handled via a dictionary.
It is accessible via::

    from beyond.config import config
    print(config)

In order to dynamically modify values of the dictionary, it is preferable
to use the :py:meth:`~Config.update` method.

The configuration dictionary contains a few fields useful for the library
behavior. A description of the fields is provided :ref:`here <beyondconf>`.

.. _beyondconf:

Config dict specification
-------------------------

eop
^^^
.. _eop-missing-policy:

missing_policy
    Define the behavior of the library when encountering a missing value in the
    environment data. Current variable behavior are:

        * ``pass`` - Use zero as a value
        * ``warning`` - Same as ``extrapolate`` but issue a warning
        * ``error`` - Raise an exception

    If this variable is not set, the library will use
    :py:data:`~beyond.dates.eop.EopDb.MIS_DEFAULT`

.. _eop-dbname:

dbname
    Define the database used by the library in order to retrieve model
    corrections and time-scales differences. See :py:mod:`~beyond.dates.eop`.
    If omitted, the default database will be
    :py:data:`~beyond.dates.eop.EopDb.DEFAULT_DBNAME`

env
^^^

jpl
    This variable is optional and is only needed if you wish to track planets or
    other solar system bodies.

    Defines a list of BSP files in which to look solar system bodies (planets,
    moons, comets, etc.). de430.bsp, mar097.bsp, jup310.bsp, sat360xl.bsp

    More information in the :py:mod:`beyond.env.jpl` module.

API
---

.. automodule:: beyond.config
    :members:
