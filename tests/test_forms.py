
from pytest import fixture
import numpy as np

from beyond.dates import Date
from beyond.orbits import Orbit
from beyond.orbits.forms import TLE, KEPL_C, KEPL_M, KEPL, SPHE, CART


@fixture
def ref_date():
    return Date(2015, 9, 21, 12)


@fixture
def ref_kepl_m(ref_date):
    ref_coord = [
        7192631.11295, 0.00218439, np.deg2rad(98.50639978),
        np.deg2rad(315.72521309), np.deg2rad(67.54633938), np.deg2rad(174.37062038)
    ]
    ref_form = KEPL_M
    ref_frame = "EME2000"
    ref_propagator = 'Sgp4'
    return Orbit(ref_date, ref_coord, ref_form, ref_frame, ref_propagator)


@fixture
def ref_kepl(ref_date):

    return Orbit(
        ref_date,
        [
            7192631.11295, 0.00218439, 1.71926101045,
            5.51044449998, 1.17890601985, 3.04376883055,
        ],
        KEPL,
        "EME2000",
        "Sgp4"
    )


@fixture
def ref_cart(ref_date):
    return Orbit(
        ref_date,
        [
            -1.77079285e+06, 3.04066799e+06, -6.29108469e+06,
            5.05386814e+03, -4.20539932e+03, -3.45695948e+03
        ],
        CART,
        "EME2000",
        "Sgp4"
    )


@fixture
def ref_sphe(ref_date):
    return Orbit(
        ref_date,
        [
            7.20826718e+06, 2.09815148e+00, -1.06082733e+00,
            1.58820333e+00, -6.39690485e-04, -9.82054932e-04
        ],
        SPHE,
        "EME2000",
        "Sgp4"
    )


@fixture
def ref_kepl_c(ref_date):
    return Orbit(
        ref_date,
        [
            7.19263111e+06, 8.34297391e-04, 2.01878863e-03,
            1.71926101e+00, 5.51044450e+00, 4.22224746e+00
        ],
        KEPL_C,
        "EME2000",
        "Sgp4"
    )


@fixture
def ref_tle(ref_date):
    return Orbit(
        ref_date,
        [
            1.71926101e+00, 5.51044450e+00, 2.18439000e-03,
            1.17890602e+00, 3.04334144e+00, 1.03499315e-03
        ],
        TLE,
        "EME2000",
        "Sgp4"
    )


def test_same(ref_kepl_m):
    keplm = KEPL_M(ref_kepl_m, KEPL_M)
    assert (keplm == ref_kepl_m.base).all()


def test_kepl_m(ref_kepl_m):
    kep = KEPL_M(ref_kepl_m, "keplerian")
    assert np.allclose(kep, [
        7.19263111e+06, 2.18439000e-03, 1.71926101e+00,
        5.51044450e+00, 1.17890602e+00, 3.04376883e+00
    ])

    tle = KEPL_M(ref_kepl_m, TLE)
    assert np.allclose(tle, [
        1.71926101e+00, 5.51044450e+00, 2.18439000e-03,
        1.17890602e+00, 3.04334144e+00, 1.03499315e-03
    ])

    # Small mean anomaly
    kepl_m = ref_kepl_m.copy()
    kepl_m[-1] = 0.1
    kep = KEPL_M(kepl_m, KEPL)
    assert np.allclose(kep, [
        7.19263111e+06, 2.18439000e-03, 1.71926101e+00,
        5.51044450e+00, 1.17890602e+00, 1.00437338e-01
    ])

    # Negative mean anomaly
    kepl_m = ref_kepl_m.copy()
    kepl_m[-1] = -kepl_m[-1]
    kep = KEPL_M(kepl_m, KEPL)
    assert np.allclose(kep, [
        7.19263111e+06, 2.18439000e-03, 1.71926101e+00,
        5.51044450e+00, 1.17890602e+00, 3.23941648e+00
    ])

    kepl_m = ref_kepl_m.copy()
    kepl_m[-1] = 0.0001
    kepl_m[1] = 0.95
    kep = KEPL_M(kepl_m, KEPL)
    assert np.allclose(kep, [
        7.19263111e+06, 9.50000000e-01, 1.71926101e+00,
        5.51044450e+00, 1.17890602e+00, 1.24896796e-02
    ])


def test_kepl(ref_kepl):
    keplm = KEPL(ref_kepl, KEPL_M)
    assert np.allclose(keplm, [
        7.19263111e+06, 2.18439000e-03, 1.71926101e+00,
        5.51044450e+00, 1.17890602e+00, 3.04334144e+00
    ])

    cart = KEPL(ref_kepl, CART)
    assert np.allclose(cart, [
        -1.77079285e+06, 3.04066799e+06, -6.29108469e+06,
        5.05386814e+03, -4.20539932e+03, -3.45695948e+03
    ])

    kepc = KEPL(ref_kepl, KEPL_C)
    assert np.allclose(kepc, [
        7.19263111e+06, 8.34297391e-04, 2.01878863e-03,
        1.71926101e+00, 5.51044450e+00, 4.22267485e+00
    ])

    # Hyperbolic case
    ref_kepl_h = ref_kepl.copy()
    ref_kepl_h[1] = 1.2
    ref_kepl_h[-1] = 0.2
    keplm_h = KEPL(ref_kepl_h, KEPL_M)
    assert np.allclose(keplm_h, [
        7.19263111e+06, 1.20000000e+00, 1.71926101e+00,
        5.51044450e+00, 1.17890602e+00, 1.21488570e-02
    ])


def test_cart(ref_cart):
    kepl = CART(ref_cart, KEPL)
    assert np.allclose(kepl, [
        7.19263111e+06, 2.18438989e-03, 1.71926101e+00,
        5.51044450e+00, 1.17890554e+00, 3.04376931e+00
    ])

    sph = CART(ref_cart, SPHE)
    assert np.allclose(sph, [
        7.20826718e+06, 2.09815148e+00, -1.06082733e+00,
        1.58820333e+00, -6.39690485e-04, -9.82054932e-04
    ])


def test_sphe(ref_sphe):
    cart = SPHE(ref_sphe, CART)
    assert np.allclose(cart, [
        -1.77079286e+06, 3.04066800e+06, -6.29108469e+06,
        5.05386814e+03, -4.20539931e+03, -3.45695949e+03
    ])


def test_kepl_c(ref_kepl_c):
    kepl = KEPL_C(ref_kepl_c, KEPL)
    assert np.allclose(kepl, [
        7.19263111e+06, 2.18439000e-03, 1.71926101e+00,
        5.51044450e+00, 1.17890602e+00, 3.04334144e+00
    ])


def test_tle(ref_tle):
    keplm = TLE(ref_tle, KEPL_M)
    assert np.allclose(keplm, [
        7.19263113e+06, 2.18439000e-03, 1.71926101e+00,
        5.51044450e+00, 1.17890602e+00, 3.04334144e+00
    ])
