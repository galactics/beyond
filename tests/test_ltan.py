from beyond.dates import Date
from beyond.utils.ltan import ltan2raan, orb2ltan


def test_ltan2raan(common_env):

    date = Date(2020, 1, 29, 18, 27)

    assert ltan2raan(date, 22.5) == 1.8496591694176407
    assert ltan2raan(date, 22.5, "true") == 1.901700132311372


def test_raan2ltan(common_env, iss_tle):

    assert orb2ltan(iss_tle.orbit()) == 0.903570175768742
    assert orb2ltan(iss_tle.orbit(), "true") == 0.9741125897719947
