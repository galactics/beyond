Date handling
=============

The Date object
---------------

.. autoclass:: beyond.dates.date.Date
    :members: datetime, mjd, jd, now, change_scale, strftime, strptime, range

.. autoclass:: beyond.dates.date.DateRange
    :members: start, stop, step, inclusive, dur

.. _eop:

Earth Orientation and leap second
---------------------------------

Input data
^^^^^^^^^^

In order to parse Earth Orientation Parameters (EOP) input data, you can use the
following classes

.. autoclass:: beyond.dates.eop.Finals
.. autoclass:: beyond.dates.eop.Finals2000A
.. autoclass:: beyond.dates.eop.TaiUtc

Databases
^^^^^^^^^

Beyond provides a simple (as simplistic) database implementation for EOP :
:py:class:`~beyond.dates.eop.SimpleEopDatabase`.

.. autoclass:: beyond.dates.eop.SimpleEopDatabase
    :members:


If you need/want another database engine, you just have to create a new class
defining a ``__getitem__`` method and register it under the name you wish.

There is two methods for registering a database. The first one, is via the
:py:func:`~beyond.dates.eop.register` decorator

.. code-block:: python

    from beyond.dates.eop import register

    @register('sqlite')
    class SqliteEnvDatabase:

        def __getitem__(self, mjd: float):

            # retrieve data
            if data is None:
                raise KeyError(mjd)

            return data

The second is via the `entry point <https://setuptools.readthedocs.io/en/latest/pkg_resources.html#entry-points>`__ ``beyond.eopdb``.

If you create a python package that contain an EOP database, you can declare
that database directly during install time.
For that, in the *setup.py* file of your package, you have to provide the import
path to this database in the following fashion:

.. code-block:: python

    from setuptools import setup

    setup(
        name=mypackage,
        version="12.4.beta",
        description="My awesome package",
        author="John Doe",
        ...
        entry_points={
            'beyond.eopdb': [
                "my_personnal_db = mypackage.module:MyDatabase"
            ]
        }
    )

This way, the class ``MyDatabase`` will always be available to the beyond
library, and will be instantiated if needed (i.e. if the :ref:`dbname config
variable <eop-dbname>` is set to "*my_personnal_db*").

Internals
^^^^^^^^^

In order to access different databases with the same interface, beyond uses the
:py:class:`~beyond.dates.eop.EopDb` class.
It is this class that handle registered databases, and select the activated one.

.. autoclass:: beyond.dates.eop.EopDb
    :members:

.. autofunction:: beyond.dates.eop.register
