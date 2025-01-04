"""Reproducing the figures on the original Yamanaka-Ankersen paper

New State Transition Matrix for Relative Motion on an Arbitrary Elliptical Orbit
Koji Yamanaka and Finn Ankersen.
Journal of Guidance, Control, and Dynamics 25, no. 1 (January 2002): 60–66.
https://doi.org/10.2514/2.4875.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt

from beyond.propagators.rpo import YamanakaAnkersen, ClohessyWiltshire
from beyond.frames.frames import HillFrame
from beyond.orbits import Orbit
from beyond.dates import Date, timedelta
from beyond.constants import Earth

date = Date(2023, 11, 26)

alt = 500_000
rp = alt + Earth.r
i = np.radians(30)
nu = np.radians(45)

for i, e in enumerate([0.1, 0.7]):
    a = rp / (1 - e)

    target = Orbit([a, e, i, 0, 0, nu], date, "keplerian", "EME2000", "Kepler")

    stop = 2 * target.infos.period
    step = timedelta(seconds=60)

    ephem_target = target.ephem(stop=stop, step=step).copy(form="keplerian")

    prop_ya = YamanakaAnkersen(target)
    prop_cw = ClohessyWiltshire.from_orbit(target, orientation="LVLH")
    orb_cw = Orbit(
        [100, 10, 10, 0.1, 0.1, 0.1],
        target.date,
        form="cartesian",
        frame=HillFrame("LVLH"),
        propagator=prop_cw,
    )

    orb_ya = orb_cw.as_orbit(prop_ya)

    ephem_cw = orb_cw.ephem(stop=stop, step=step)
    ephem_ya = orb_ya.ephem(stop=stop, step=step)

    print(repr(ephem_ya[-1]))

    plt.figure(figsize=(10, 6))

    plt.subplot(121)

    plt.plot(ephem_cw[:, 0], ephem_cw[:, 2], label="CW")
    plt.plot(ephem_ya[:, 0], ephem_ya[:, 2], label="YA")
    plt.plot(0, 0, "r+", label="target")
    plt.grid(ls=":")
    plt.gca().invert_xaxis()
    plt.gca().invert_yaxis()
    plt.legend()
    plt.xlabel("X (m)")
    plt.ylabel("Z (m)")

    plt.subplot(122)

    plt.plot(ephem_cw[:, 0], ephem_cw[:, 1], label="CW")
    plt.plot(ephem_ya[:, 0], ephem_ya[:, 1], label="YA")
    plt.plot(0, 0, "r+", label="target")
    plt.grid(ls=":")
    plt.gca().invert_xaxis()
    # plt.gca().invert_yaxis()
    plt.legend()
    plt.xlabel("X (m)")
    plt.ylabel("Y (m)")

    plt.suptitle(f"perigee = {alt / 1000:0.1f} km / e = {e:0.1f}")

    plt.tight_layout()

if "no-display" not in sys.argv:
    plt.show()
