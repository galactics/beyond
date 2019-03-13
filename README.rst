Beyond
======

.. image:: http://readthedocs.org/projects/beyond/badge/?version=latest
    :alt: Documentation Status
    :target: http://beyond.readthedocs.io/en/latest/?badge=latest

.. image:: https://travis-ci.org/galactics/beyond.svg?branch=master
    :alt: Tests
    :target: https://travis-ci.org/galactics/beyond

.. image:: https://coveralls.io/repos/github/galactics/beyond/badge.svg?branch=master
    :alt: Coverage Status
    :target: https://coveralls.io/github/galactics/beyond?branch=master

.. image:: https://img.shields.io/pypi/v/beyond.svg
    :alt: PyPi version
    :target: https://pypi.python.org/pypi/beyond

.. image:: https://img.shields.io/pypi/pyversions/beyond.svg
    :alt: Python versions
    :target: https://pypi.python.org/pypi/beyond

This library was started to better understand how Flight Dynamics works. It
has no intent of efficiency nor performance at the moment, and the goal is
mainly to develop a simple API for space observations.

The sources of this library can be found at `github <https://github.com/galactics/beyond>`__ and
are under the MIT license.

Installation
------------

Beyond requires Python 3.5+, numpy and `sgp4 <https://github.com/brandon-rhodes/python-sgp4>`__.
To install the library and its dependencies use pip

.. code-block:: shell

    pip install beyond

Documentation
-------------

  * `Last release <http://beyond.readthedocs.io/en/stable/>`__ (stable)
  * `Dev <http://beyond.readthedocs.io/en/latest/>`__ (latest)

Usage
-----

.. code-block:: python

    import numpy as np
    from beyond.orbits import Tle
    from beyond.frames import create_station
    from beyond.dates import Date, timedelta


    # Parse TLE
    tle = Tle("""ISS (ZARYA)
    1 25544U 98067A   19072.15347313  .00000167  00000-0  10147-4 0  9997
    2 25544  51.6420 118.6717 0004098  99.2855 123.2259 15.52799885160336""")

    # Create a station from which to compute the pass
    station = create_station('KSC', (28.524058, -80.65085, 0.0))

    for orb in station.visibility(tle.orbit(), start=Date.now(), stop=timedelta(days=1), step=timedelta(minutes=2), events=True):

        # As all angles are given in radians,
        # there is some conversion to do
        azim = -np.degrees(orb.theta) % 360
        elev = np.degrees(orb.phi)
        r = orb.r / 1000.

        print("{event:10} {tle.name}  {date:%Y-%m-%dT%H:%M:%S.%f} {azim:7.2f} {elev:7.2f} {r:10.2f}".format(
            date=orb.date, r=r, azim=azim, elev=elev,
            tle=tle, event=orb.event if orb.event is not None else ""
        ))

        # Stop at the end of the first pass
        if orb.event and orb.event.info == "LOS":
            break

This library is used as basis for the `Space-Command <https://github.com/galactics/space-command>`__ utility.

Commons usages for this library are:

  * `Predicting of satellite visibility <http://beyond.readthedocs.io/en/stable//examples.html#station-pointings>`__
  * `Computing satellite ground track <http://beyond.readthedocs.io/en/stable//examples.html#ground-track>`__
  * `Computing planets visibility <http://beyond.readthedocs.io/en/stable//examples.html#jupiter-and-its-moons>`__

References
----------

A lot of the formulas and flight dynamic algorithm are based on Vallado's
*Fundamentals of Astrodynamic and Applications* 4th ed.
