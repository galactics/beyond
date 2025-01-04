import numpy as np
from pytest import fixture

from beyond.io.tle import Tle
from beyond.dates import Date, timedelta
from beyond.propagators.analytical import EcksteinHechler
from beyond.orbits import MeanOrbit, StateVector

ref = {
    "mean": MeanOrbit(
        [
            6793168.043926995,
            6.975603931616129e-05,
            0.0004794571601579559,
            0.9013194416564078,
            4.257455408161921,
            5.312329330875215,
        ],
        Date(2023, 7, 4, 4, 32, 4, 686432),
        "mean_circular",
        "CIRF",
        EcksteinHechler(False),
    ),
    "osculating": StateVector(
        [
            6790998.220794241,
            -0.0002432281259211617,
            0.0004536564274542095,
            0.9011933767382031,
            4.257042666714024,
            5.311971200949481,
        ],
        Date(2023, 7, 4, 4, 32, 4, 686432),
        "mean_circular",
        "CIRF",
    ),
}

ref_date = {
    "mean": MeanOrbit(
        [
            6793168.043926995,
            0.00037500378819392837,
            0.0006420732175721347,
            0.9013194416564078,
            3.3215501429116445,
            3.827956538505063,
        ],
        Date(2023, 7, 15),
        "mean_circular",
        "CIRF",
        EcksteinHechler(False),
    ),
    "osculating": StateVector(
        [
            6794341.493224958,
            0.00036043866470490866,
            0.0002587774167155157,
            0.9013878315499614,
            3.321982600081687,
            3.8283388388815403,
        ],
        Date(2023, 7, 15),
        "mean_circular",
        "CIRF",
    ),
}


ref_fit = MeanOrbit(
    [
        6793683.868413672,
        -2.8436091859129177e-05,
        0.0013390737494340633,
        0.9013200488995392,
        4.517164069454659,
        1.8353248756800076,
    ],
    Date(2023, 7, 1, 4, 32, 4, 686432),
    "mean_circular",
    "CIRF",
    EcksteinHechler(),
)


@fixture(params=ref.keys())
def propag_type(request):
    return request.param


@fixture
def tle():
    tle = """ISS (ZARYA)
1 25544U 98067A   23182.18894313  .00014575  00000+0  25754-3 0  9990
2 25544  51.6418 259.1154 0004762  93.3659  11.7905 15.50581131403963"""

    return Tle(tle).orbit()


@fixture
def orb(tle, propag_type):
    orb = tle.copy(form="mean_circular")
    orb.propagator = EcksteinHechler(osculating=propag_type == "osculating")

    return orb


def test_propagation(helper, orb, propag_type):
    # Propagation via a Date object
    propagated = orb.propagate(ref_date[propag_type].date)
    helper.assert_orbit(ref_date[propag_type], propagated, form="mean_circular")

    # Propagation via a timedelta object
    propagated = orb.propagate(timedelta(3))
    helper.assert_orbit(ref[propag_type], propagated, form="mean_circular")

    # Propagation as an ephemeris
    ephem = orb.ephem(
        start=Date(orb.date.d),
        stop=ref_date[propag_type].date,
        step=timedelta(minutes=3),
    )
    helper.assert_orbit(ref_date[propag_type], ephem[-1])

    ephem = orb.ephem(stop=timedelta(3), step=timedelta(minutes=3))
    helper.assert_orbit(ref[propag_type], ephem[-1])


def test_fit(helper, tle):
    sv = tle.propagate(tle.date)
    # The ref_fit mean orbit does not have these attribute set
    del sv._data["name"]
    del sv._data["cospar_id"]

    mean_orbit = EcksteinHechler.fit_statevector(sv)
    helper.assert_orbit(ref_fit, mean_orbit, form="mean_circular")
