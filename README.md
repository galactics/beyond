Beyond
======

[![Documentation Status](http://readthedocs.org/projects/beyond/badge/?version=latest)](http://beyond.readthedocs.io/en/latest/?badge=latest)
[![Tests](https://travis-ci.org/galactics/beyond.svg?branch=master)](https://travis-ci.org/galactics/beyond)
[![Coverage Status](https://coveralls.io/repos/github/galactics/beyond/badge.svg?branch=master)](https://coveralls.io/github/galactics/beyond?branch=master)
[![PyPi version](https://img.shields.io/pypi/v/beyond.svg)](https://pypi.python.org/pypi/beyond)
[![Python versions](https://img.shields.io/pypi/pyversions/beyond.svg)](https://pypi.python.org/pypi/beyond)

This library was started to better understand how Flight Dynamics works. It
has no intent of efficiency nor performance at the moment, and the goal is
mainly to develop a simple API for space observations.

The sources of this library can be found at [github](https://github.com/galactics/beyond)

Installation
------------

Beyond requires Python 3.5+, numpy and [sgp4](https://github.com/brandon-rhodes/python-sgp4). To install it use pip

    pip install beyond

Documentation
-------------

The documentation of the library can be found [here](http://beyond.readthedocs.io/en/latest/).

Usage
-----

Commons usages are:

*   [Predicting of satellite visibility](http://beyond.readthedocs.io/en/latest//examples.html#station-pointings)
*   [Computing satellite ground track](http://beyond.readthedocs.io/en/latest//examples.html#ground-track)
*   [Computing planets visibility](http://beyond.readthedocs.io/en/latest//examples.html#jupiter-and-its-moons)

References
----------

A lot of the formulas and flight dynamic algorithm are based on Vallado's
_Fundamentals of Astrodynamic and Applications_ 4th ed.
