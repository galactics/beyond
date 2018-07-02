
from pytest import fixture
from unittest.mock import patch

from beyond.config import config
from beyond.dates.eop import Eop
from beyond.frames.stations import create_station
from beyond.orbits import Tle
from beyond.propagators.kepler import Kepler
from beyond.dates import Date, timedelta
from beyond.env.solarsystem import get_body


@fixture(autouse=True, scope="session")
def config_override():
    """Create a dummy config dict containing basic data
    """

    config.update({
        "eop": {
            "missing_policy": "pass",
        }
    })


@fixture
def common_env():
    with patch('beyond.dates.date.get_eop') as m:
        m.return_value = Eop(
            x=-0.00951054166666622, y=0.31093590624999734, dpsi=-94.19544791666682,
            deps=-10.295645833333051, dy=-0.10067361111115315, dx=-0.06829513888889051,
            lod=1.6242802083331438, ut1_utc=0.01756018472222477, tai_utc=36.0
        )
        yield


@fixture
def station(common_env):
    return create_station('Toulouse', (43.604482, 1.443962, 172.), delay=True)


@fixture(params=["tle", "ephem"])
def orbit(request, common_env):

    orb = Tle("""ISS (ZARYA)
1 25544U 98067A   18124.55610684  .00001524  00000-0  30197-4 0  9997
2 25544  51.6421 236.2139 0003381  47.8509  47.6767 15.54198229111731""").orbit()

    if request.param == "tle":
        return orb
    elif request.param == "ephem":
        start = Date(2018, 4, 5, 16, 50)
        stop = timedelta(hours=6)
        step = timedelta(seconds=15)

        return orb.ephem(start, stop, step)
    elif request.param == "kepler":
        orb.propagator = Kepler(
            timedelta(seconds=60),
            get_body('Earth')
        )
        return orb
