# Changelog

This file tries to regroup all notable modifications of the ``beyond`` library.
Each release is linked to a git commit.

## [v0.7.5] - 2022-10-13

### Added

- B-plane computation for planetary capture of flyby
- Generic Lagrange and linear interpolators

### Modified

- CCSDS : OEM and OMM optional fields are now optionals
- Consistency of API between impulsive and continuous thrusts
- Simplification of frame transition matrices
- Printing a TLE object display its name, if available
- CCSDS : TDM de-duplication of code

### Fixed

- CCSDS : OEM interpolation degree
- Improve error messages

## [v0.7.4] - 2022-01-15

### Added

- Altitude of periapsis/apoapsis in Info object
- Python 3.10 support
- Lagrange Points frames
- Propagators can be attached to Body objects in a clean fashion

### Modified

- Ephem interpolation is made in TAI
- W component of local orbital frames were miscomputed. The effect was very small for circular
  orbit, hence the difficulty to spot it.
- Setting an attribute of StateVector/Orbit objects is handled more robustly.
- Analytical propagators of the Sun and the Moon are now differentiated to provide velocity
- Osculating keplerian elements in CCSDS OPM can be disabled

## [v0.7.3] - 2021-07-25

### Added

- python 3.9 support and tests
- Sphere of Influence propagators (both analytical and numerical) have their own module
- ``StateVector.copy()`` now accepts "same" argument, to express two StateVector objects
  in the same form and frame.
- Maneuvers in terms of keplerian elements

### Modified

- ``beyond.orbits.man.dkep2dv()`` function has clearer arguments, is better documented
- Better exception messages when failing to parse a TLE
- Clarification of matrix building when handling rotating frames
- ``DateRange`` object simplification
- f-string everywhere
- LTAN now computed in seconds

### Fixed

- A dangling modulo messed with hyperbolic keplerian representation
- Barycentric frames correctly handled in CCSDS files

## [v0.7.2] - 2020-11-11

### Added

- equinoctial, cylindrical and mean circular forms
- OMM in SGP and TLE formats are compatibles
- A lot of small additions to the documentation of existing functions/methods

### Modified

- Following horizon format changes

### Removed

- RSW and LVLV are not synonym to QSW any more
- Disable keplerian representation of non inertial CCSDS OPM

## [v0.7.1] - 2020-09-13

### Added

- Clohessy-Wiltshire propagator for relative motion

### Modified

- Listeners are now part of the `beyond.propagators` subpackage
- Diminished precision on covariance ccsds output, for increased tests reliability

## [v0.7] - 2020-08-11

### Added

- Optional dynamic interplanetary frame via the `env.jpl.dynamic_frames` configuration variable
- Single function to retrieve local orbital reference frame rotation matrix
- Creation of the `StateVector`  class as parent of the `Orbit` class. It has
  the same behavior as `Orbit` but can't be extrapolated.
- Covariance matrix can now be expressed in a reference frame independent of its orbit.

### Modified

- The list of `bsp` and `tpc` files to read for the `beyond.env.jpl` module to work
  should be provided to the `env.jpl.files` configuration variable, instead of the previous
  `env.jpl`.
- The `beyond.utils.matrix.expand()` function now takes a single argument.
- Refactoring of `beyond.propagator.keplernum` and `beyond.orbits.man` to remove unused method argument
- Refactoring of `beyond.frames.frames` to avoid using metaclasses. This has huge code repercussions
  and affected a large number of files.
- The `skip_if_no_mpl` test decorator is replaced by `mpl`

### Fixed

- Wrong assumption on the config dict structure now leads to a ``ConfigError``
- The BSTAR drag term of the TLE format can be above 1e-1

## [v0.6.9] - 2020-04-19

### Added

- OrbitInfo for hyperbolic orbits
- Kepler and J2 analytical propagators
- Beta angle computation
- Constellation and LEO builder
- Local Time at Ascending Node computation module
- Real adaptive step size for KeplerNum propagator
- Runge-Kutta-Fehlberg method for KeplerNum
- Lambert's problem solver
- ``ccsds`` now keeps track of "USER_DEFINED" fields

### Modified

- ZeroDoppler listeners renamed as RadialVelocity
- The Kepler numerical propagator (now renamed as KeplerNum) use Ephem objects for interpolation
- NonePropagator is not used anymore when ``orb.propagator = None`` and has to be explicitly passed
- Hyperbolic orbits are much better now that their computations are simply done right
- ``find_event`` uses ``events_iterator``, and Listeners are cleaned of residual states before each iterator creation
- ``ccsds`` as a single subpackage and homogeneous internal functions

## [v0.6.8] - 2019-12-08

### Added

- NonePropagator for unmoving objects
- Eccentric anomaly form
- AnomalyListener
- find_event function
- Add python 3.8 support
- Add CCSDS XML parsing and dumping

### Modified

- Raise exception when not enough points to interpolate an ephemeris

### Removed

- Removed python 3.5 support

## [v0.6.7] - 2019-10-21

### Added

- JPL ephemeris : handle unknown objects
- Maneuvers : Continuous maneuver object

