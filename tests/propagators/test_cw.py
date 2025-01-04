from pytest import fixture, mark, xfail

import numpy as np

from beyond.orbits import Orbit, Ephem
from beyond.dates import Date, timedelta
from beyond.propagators.rpo import ClohessyWiltshire
from beyond.orbits.man import ImpulsiveMan, ContinuousMan
from beyond.frames.frames import HillFrame


def plot_ephem(ephem):

    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    dates = list(ephem.dates)
    ax = plt.subplot(111)
    plt.plot(dates, ephem[:, 0], label=ephem[0].propagator.frame.orientation[0])
    plt.plot(dates, ephem[:, 1], label=ephem[0].propagator.frame.orientation[1])
    plt.plot(dates, ephem[:, 2], label=ephem[0].propagator.frame.orientation[2])

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.legend()
    plt.show()


@fixture(params=["QSW", "TNW"])
def propagator(request):
    hill = HillFrame(orientation=request.param)
    return ClohessyWiltshire(6800000.0, frame=hill)


@fixture
def lower_circular(propagator):
    """Define an orbit 600 m below the target, and 1500 behind
    """

    return Orbit(
        propagator._mat6 @ [-600, -1500, 0, 0, 1.5 * propagator.n * 600, 0],
        Date(2020, 5, 24),
        "cartesian",
        "Hill",
        propagator,
    )


@fixture
def tangential(propagator):
    return Orbit(
        propagator._mat6 @ [0, -100, 0, 0, 0, 0],
        Date(2020, 5, 24),
        "cartesian",
        "Hill",
        propagator,
    )


def test_circular_lower(lower_circular):
    """This test checks if the stability of a circular lower orbit
    """
    orb = lower_circular.propagate(timedelta(minutes=5))

    radial = 0 if lower_circular.propagator.frame.orientation == "QSW" else 1
    tan = 1 if lower_circular.propagator.frame.orientation == "QSW" else 0

    assert np.isclose(orb[radial], lower_circular[radial])
    assert orb[tan] > lower_circular[tan]
    assert orb[2] == lower_circular[2]


def test_stable_tangential(tangential):

    orb = tangential.propagate(timedelta(minutes=5))

    radial = 0 if tangential.propagator.frame.orientation == "QSW" else 1
    tan = 1 if tangential.propagator.frame.orientation == "QSW" else 0

    assert orb[radial] == tangential[radial]
    assert orb[tan] == tangential[tan]
    assert orb[2] == tangential[2]


@mark.parametrize("kind", ["impulive", "continuous"])
def test_man_hohmann(kind, lower_circular):
    """Check stability of a Hohmann transfer to nullified radial distance

    i.e. if the tangential distance does not evolve
    """

    orb = lower_circular

    man_start = orb.date + timedelta(seconds=60)
    if kind == "impulive":
        man_stop = man_start + timedelta(seconds=np.pi / orb.propagator.n)
    else:
        man_stop = timedelta(seconds=2 * np.pi / orb.propagator.n)

    delta_a = 600
    dv = 1.5 * orb.propagator.n * delta_a / 6

    if kind == "impulive":
        orb.maneuvers = [
            ImpulsiveMan(man_start, orb.propagator._mat3 @ [0, dv, 0]),
            ImpulsiveMan(man_stop, orb.propagator._mat3 @ [0, dv, 0]),
        ]
    else:
        orb.maneuvers = [
            ContinuousMan(man_start, man_stop, dv=2 * orb.propagator._mat3 @ [0, dv, 0]),
        ]

    # ephem = orb.ephem(stop=man_stop + timedelta(hours=1), step=timedelta(seconds=60))
    # plot_ephem(ephem)

    orb2 = orb.propagate(man_stop + timedelta(seconds=60))
    orb3 = orb.propagate(man_stop + timedelta(seconds=120))

    radial = 0 if orb.propagator.frame.orientation == "QSW" else 1
    tan = 1 if orb.propagator.frame.orientation == "QSW" else 0

    assert np.isclose(orb2[radial], orb3[radial])
    assert np.isclose(orb2[tan], orb3[tan])
    assert orb2[2] == orb3[2]

    # Propagate during the continuous maneuver
    if kind == "continuous":
        orb4 = orb.propagate(man_start + timedelta(minutes=25))
        assert orb.maneuvers[0].check(orb4.date)

        if orb.propagator.frame.orientation == "QSW":
            assert - delta_a < orb4[radial] < 0
        else:
            assert delta_a > orb4[radial] > 0


