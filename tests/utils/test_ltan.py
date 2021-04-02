from beyond.dates import Date, timedelta
from beyond.utils import ltan
from beyond.env import solarsystem


eps = 1e-14


def test_ltan2raan(common_env):

    date = Date(2020, 1, 29, 18, 27)

    assert abs(ltan.ltan2raan(date, 22.5 * 3600) - 1.8496591694176407) < eps
    assert abs(ltan.ltan2raan(date, 22.5 * 3600, "true") - 1.901700132311372) < eps


def test_raan2ltan(common_env, iss_tle):

    orb = iss_tle.orbit().copy(frame="EME2000", form="keplerian")

    assert abs(ltan.raan2ltan(orb.date, orb.raan) / 3600 - 0.903570175768742) < eps
    assert abs(ltan.raan2ltan(orb.date, orb.raan, "true") / 3600 - 0.9741125897719947) < eps
