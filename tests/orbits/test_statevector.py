from pytest import fixture, raises
import numpy as np

from beyond.io.tle import Tle
from beyond.orbits import StateVector


cases = {
    "tle": dict(
        i=0.9013246776441637,
        Ω=4.122710293976634,
        Omega=4.122710293976634,
        raan=4.122710293976634,
        e=0.0003381,
        ω=0.8351557550425547,
        omega=0.8351557550425547,
        M=0.8321153914855804,
        n=0.0011302448468631173,
    ),
    "cartesian": dict(
        x=+3846151.811598413,
        y=-1783447.050631176,
        z=5292398.809619665,
        vx=3862.139125251566,
        x_dot=3862.139125251566,
        vy=6598.5917772289085,
        y_dot=6598.5917772289085,
        vz=-580.669327598516,
        z_dot=-580.669327598516,
    ),
    "spherical": dict(
        r=6781080.467029605,
        θ=-0.43418536221185006,
        theta=-0.43418536221185006,
        φ=0.8954099055365006,
        phi=0.8954099055365006,
        r_dot=1.9172006159737782,
        θ_dot=0.0017952533349796453,
        theta_dot=0.0017952533349796453,
        φ_dot=-0.00013731861912328838,
        phi_dot=-0.00013731861912328838,
    ),
}


@fixture(params=cases.keys())
def sv(request):
    tle = Tle(
        """ISS (ZARYA)
1 25544U 98067A   18124.55610684  .00001524  00000-0  30197-4 0  9997
2 25544  51.6421 236.2139 0003381  47.8509  47.6767 15.54198229111731"""
    )
    morb = tle.orbit().copy(form=request.param)
    # Quick and dirty transformation of the MeanOrbit into a StateVector, without
    # any propagation. This is done for simplicity, as the resulting StateVector
    # will be used for nothing but checks for setters and getters.

    new_dict = morb._data.copy()
    new_dict.pop("propagator")
    return StateVector(morb.base, **new_dict)


def test_getter(sv):

    for n, v in cases[sv.form.name].items():
        np.testing.assert_almost_equal(getattr(sv, n), v)
        np.testing.assert_almost_equal(sv[n], v)

    assert sv.ndot == 3.048e-05
    assert sv.ndotdot == 0.0
    assert sv.bstar == 3.0197e-05

    assert sv.name == "ISS (ZARYA)"
    assert sv.cospar_id == "1998-067A"

    name = "x" if sv.form.name != "cartesian" else "theta"

    with raises(AttributeError):
        getattr(sv, name)

    with raises(KeyError):
        sv[name]

    with raises(AttributeError):
        getattr(sv, "dummy")

    with raises(KeyError):
        sv["dummy"]


def test_setter(sv):

    for n in cases[sv.form.name].keys():
        setattr(sv, n, 0)
        assert getattr(sv, n) == 0
        sv[n] = 1
        assert sv[n] == 1

    sv.ndot = 10
    sv.ndotdot = 9
    sv.bstar = 8

    sv.name = "test"
    sv.cospar_id = "9999-999A"

    assert sv.ndot == 10
    assert sv.ndotdot == 9
    assert sv.bstar == 8

    assert sv.name == "test"
    assert sv.cospar_id == "9999-999A"

    assert sv["ndot"] == 10
    assert sv["ndotdot"] == 9
    assert sv["bstar"] == 8

    assert sv["name"] == "test"
    assert sv["cospar_id"] == "9999-999A"

    # This test is here to challenge the strange behaviour encountered
    # when one create an attribute, that is later superseded by the
    # variable name of the specific form.

    form = sv.form

    name = "x" if form.name == "spherical" else "theta"

    with raises(AttributeError):
        setattr(sv, name, 5)

    with raises(KeyError):
        sv[name] = 4
