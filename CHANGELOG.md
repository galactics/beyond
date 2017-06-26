# Changelog

This file tries to regroup all notable modifications of the ``beyond`` library.
Each release is linked to a git commit.

## [Unreleased]

### Added
- Integration of JPL ephemeris by interfacing Brandon Rhodes' [jplephem](https://github.com/brandon-rhodes/python-jplephem) python library
- First try at RK4 numerical propagator
- Listeners for events computation (AOS, LOS, umbra, etc.)
- CCSDS Orbit Data Message reading and writing
- Multi TLE parser (#18)
- frames now declare a central body, with some caracteristics (#20)

### Changed
- Spherical parameters orders (now r, theta, phi)
- Propagators are now instances instead of classes
- ``solarsystem`` module

### Fixed
- Correction of velocity computation when switching from cartesian to spherical
- COSPAR ID parsing in TLE

## [v0.2.1] - 2017-03-09

Change the name of the library to beyond (formerly space-api)

## [v0.2] - 2017-03-04

### Added
- CIO based frames (#1)
- Ephem object (#3)
- Full SGP4/SDP4 propagator, by interfacing Brandon Rhodes' [sgp4](https://github.com/brandon-rhodes/python-sgp4) python library (#4)
- Python classifiers for PyPI (#8)
- Lagrange Interpolation in Ephem objects (#15)

### Changed
- Date inner values in TAI (#13)

### Fixed
- Ordering of Node2 graphs (#2)

## [v0.1] - 2016-05-22

Initial release with basic functionnalities