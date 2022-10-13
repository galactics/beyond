from pytest import mark

from beyond.dates import Date, timedelta
from beyond.utils import ltan
from beyond.env import solarsystem


eps = 1e-14


@mark.parametrize(
    "type, expected",
    [("mean", 1.8496591694176407), ("true", 1.901700132311372)],
    ids=("mean", "true"),
)
def test_ltan2raan(common_env, type, expected):

    date = Date(2020, 1, 29, 18, 27)
    assert abs(ltan.ltan2raan(date, 22.5 * 3600, type) - expected) < eps


@mark.parametrize(
    "type, expected",
    [("mean", 0.903570175768742), ("true", 0.9741125897719947)],
    ids=("mean", "true"),
)
def test_raan2ltan(common_env, iss_tle, type, expected):

    orb = iss_tle.orbit().copy(frame="EME2000", form="keplerian")
    assert abs(ltan.raan2ltan(orb.date, orb.raan, type) / 3600 - expected) < eps
