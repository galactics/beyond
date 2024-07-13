
from pytest import fixture
import numpy as np

from beyond.dates import Date
from beyond.orbits import StateVector
from beyond.orbits.forms import TLE, KEPL_E, KEPL_C, KEPL_M, KEPL, SPHE, CART, EQUI, CYL, KEPL_MC


@fixture
def ref_date():
    return Date(2015, 9, 21, 12)


@fixture
def ref_kepl_m(ref_date):
    return StateVector(
        [
            7192631.11295, 0.00218439, np.deg2rad(98.50639978),
            np.deg2rad(315.72521309), np.deg2rad(67.54633938), np.deg2rad(174.37062038)
        ],
        ref_date,
        KEPL_M,
        "EME2000"
    )

@fixture
def ref_kepl(ref_date):

    return StateVector(
        [
            7192631.11295, 0.00218439, 1.71926101045,
            5.51044449998, 1.17890601985, 3.04376883055,
        ],
        ref_date,
        KEPL,
        "EME2000"
    )


@fixture
def ref_cart(ref_date):
    return StateVector(
        [
            -1.77079285e+06, 3.04066799e+06, -6.29108469e+06,
            5.05386814e+03, -4.20539932e+03, -3.45695948e+03
        ],
        ref_date,
        CART,
        "EME2000"
    )


@fixture
def ref_sphe(ref_date):
    return StateVector(
        [
            7.20826718e+06, 2.09815148e+00, -1.06082733e+00,
            1.58820333e+00, -6.39690485e-04, -9.82054932e-04
        ],
        ref_date,
        SPHE,
        "EME2000"
    )


@fixture
def ref_kepl_c(ref_date):
    return StateVector(
        [
            7.19263111e+06, 8.34297391e-04, 2.01878863e-03,
            1.71926101e+00, 5.51044450e+00, 4.22224746e+00
        ],
        ref_date,
        KEPL_C,
        "EME2000"
    )


@fixture
def ref_tle(ref_date):
    return StateVector(
        [
            1.71926101e+00, 5.51044450e+00, 2.18439000e-03,
            1.17890602e+00, 3.04334144e+00, 1.03499315e-03
        ],
        ref_date,
        TLE,
        "EME2000"
    )


@fixture
def ref_kepl_hyper(ref_date):
    return StateVector(
        [
            -7192631.11295, 1.00218439, 1.71926101045,
            5.51044449998, 1.17890601985, 0.1,
        ],
        ref_date,
        KEPL,
        "EME2000"
    )


@fixture
def ref_equi(ref_date):
    return StateVector(
        [
            7.19263111e+06,  2.00667384e-03,  8.63029427e-04,
            8.31052761e-01, -8.10276759e-01,  9.73311935e+00
        ],
        ref_date,
        EQUI,
        "EME2000"
    )


@fixture
def ref_cyl(ref_date):
    return StateVector(
        [
            3.51871697e+06,  2.09815148e+00, -6.29108469e+06,
            -6.17741547e+03, -6.39690485e-04, -3.45695948e+03
        ],
        ref_date,
        CYL,
        "EME2000"
    )


@fixture
def ref_kepl_mc(ref_date):
    return StateVector(
        [
            7.19263111e+06, 8.34297391e-04, 2.01878863e-03,
            1.71926101e+00, 5.51044450e+00, 4.22224746e+00
        ],
        ref_date,
        KEPL_MC,
        "EME2000"
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


def test_hyperbolic(ref_kepl_hyper):

    def to_sv(arr, form):
        return StateVector(
            arr,
            ref_kepl_hyper.date,
            form,
            ref_kepl_hyper.frame,
        )

    # To cartesian ...
    cart = to_sv(KEPL(ref_kepl_hyper, CART), CART.name)
    assert np.allclose(cart.base, [
        1687.60352732, -4761.78462622, 14918.72031867,
        -159632.45044557, 140048.25302776, 74649.10622557
    ])

    # ... and back
    kepl_h = CART(cart, KEPL)
    assert np.allclose(kepl_h, ref_kepl_hyper.base)

    # To keplerian eccentric ...
    kepl_e = to_sv(KEPL(ref_kepl_hyper, KEPL_E), KEPL_E.name)
    assert np.allclose(kepl_e.base, [
        -7.19263111e+06, 1.00218439e+00, 1.71926101e+00,
        5.51044450e+00, 1.17890602e+00, 3.30579237e-03
    ])

    # ... and back
    kepl_h = to_sv(KEPL_E(kepl_e, KEPL), KEPL.name)
    assert np.allclose(kepl_h.base, ref_kepl_hyper.base)

    # To Keplerian mean ...
    kepl_m = to_sv(KEPL_E(kepl_e, KEPL_M), KEPL_M.name)
    assert np.allclose(kepl_m.base, [
        -7.19263111e+06, 1.00218439e+00, 1.71926101e+00,
        5.51044450e+00, 1.17890602e+00, 7.22717405e-06
    ])

    # ... and back
    kepl_e2 = to_sv(KEPL_M(kepl_m, KEPL_E), KEPL_E.name)
    assert np.allclose(kepl_e.base, kepl_e2.base)


def test_equinoctial(ref_kepl, ref_equi):

    equi = KEPL(ref_kepl, EQUI)
    assert np.allclose(ref_equi.base, equi)

    kepl = EQUI(ref_equi, KEPL)
    assert np.allclose(ref_kepl.base, kepl)


def test_cylindrical(ref_cart, ref_cyl):

    cyl = CART(ref_cart, CYL)
    assert np.allclose(ref_cyl.base, cyl)

    cart = CYL(ref_cyl, CART)
    assert np.allclose(ref_cart.base, cart)


def test_keplerian_mean_circular(ref_kepl_m, ref_kepl_mc):

    kepl_mc = KEPL_M(ref_kepl_m, KEPL_MC)
    assert np.allclose(ref_kepl_mc.base, kepl_mc)

    kepl_m = KEPL_MC(ref_kepl_mc, KEPL_M)
    assert np.allclose(ref_kepl_m.base, kepl_m)
