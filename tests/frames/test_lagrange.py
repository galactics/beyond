from pathlib import Path
from pytest import mark, fixture

from beyond.env import solarsystem as sol
from beyond.frames.lagrange import lagrange, LagrangeOrient
from beyond.io import ccsds
from beyond.dates import Date, timedelta
from beyond.propagators.numerical import KeplerNum
from beyond.frames.orient import EME2000


@fixture
def gaia_oem():
    """Gaia Ephem in EME2000"""
    filepath = Path(__file__).parent.joinpath("data/gaia.oem")
    return ccsds.load(filepath.open()) 


@fixture
def gaia_opm(gaia_oem):
    """An orbit object extracted from the previous Ephem"""
    return gaia_oem[0]


@mark.parametrize("orient", ("synodic", "EME2000"))
@mark.parametrize("kind", list(range(1, 6)))
def test_solarsystem(gaia_opm, kind, orient, helper):

    if orient == "synodic":
        orient_obj = None
        frame_name = f"SunEarthLagrange"
    else:
        orient_obj = EME2000
        frame_name = "EME2000"

    f_earth = sol.get_frame("Earth")
    f_sun = sol.get_frame("Sun")
    fl = lagrange(f_sun, f_earth, kind, orientation=orient_obj)

    assert fl.name == f"SunEarthL{kind}"
    assert fl.center.name == f"SunEarthL{kind}"
    assert fl.center.body is None
    assert fl.orientation.name == frame_name
    
    if orient_obj is None:
        assert isinstance(fl.orientation, LagrangeOrient)
    else:
        assert fl.orientation == EME2000

    opm = gaia_opm.copy(frame=fl)
    opm2 = opm.copy(frame="EME2000")

    filepath = Path(__file__).parent.joinpath(f"data/L{kind}-{orient}.opm")
    ref = ccsds.load(filepath.open())

    helper.assert_orbit(opm, ref)
