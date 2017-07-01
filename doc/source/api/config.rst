.. _configuration:

Configuration
=============

.. note:: Setting up a configuration, althought it will degrade the precision
    of the library, is presently optional. This may change in a future version.

The ``beyond.conf`` file contains a few fields usefull for the library
behaviour. A description of the fields is provided :ref:`here <beyondconf>`.

.. code-block:: ini

    [env]
    pole_motion_source = all

You can create a directory containing the beyond.conf file and load it

.. code-block:: python

    from beyond.config import config
    config.load('/home/user/project-X/data/')
    # or
    config.load('/home/user/project-X/data/beyond.conf')

.. _beyondconf:

beyond.conf
-----------

env
^^^

pole_motion_source
    Either ``all`` or ``daily`` depending on the files you want to use for pole motion
    model correction.

    These are necessary for precision of frame transformations and date handling

        - finals.all
        - finals2000A.all
        - finals.daily
        - finals2000A.daily
        - tai-utc.dat

    The differences between the ``.daily`` and ``.all`` files, explained `here <http://maia.usno.navy.mil/ser7/readme>`__, are mainly about freshness and timespan.
    They are available on the `US Naval Observatory <http://maia.usno.navy.mil/ser7/>`__
    web server. 
    In order to use them into the Space-API library, you should place them into
    the following file tree::

        data/
         |_ beyond.conf
         |_ env/
             |_ finals.all
             |_ finals2000A.all
             |_ tai-tuc.dat

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