@mark.parametrize("kind", ["impulive", "continuous"])
def test_man_eccentric_boost(kind, tangential):

    orb = tangential

    man_start = orb.date + timedelta(seconds=60)
    if kind == "impulive":
        man_stop = man_start + timedelta(seconds=np.pi / orb.propagator.n)
    else:
        man_stop = timedelta(seconds=2 * np.pi / orb.propagator.n)

    forward = 70  # Advance 70 m closer to the target
    dv = forward * orb.propagator.n / 4

    if kind == "impulive":
        orb.maneuvers = [
            ImpulsiveMan(man_start, orb.propagator._mat3 @ [-dv, 0, 0]),
            ImpulsiveMan(man_stop, orb.propagator._mat3 @ [-dv, 0, 0]),
        ]
    else:
        orb.maneuvers = ContinuousMan(man_start, man_stop, dv=2*orb.propagator._mat3 @ [-dv, 0, 0])

    # ephem = orb.ephem(stop=man_stop + timedelta(hours=1), step=timedelta(seconds=60))
    # plot_ephem(ephem)

    orb2 = orb.propagate(man_stop + timedelta(seconds=120))

    radial = 0 if orb.propagator.frame.orientation == "QSW" else 1
    tan = 1 if orb.propagator.frame.orientation == "QSW" else 0

    assert np.isclose(orb[radial], orb2[radial])
    assert np.isclose(orb2[tan] - orb[tan], forward)
    assert np.isclose(orb2[tan], -30)
    assert orb[2] == orb2[2]


def test_man_tangential_boost(tangential):

    orb = tangential

    man_start = orb.date + timedelta(seconds=60)
    man_stop = man_start + timedelta(seconds=2 * np.pi / orb.propagator.n)

    forward = 70  # Advance 70 m closer to the target
    dv = forward * orb.propagator.n / (6 * np.pi)

    orb.maneuvers = [
        ImpulsiveMan(man_start, orb.propagator._mat3 @ [0, -dv, 0]),
        ImpulsiveMan(man_stop, orb.propagator._mat3 @ [0, dv, 0]),
    ]

    # ephem = orb.ephem(stop=man_stop + timedelta(hours=1), step=timedelta(seconds=60))
    # plot_ephem(ephem)

    orb2 = orb.propagate(man_stop + timedelta(seconds=120))

    radial = 0 if orb.propagator.frame.orientation == "QSW" else 1
    tan = 1 if orb.propagator.frame.orientation == "QSW" else 0

    assert np.isclose(orb[radial], orb2[radial])
    assert np.isclose(orb2[tan] - orb[tan], forward)
    assert np.isclose(orb2[tan], -30)
    assert orb[2] == orb2[2]


def test_man_tangetial_linear(tangential):

    orb = tangential

    forward = 60

    dv = 0.1
    duration = timedelta(seconds=abs(forward / dv))
    dv1 = orb.propagator._mat3 @ [0, dv, 0]
    accel = (orb.propagator._mat3 @ [-1, 0, 0]) * 2 * orb.propagator.n * dv

    man_start = orb.date + timedelta(seconds=10)
    duration = timedelta(seconds=forward / dv)
    man_stop = man_start + duration

    orb.maneuvers = [
        ImpulsiveMan(man_start, dv1),
        ContinuousMan(man_start, duration, accel=accel),
        ImpulsiveMan(man_stop, -dv1),
    ]

    # ephem = orb.ephem(stop=man_stop + timedelta(hours=1), step=timedelta(seconds=60))
    # plot_ephem(ephem)

    orb2 = orb.propagate(man_stop + timedelta(seconds=120))

    radial = 0 if orb.propagator.frame.orientation == "QSW" else 1
    tan = 1 if orb.propagator.frame.orientation == "QSW" else 0

    assert duration.total_seconds() == 600
    assert np.isclose(orb2[radial], 0)
    assert np.isclose(orb2[tan] - orb[tan], forward)
    assert orb2[2] == orb[2]


def test_from_orbit(lower_circular, orbit):

    if isinstance(orbit, Ephem):
        xfail("Ephem are not handled by ClohessyWiltshire propagator")

    propagator = ClohessyWiltshire.from_orbit(orbit, lower_circular.propagator.frame.orientation)
    
    lower_circular.propagator = propagator

