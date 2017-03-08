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

You can either create a directory containing the beyond.conf file and load it by hand

.. code-block:: python

    from beyond.config import config
    config.load('/home/user/project-X/data/')
    # or
    config.load('/home/user/project-X/data/beyond.conf')

or create a ``.beyond`` directory directly in your home, containing the :ref:`beyondconf`
file, which will be automatically loaded.

.. code-block:: text

    /home/
     |_ user/
         |_ .beyond/
             |_ beyond.conf

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

API
---

.. automodule:: beyond.config
    :members:
