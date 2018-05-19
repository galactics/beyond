
from pytest import yield_fixture, fixture
from unittest.mock import patch

from beyond.config import config
from beyond.dates.eop import Eop
from beyond.frames.stations import create_station


@fixture(autouse=True, scope="session")
def config_override():
    """Create a dummy config dict containing basic data
    """

    config.update({
        "eop": {
            "missing_policy": "pass",
        }
    })


@yield_fixture(scope='session')
def station_env():
    with patch('beyond.frames.iau1980.get_eop') as m, patch('beyond.dates.date.get_eop') as m2:
        m.return_value = Eop(
            x=-0.00951054166666622, y=0.31093590624999734, dpsi=-94.19544791666682, deps=-10.295645833333051,
            dy=-0.10067361111115315, dx=-0.06829513888889051, lod=1.6242802083331438,
            ut1_utc=0.01756018472222477, tai_utc=36.0
        )
        m2.return_value = m.return_value

        yield


@fixture(scope='session')
def station(station_env):
    return create_station('Toulouse', (43.604482, 1.443962, 172.), delay=True)
