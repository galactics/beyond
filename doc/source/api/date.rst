Date handling
=============

The Date object
---------------

.. autoclass:: beyond.dates.date.Date
    :members:
    :show-inheritance:

Earth Orientation and leap second
---------------------------------

.. autoclass:: beyond.dates.eop.EnvDatabase
    :members:

Database behaviour
^^^^^^^^^^^^^^^^^^

See :ref:`configuration <eop-missing-policy>` for details on missing values response.

Usage
^^^^^

.. code-block:: python

    from beyond.date.eop import EnvDatabase, Finals, Finals2000A, TaiUTC

    iau1980 = "/path/to/finals.daily"
    iau2010 = "/path/to/finals2000A.daily"
    tai_utc = "/path/to/tai-utc.dat"

    EnvDatabase.insert(finals=iau2980, finals2000A=iau2010, tai_utc=tai_utc)