### Modified

- Maneuvers : ImpulsiveMan replace Maneuver object
- Form : Documentation of keplerian circular form now coherent with code

## [v0.6.6] - 2019-07-23

### Added

- Measures data, for orbit determination
- Common ParseError class, with specific subclasses
- [black](https://github.com/psf/black)

### Modified

- Config dict is no longer a singleton
- Use of ``math`` trigonometric functions for IAU1980 and IAU2010 computations, increases speed.

## [v0.6.5] - 2019-06-10

### Added

- Kepler propagator in `get_propagator()` scope
- Gamma50 frame
- Horizon format ephemeris parser

### Modified

- TLE and CCSDS formats regrouped under the `beyond.io` subpackage

## [v0.6.4] - 2019-03-17

### Added

- SoI : Possibility to force the frame of SoI propagator
- Date are now hashable and directly usable for plotting in matplotlib
- Propagators' iter() method accept Date iterable (allows to iter over variable step-sizes)
- Basic handling of covariance matrices
- Possibility to bypass the warning when creating a frame with a name already taken
- Tests on documentation examples

### Modified

- Kepler Propagator : Refactoring to allow any kind of numerical propagator
- Tle ndot and ndotdot parsing correction
- Change of default EOP policy to 'pass'. No more warning about missing data

## [v0.6.3] - 2019-02-23

### Added

- Tests for maneuver handling in CCSDS OPM
- OrbitInfos class for rapid orbit additional informations (velocity, perapside radius, etc.)
- Maneuvers have a optional 'comment' field, allowing to give more information
- Declare a maneuver as a increment of keplerian elements with DeltaCombined
- SOIPropagator for rapid extrapolation through multiple Sphere of Influence

### Changed

- `jpl.get_body()` now returns a Body instance and not an Orbit
- Maneuvers now check themselves for application
- The time resolution of a speaker/listener can be modified per class/instances
- 'lambda' and 'λ' are replaced by the argument of latitude u = ω + ν in the Keplerian Circular form
- A big pass over all comments and documentation regarding English

## [v0.6.2] - 2018-12-19

### Added

- Better logging integration
- Terminator detection
- QSW aliases

### Changed

- TLE epoch parsing before 2000
- Apside, Node and light listeners now computing in the propagator reference frame

## [v0.6.1] - 2018-11-01

### Added

- Visibility allow passing user listeners and merge them with station listeners
- Better describe when a wrong argument type is provided to ``Date`` constructor

### Changed

- Better ``Date`` subclass handling
- When interpolating an ``Ephem`` object, the research for the good points is faster
  due to the use of binary search, particularly when dealing with long ephemeris files

## [v0.6] - 2018-10-20

### Added

- Tle generator error handling
- Maneuvers for the Kepler propagator
- CCSDS handling of maneuvers
- Possibility to have tolerant ephems regarding date inputs
- Entry points for EOP databases registration
- JPL module now callable on bsp files for details on content
- Python 3.7 compatibility and tests
- Library custom errors
- Config set method
- Ephem object deep copy and conversions

### Changed

- Eop acquisition is done at Date creation, instead of at frame transformation
- get_body only allows one body selection at a time

### Removed

- Station propagation delay : The method was heavy and not entirely correct, if not totally wrong

## [v0.5] - 2018-05-01

### Added

- TLE tests and coverages
- Possibility to compute passes with light propagation delay taken into account
- CCSDS OEM handle multiple Ephems
- CCSDS handling of frame central body
- JPL frames bulk creation
- JPL .tpc files handling for frame central body definition
- Date.strftime
- Define a mask for a station

### Changed

- The CCSDS API now mimicks the json (load, loads, dump, dumps)
- Frames translation now directly with vectors
- Node harmonization, only one implementation used
- Stations handling has a proper module
- MIT license

## [v0.4] - 2017-12-10

### Added
- Config get() method to implement default behavior in case of missing parameter
- Documentation of orbital forms (cartesian, keplerian, etc.)
- TDB timescale
- Tle now keep any keyword argument passed in a kwargs attribute
- Others listeners can be added to a visibility computation
- Possibility to issue an error, a warning or nothing in case of missing Earth Orientation Parameters
- Possibility to define a custom Earth Orientation Parameters database

### Removed
- The config variable does not depend on a specific file anymore (previously ConfigParser, then TOML)
  but is a dictionary

### Changed
- replacement of incorrect 'pole_motion' functions and variables names for
  'earth_orientation'
- Moon analytic position now computed with respect to TDB timescale
- A Listener does not return a string anymore, but an Event object
- Tests are now conducted by tox

## [v0.3] - 2017-06-27

### Added
- Integration of JPL ephemeris by interfacing Brandon Rhodes' [jplephem](https://github.com/brandon-rhodes/python-jplephem) python library
- First try at RK4 numerical propagator
- Listeners for events computation (AOS, LOS, umbra, etc.)
- CCSDS Orbit Data Message reading and writing
- Multi TLE parser (#18)
- frames now declare a central body, with some characteristics (#20)

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

Initial release with basic functionalities
