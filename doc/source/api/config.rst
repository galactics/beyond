.. _configuration:

Configuration
=============

.. note:: Setting up a configuration, althought it will degrade the precision
    of the library, is presently optional. This may change in a future version.

The ``beyond.conf`` file contains a few fields usefull for the library
behaviour. A description of the fields is provided :ref:`here <beyondconf>`.

.. code-block:: ini

    [env]
    eop_missing_policy = "error"

You can create a directory containing the beyond.conf file and load it

.. code-block:: python

    from beyond.config import config
    config.read('/home/user/project-X/data/beyond.conf')

.. _beyondconf:

beyond.conf
-----------

This file follows the `TOML <https://github.com/toml-lang/toml>`__ specification.

env
^^^

.. _eop-missing-policy:

eop_missing_policy
    Define the behaviour of the library when encountering a missing value in the
    environment data. Current vailable behaviour are:

        * ``pass`` - Use zero as a value
        * ``extrapolate`` - Duplicate the last available data
        * ``warning`` - Same as ``extrapolate`` but issue a warning
        * ``error`` - Raise an exception

    If this variable is not set, The EnvDatabase will use :py:attr:`~beyond.dates.eop.EnvDatabase.MIS_DEFAULT`

planets_source
    This variable is optional and is only needed if you wish to track planets or other
    solar system bodies.

    It defines a list of file in which to look solar system bodies (planets, moons, comets, etc.).
    Those files should be placed in the same `env` folder as above.

    This variable may take on a coma-separated list of files::

        [env]
        platets_source = de430.bsp, mar097.bsp, jup310.bsp, sat360xl.bsp

    More information in the :py:mod:`beyond.env.jpl` module.

API
---

.. automodule:: beyond.config
    :members:
