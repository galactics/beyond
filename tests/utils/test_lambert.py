from pytest import mark

import numpy as np
# import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D

from beyond.dates import timedelta
from beyond.utils.lambert import lambert
from beyond.orbits import Ephem


@mark.parametrize("direction", ["prograde", "retrograde"])
def test_leo(iss_tle, direction):

    orbit = iss_tle.orbit().copy(form="keplerian_mean")
    target = orbit.copy()

    target.date = orbit.date + timedelta(minutes=45)

    # 600 km higher
    target[0] = orbit[0] + 600_000
    # On the other side of the orbit
    target[-1] = (orbit[-1] + np.pi) % (np.pi * 2)
    target[2] = orbit[2]

    # print(repr(orbit))
    # print(repr(target))

    orb1, orb2 = lambert(orbit, target, direction == "prograde")

    # Check the position has not changed
    assert all(orb1[:3] == orbit.copy(form="cartesian")[:3])
    assert all(orb2[:3] == target.copy(form="cartesian")[:3])

    # Check the velocity has changed
    assert np.linalg.norm(orb1[3:]) > np.linalg.norm(orbit.copy(form="cartesian")[3:])
    assert np.linalg.norm(orb2[3:]) < np.linalg.norm(target.copy(form="cartesian")[3:])

    # duration = timedelta(minutes=60)
    # orbit.propagator = "Kepler"
    # init_ephem = orbit.ephem(stop=duration, step=timedelta(seconds=30))

    # orb1.propagator = "Kepler"
    # transfert_ephem = orb1.ephem(start=orbit.date, stop=duration, step=timedelta(seconds=30))

    # target.propagator = "Kepler"
    # target_ephem = target.ephem(start=orbit.date, stop=duration, step=timedelta(seconds=30))

    # fig = plt.figure()
    # ax = plt.gca(projection='3d')
    # ax.view_init(elev=52, azim=140)

    # plt.plot(init_ephem[:, 0], init_ephem[:, 1], init_ephem[:, 2], label="original")
    # plt.plot(transfert_ephem[:, 0], transfert_ephem[:, 1], transfert_ephem[:, 2], label="transfert")
    # plt.plot(target_ephem[:, 0], target_ephem[:, 1], target_ephem[:, 2], label="target")

    # plt.legend()
    # plt.show()
