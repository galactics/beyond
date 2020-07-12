import numpy as np
from pytest import mark

from beyond.utils.beta import beta, beta_limit
from beyond.env.jpl import get_body


def test_beta(iss_tle):

    orbit = iss_tle.orbit()

    beta_ = beta(orbit)
    beta_lim = beta_limit(orbit)

    assert np.isclose(beta_, -0.018861895899919556)
    assert np.isclose(beta_lim, 1.2243289463926432)


@mark.jpl
def test_beta_mars(jplfiles, iss_tle):

    # Test with another body than the sun
    beta_mars = beta(iss_tle.orbit(), get_body("Mars"))

    assert np.isclose(beta_mars, -1.059116181654628)
