Space API
=========

[![Documentation Status](http://readthedocs.org/projects/space-api/badge/?version=latest)](http://space-api.readthedocs.io/en/latest/?badge=latest)
[![Tests](https://travis-ci.org/galactics/space-api.svg?branch=master)](https://travis-ci.org/galactics/space-api)
[![Coverage Status](https://coveralls.io/repos/github/galactics/space-api/badge.svg?branch=master)](https://coveralls.io/github/galactics/space-api?branch=master)

This library was started to better understand how Flight Dynamics works. It
has no intent of efficiency nor performance at the moment, and the goal is
mainly to develop a simple API for space observations.

The sources of this library can be found at [github](https://github.com/galactics/space-api)

Installation
------------

Space API only requires Python 3.5+, numpy and [sgp4](https://github.com/brandon-rhodes/python-sgp4). To install it use pip

    pip install space-api

Documentation
-------------

The documentation of the library can be found [here](http://space-api.readthedocs.io/en/latest/).

Usage
-----

You can find some usage in the official documentation at [this page](http://space-api.readthedocs.io/en/latest//examples.html).

Commons usages are:

*   Predicting of satellite visibility
*   Computing satellite ground track

References
----------

A lot of the formulas and flight dynamic algorithm are based on Vallado's
_Fundamentals of Astrodynamic and Applications_ 4th ed.