from pytest import fixture

import numpy as np

from beyond.dates import Date, timedelta
from beyond.orbits import Orbit
from beyond.constants import Earth
from beyond.propagators.rpo import YamanakaAnkersen
from beyond.frames.frames import HillFrame
from beyond.frames.local import QSW2LVLH
from beyond.utils.matrix import expand


@fixture(params=[0.1, 0.7], ids=["ecc=0.1", "ecc=0.7"])
def target(request):
    date = Date(2023, 11, 26)

    rp = 500_000 + Earth.r
    e = request.param
    a = rp / (1 - e)
    i = np.radians(30)
    nu = np.radians(45)

    return Orbit([a, e, i, 0, 0, nu], date, "keplerian", "EME2000", "Kepler")


@fixture
def ref_lvlh(target):
    """Refererence in LVLH"""

    if target.e == 0.1:
        date = Date(2023, 11, 26, 3, 41, 0)
        xref, yref, zref = -2908.182250516494, 6.202752618784139, 195.5364351224569
    elif target.e == 0.7:
        date = Date(2023, 11, 26, 19, 11, 0)
        xref, yref, zref = -10326.759184987815, 6.20243448860358, 3260.6919703051335
    else:
        raise ValueError(f"Unknown frame {frame}")

    return date, np.array([xref, yref, zref])


@fixture
def ref(ref_lvlh, orientation):
    date, pos = ref_lvlh

    if orientation == "LVLH":
        ref = pos
    elif orientation == "QSW":
        ref = QSW2LVLH.T @ pos

    return date, ref


@fixture(params=["LVLH", "QSW"])
def orientation(request):
    return request.param


@fixture
def propagator(target, orientation):
    return YamanakaAnkersen(target, orientation)


@fixture
def orb(orientation, target, propagator):
    # cartesian coordinates in LVLH
    pv = [100, 10, 10, 0.1, 0.1, 0.1]

    if orientation == "QSW":
        pv = expand(QSW2LVLH.T) @ pv

    return Orbit(
        pv,
        target.date,
        form="cartesian",
        frame=HillFrame(orientation),
        propagator=propagator,
    )


def test_propagation(orb, ref):
    stop = 2 * orb.propagator.target.infos.period
    ephem = orb.ephem(stop=stop, step=timedelta(seconds=60))

    res = ephem[-1]

    ref_date, ref_pv = ref

    assert np.allclose(res.base[:3], ref_pv)
    assert res.date == ref_date


def test_ephem_as_target(target, ref_lvlh):
    stop = 3 * target.infos.period
    step = timedelta(seconds=60)
    target_ephem = target.ephem(stop=stop, step=step)

    propagator = YamanakaAnkersen(target_ephem)
    orb = Orbit(
        [100, 10, 10, 0.1, 0.1, 0.1],
        target.date,
        form="cartesian",
        frame=HillFrame("LVLH"),
        propagator=propagator,
    )

    ref_date, ref_pv = ref_lvlh

    chaser_ephem = orb.ephem(stop=2 * target.infos.period, step=step)
    res = chaser_ephem[-1]

    assert np.allclose(res.base[:3], ref_pv)
    assert res.date == ref_date
