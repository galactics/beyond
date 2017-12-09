Date handling
=============

The Date object
---------------

.. autoclass:: beyond.dates.date.Date
    :members:
    :show-inheritance:

Earth Orientation and leap second
---------------------------------

.. autofunction:: beyond.dates.eop.register

This library provide a simple (as simplistic) database implementation for Earth Orientation Parameters (EOP) : :py:class:`~beyond.dates.eop.SimpleEopDatabase`.
If you need/want another database engine, you just have to create a new
class defining a ``__getitem__`` method and regitring it under the name
you wish.

.. code-block:: python

    from beyond.dates.eop import register

    @register('sqlite')
    class SqliteEnvDatabase:

        def __getitem__(self, mjd: float):

            # retrieve data
            if data is None:
                raise KeyError(mjd)

            return data

.. autoclass:: beyond.dates.eop.SimpleEopDatabase
    :members:

In order to parse EOP input data, you can use the following classes

.. automodule:: beyond.dates.eop
    :members: Finals, Finals2000A, TaiUtc

.. autodata:: beyond.dates.eop.DEFAULT_DBNAME
.. autodata:: beyond.dates.eop.MIS_DEFAULT

Database behaviour
^^^^^^^^^^^^^^^^^^

See :ref:`configuration <eop-missing-policy>` for details on missing values response.
