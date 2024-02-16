import numpy as np
from numpy.testing import assert_almost_equal

from beyond.utils.interplanetary import bplane, flyby
from beyond.constants import Earth
from beyond.dates import Date
from beyond.orbits import StateVector


def test_bplane():
    orbit = StateVector(
        [
            -1.78049834e06,
            7.50919028e06,
            6.87709673e00,
            -2.83902560e03,
            -6.73742129e02,
            1.05000000e04,
        ],
        Date(2024, 2, 16, 20, 36, 47, 492064),
        "cartesian",
        "CIRF",
    )

    B, θ, S, T, R, e, h = bplane(orbit)

    assert_almost_equal(B, [1136488.0966131, 14306186.7319276, -15856616.57573])
    assert np.degrees(θ) == 70.14408368375359
    assert_almost_equal(S, [-0.3439139, 0.7093105, 0.6153062])
    assert_almost_equal(T, [0.8998112, 0.4362795, -0.0])
    assert_almost_equal(R, [-0.2684455, 0.5536594, -0.7882882])
    assert_almost_equal(e, [-2.9982143e-01, 1.2643499e00, 1.1456790e-04])
    assert_almost_equal(h, [78846502573.38979, 18695213045.74633, 22518380182.463737])


def test_flyby():
    v_inf_in = np.array([4800, 0, 0])
    v_inf_out = np.array([0, 4800, 0])

    B, rp = flyby(v_inf_in, v_inf_out, Earth.µ)

    zp = rp - Earth.r
    assert zp == 787_918.9957261235
    assert_almost_equal(B, [0.0, -17300387.8836575, 0.0])
