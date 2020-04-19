import numpy as np

from beyond.utils.constellation import WalkerStar, WalkerDelta


def test_walker_star():

    # Iridium constellation
    ws = WalkerStar(66, 6, 2)

    ref_raan = [
        0,
        np.pi / 6,
        np.pi * 2 / 6,
        3 * np.pi / 6,
        4 * np.pi / 6,
        5 * np.pi / 6,
    ]
    raan = list(ws.iter_raan())

    assert np.allclose(raan, ref_raan)

    ref = [
        [0, 0],
        [0, 2 * np.pi / 11],
        [0, 4 * np.pi / 11],
        [0, 6 * np.pi / 11],
        [0, 8 * np.pi / 11],
        [0, 10 * np.pi / 11],
        [0, 12 * np.pi / 11],
        [0, 14 * np.pi / 11],
        [0, 16 * np.pi / 11],
        [0, 18 * np.pi / 11],
        [0, 20 * np.pi / 11],
        [np.pi / 6, 4 * np.pi / 66],
        [np.pi / 6, 4 * np.pi / 66 + 2 * np.pi / 11],
        [np.pi / 6, 4 * np.pi / 66 + 4 * np.pi / 11],
        [np.pi / 6, 4 * np.pi / 66 + 6 * np.pi / 11],
        [np.pi / 6, 4 * np.pi / 66 + 8 * np.pi / 11],
        [np.pi / 6, 4 * np.pi / 66 + 10 * np.pi / 11],
        [np.pi / 6, 4 * np.pi / 66 + 12 * np.pi / 11],
        [np.pi / 6, 4 * np.pi / 66 + 14 * np.pi / 11],
        [np.pi / 6, 4 * np.pi / 66 + 16 * np.pi / 11],
        [np.pi / 6, 4 * np.pi / 66 + 18 * np.pi / 11],
        [np.pi / 6, 4 * np.pi / 66 + 20 * np.pi / 11],
        [np.pi * 2 / 6, 8 * np.pi / 66],
        [np.pi * 2 / 6, 8 * np.pi / 66 + 2 * np.pi / 11],
        [np.pi * 2 / 6, 8 * np.pi / 66 + 4 * np.pi / 11],
        [np.pi * 2 / 6, 8 * np.pi / 66 + 6 * np.pi / 11],
        [np.pi * 2 / 6, 8 * np.pi / 66 + 8 * np.pi / 11],
        [np.pi * 2 / 6, 8 * np.pi / 66 + 10 * np.pi / 11],
        [np.pi * 2 / 6, 8 * np.pi / 66 + 12 * np.pi / 11],
        [np.pi * 2 / 6, 8 * np.pi / 66 + 14 * np.pi / 11],
        [np.pi * 2 / 6, 8 * np.pi / 66 + 16 * np.pi / 11],
        [np.pi * 2 / 6, 8 * np.pi / 66 + 18 * np.pi / 11],
        [np.pi * 2 / 6, 8 * np.pi / 66 + 20 * np.pi / 11],
        [3 * np.pi / 6, 12 * np.pi / 66],
        [3 * np.pi / 6, 12 * np.pi / 66 + 2 * np.pi / 11],
        [3 * np.pi / 6, 12 * np.pi / 66 + 4 * np.pi / 11],
        [3 * np.pi / 6, 12 * np.pi / 66 + 6 * np.pi / 11],
        [3 * np.pi / 6, 12 * np.pi / 66 + 8 * np.pi / 11],
        [3 * np.pi / 6, 12 * np.pi / 66 + 10 * np.pi / 11],
        [3 * np.pi / 6, 12 * np.pi / 66 + 12 * np.pi / 11],
        [3 * np.pi / 6, 12 * np.pi / 66 + 14 * np.pi / 11],
        [3 * np.pi / 6, 12 * np.pi / 66 + 16 * np.pi / 11],
        [3 * np.pi / 6, 12 * np.pi / 66 + 18 * np.pi / 11],
        [3 * np.pi / 6, 12 * np.pi / 66 + 20 * np.pi / 11],
        [4 * np.pi / 6, 16 * np.pi / 66],
        [4 * np.pi / 6, 16 * np.pi / 66 + 2 * np.pi / 11],
        [4 * np.pi / 6, 16 * np.pi / 66 + 4 * np.pi / 11],
        [4 * np.pi / 6, 16 * np.pi / 66 + 6 * np.pi / 11],
        [4 * np.pi / 6, 16 * np.pi / 66 + 8 * np.pi / 11],
        [4 * np.pi / 6, 16 * np.pi / 66 + 10 * np.pi / 11],
        [4 * np.pi / 6, 16 * np.pi / 66 + 12 * np.pi / 11],
        [4 * np.pi / 6, 16 * np.pi / 66 + 14 * np.pi / 11],
        [4 * np.pi / 6, 16 * np.pi / 66 + 16 * np.pi / 11],
        [4 * np.pi / 6, 16 * np.pi / 66 + 18 * np.pi / 11],
        [4 * np.pi / 6, 16 * np.pi / 66 + 20 * np.pi / 11],
        [5 * np.pi / 6, 20 * np.pi / 66],
        [5 * np.pi / 6, 20 * np.pi / 66 + 2 * np.pi / 11],
        [5 * np.pi / 6, 20 * np.pi / 66 + 4 * np.pi / 11],
        [5 * np.pi / 6, 20 * np.pi / 66 + 6 * np.pi / 11],
        [5 * np.pi / 6, 20 * np.pi / 66 + 8 * np.pi / 11],
        [5 * np.pi / 6, 20 * np.pi / 66 + 10 * np.pi / 11],
        [5 * np.pi / 6, 20 * np.pi / 66 + 12 * np.pi / 11],
        [5 * np.pi / 6, 20 * np.pi / 66 + 14 * np.pi / 11],
        [5 * np.pi / 6, 20 * np.pi / 66 + 16 * np.pi / 11],
        [5 * np.pi / 6, 20 * np.pi / 66 + 18 * np.pi / 11],
        [5 * np.pi / 6, 20 * np.pi / 66 + 20 * np.pi / 11],
    ]

    fleet = list(ws.iter_fleet())

    # assert np.allclose(fleet[55], ref[55])
    assert np.allclose(fleet, ref)


