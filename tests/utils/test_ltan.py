from beyond.dates import Date
from beyond.utils.ltan import ltan2raan, orb2ltan


eps = 1e-14

def test_ltan2raan(common_env):

    date = Date(2020, 1, 29, 18, 27)

    assert abs(ltan2raan(date, 22.5) - 1.8496591694176407) < eps
    assert abs(ltan2raan(date, 22.5, "true") - 1.901700132311372) < eps


def test_raan2ltan(common_env, iss_tle):

    assert abs(orb2ltan(iss_tle.orbit()) - 0.903570175768742) < eps
    assert abs(orb2ltan(iss_tle.orbit(), "true") - 0.9741125897719947) < eps
