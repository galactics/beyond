from pytest import mark

from beyond.dates import Date, timedelta
from beyond.env import jpl
from beyond.io import ccsds
from beyond.propagators.analytical import SoIAnalytical
from beyond.propagators.numerical import SoINumerical


opm_with_man = """CCSDS_OPM_VERS = 2.0
CREATION_DATE = 2019-02-22T23:22:31
ORIGINATOR = N/A

META_START
OBJECT_NAME          = N/A
OBJECT_ID            = N/A
CENTER_NAME          = EARTH
REF_FRAME            = EME2000
TIME_SYSTEM          = UTC
META_STOP

COMMENT  State Vector
EPOCH                = 2018-05-02T00:00:00.000000
X                    =  6678.000000 [km]
Y                    =     0.000000 [km]
Z                    =     0.000000 [km]
X_DOT                =     0.000000 [km/s]
Y_DOT                =     7.088481 [km/s]
Z_DOT                =     3.072802 [km/s]

COMMENT  Keplerian elements
SEMI_MAJOR_AXIS      =  6678.000000 [km]
ECCENTRICITY         =     0.000000
INCLINATION          =    23.436363 [deg]
RA_OF_ASC_NODE       =     0.000000 [deg]
ARG_OF_PERICENTER    =     0.000000 [deg]
TRUE_ANOMALY         =     0.000000 [deg]

COMMENT  Escaping Earth
MAN_EPOCH_IGNITION   = 2018-05-02T00:39:03.955092
MAN_DURATION         = 0.000 [s]
MAN_DELTA_MASS       = 0.000 [kg]
MAN_REF_FRAME        = TNW
MAN_DV_1             = 3.456791 [km/s]
MAN_DV_2             = 0.000000 [km/s]
MAN_DV_3             = 0.000000 [km/s]
"""

opm_without_man = """CCSDS_OPM_VERS = 2.0
CREATION_DATE = 2021-02-10T22:22:15.320723
ORIGINATOR = N/A

META_START
OBJECT_NAME          = N/A
OBJECT_ID            = N/A
CENTER_NAME          = EARTH
REF_FRAME            = EME2000
TIME_SYSTEM          = UTC
META_STOP

COMMENT  State Vector
EPOCH                = 2018-05-02T00:45:03.955092
X                    = -6822.384678 [km]
Y                    =  -492.535719 [km]
Z                    =  -213.510446 [km]
X_DOT                =    -0.873741 [km/s]
Y_DOT                =   -10.012250 [km/s]
Z_DOT                =    -4.340233 [km/s]

COMMENT  Keplerian elements
SEMI_MAJOR_AXIS      = -118795.753786 [km]
ECCENTRICITY         =     1.056211
INCLINATION          =    23.436361 [deg]
RA_OF_ASC_NODE       =   360.000000 [deg]
ARG_OF_PERICENTER    =   166.832186 [deg]
TRUE_ANOMALY         =    17.666887 [deg]
GM                   = 398600.9368 [km**3/s**2]
"""


@mark.jpl
@mark.parametrize("method", ["analytical", "numerical"])
def test_soi(jplfiles, method):

    planetary_step = timedelta(seconds=180)
    solar_step = timedelta(hours=12)

    jpl.create_frames()

    central = jpl.get_body('Sun')
    planets = jpl.get_body('Earth')

    if method == "numerical":
        propagator = SoINumerical(solar_step, planetary_step, central, planets)
        txt = opm_with_man
    else:
        propagator = SoIAnalytical(central, planets)
        propagator.step = solar_step
        txt = opm_without_man

    opm = ccsds.loads(txt).as_orbit(propagator)

    # d, r = [], []
    frames = set()
    for orb in opm.iter(stop=timedelta(5)):
        frames.add(orb.frame.name)
    #     r.append(orb.copy(frame="EME2000", form="spherical").r)
    #     d.append(orb.date)

    # import matplotlib.pyplot as plt
    # plt.plot(d, r)
    # plt.show()

    assert not frames.symmetric_difference(['Sun', 'EME2000'])

    # Check if the last point is out of Earth sphere of influence
    assert orb.copy(frame='EME2000', form="spherical").r > SoINumerical.SOIS['Earth'].radius