def test_walker_delta():

    # Galileo constellation
    wd = WalkerDelta(24, 3, 1)
    ref_raan = [0, 2 * np.pi / 3, 4 * np.pi / 3]
    raan = list(wd.iter_raan())

    assert np.allclose(raan, ref_raan)

    ref = [
        [0, 0],
        [0, np.pi / 4],
        [0, np.pi / 2],
        [0, 3 * np.pi / 4],
        [0, np.pi],
        [0, 5 * np.pi / 4],
        [0, 3 * np.pi / 2],
        [0, 7 * np.pi / 4],
        [2 * np.pi / 3, np.pi / 12],
        [2 * np.pi / 3, np.pi / 12 + np.pi / 4],
        [2 * np.pi / 3, np.pi / 12 + np.pi / 2],
        [2 * np.pi / 3, np.pi / 12 + 3 * np.pi / 4],
        [2 * np.pi / 3, np.pi / 12 + np.pi],
        [2 * np.pi / 3, np.pi / 12 + 5 * np.pi / 4],
        [2 * np.pi / 3, np.pi / 12 + 3 * np.pi / 2],
        [2 * np.pi / 3, np.pi / 12 + 7 * np.pi / 4],
        [4 * np.pi / 3, np.pi / 6],
        [4 * np.pi / 3, np.pi / 6 + np.pi / 4],
        [4 * np.pi / 3, np.pi / 6 + np.pi / 2],
        [4 * np.pi / 3, np.pi / 6 + 3 * np.pi / 4],
        [4 * np.pi / 3, np.pi / 6 + np.pi],
        [4 * np.pi / 3, np.pi / 6 + 5 * np.pi / 4],
        [4 * np.pi / 3, np.pi / 6 + 3 * np.pi / 2],
        [4 * np.pi / 3, np.pi / 6 + 7 * np.pi / 4],
    ]

    fleet = list(wd.iter_fleet())

    # assert np.allclose(fleet[16], ref[16])
    assert np.allclose(fleet, ref)
