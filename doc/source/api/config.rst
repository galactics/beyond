.. _configuration:

Configuration
=============

You need to get a few files in order to get things rolling. They are
necessary for precision of frame transformations and date handling

    - finals.all
    - finals2000A.all
    - tai-utc.dat

These files are available on the `US Naval Observatory <http://maia.usno.navy.mil/ser7/>`__
web server. 
In order to use them into the Space-API library, you should place them into
the following file tree::

    data/
     |_ space.ini
     |_ env/
         |_ finals.all
         |_ finals2000A.all
         |_ tai-tuc.dat

The ``space.ini`` file contains a few fields usefull for default library
behaviour. A description of the fields is provided :ref:`here <spaceini>`.

.. code-block:: ini

    [env]
    pole_motion_source = all

Then you can either create the directory and load it by hand

.. code-block:: python

    from space.config import config
    config.load('/home/user/project-X/data/')

or create a ``.space`` directory directly in your home and containing the same
tree as above.

.. code-block:: text

    /home/
     |_ user/
         |_ .space/
             |_ space.ini
             |_ env/
                 |_ finals.all
                 |_ finals2000A.all
                 |_ tai-tuc.dat

Config
------

.. automodule:: space.config
    :members:

.. _spaceini:

space.ini
---------

pole_motion_source
    Either ``all`` or ``daily`` depending on the files you use for pole motion
    model correction.
