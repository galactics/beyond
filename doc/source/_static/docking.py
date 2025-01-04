"""Example script for docking to the ISS, starting from an orbit 3000 m below

This script uses the V-bar approach strategy, with an approach ellipse at 2000
meters and a keep-out sphere at 200 meters.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches

from beyond.dates import Date, timedelta
from beyond.orbits import Orbit
from beyond.propagators.rpo import ClohessyWiltshire
from beyond.utils.rpohelper import RpoHelper
from beyond.propagators.listeners import Listener, Event, find_event
from beyond.orbits.man import ImpulsiveMan, ContinuousMan


class TangentialDistanceListener(Listener):
    """This listener is useful to detect the exact time at which to
    start the Hohmann transfer in order to place the chaser spacecraft
    at the first hold point
    """

    def __init__(self, delta, orientation="QSW"):
        self.delta = delta
        self.orientation = orientation

    def info(self, orb):
        return Event(self, "go")

    def __call__(self, orb):
        idx = 1 if self.orientation == "QSW" else 0
        return orb[idx] - self.delta


propagator = ClohessyWiltshire(6378000 + 410000)
helper = RpoHelper(propagator)

radial = -3000  # radial distance at the beginning of the simulation
date = Date(Date.now().d)
step = timedelta(seconds=10)
hold_points = [
    -2500,  # First hold point well outside the approach ellipse
    -200,  # Second hold point just outside the keep-out sphere
    -10,  # Last hold point close to the docking port for the last checks
]
hold = timedelta(minutes=10)  # hold duration
linear_dv = 0.5  # Proximity linear velocity
final_dv = 0.1  # Final linear velocity for docking
duration = helper.period * 3

# Tangential distance necessary for a Hohmann transfer
tangential = helper.hohmann_distance(radial)

# Initial orbit
orb = helper.coelliptic(date, radial, tangential * 1.5)

# Search for the point of desired maneuver in order to arrive at the
# first hold point
ephem = orb.ephem(
    step=step,
    stop=helper.period * 2,
    listeners=TangentialDistanceListener(
        tangential + hold_points[0], helper.frame.orientation
    ),
)
start_man = find_event(ephem, "go")

# Creation of the two impulsive maneuvers that place the spacecraft at the
# first hold point (at 2500 m)
orb.maneuvers.extend(helper.hohmann(-radial, start_man.date))

# Eccentric boost in order to go to the next hold point (at 200 m)
orb.maneuvers.extend(
    helper.eccentric_boost(
        hold_points[1] - hold_points[0], orb.maneuvers[-1].date + hold
    )
)

# Linear maneuver at 0.5 m/s to reach the next hold point (at 10 m)
orb.maneuvers.extend(
    helper.vbar_linear(
        hold_points[2] - hold_points[1], orb.maneuvers[-1].date + hold, linear_dv
    )
)

# Final maneuver at 0.1 m/s to reach the docking port
orb.maneuvers.extend(
    helper.vbar_linear(-hold_points[2], orb.maneuvers[-1].date + hold, final_dv)
)

chaser_ephem = orb.ephem(step=step, stop=duration)
dates = list(chaser_ephem.dates)
result = np.asarray(chaser_ephem)

# Display the trajectory
print("Final position")
print(f"Q = {chaser_ephem[-1, 0]: 7.3f}")
print(f"S = {chaser_ephem[-1, 1]: 7.3f}")
print(f"W = {chaser_ephem[-1, 2]: 7.3f}")

man_dates = [man.date for man in orb.maneuvers if isinstance(man, ImpulsiveMan)]
cont_man = [man for man in orb.maneuvers if isinstance(man, ContinuousMan)]
mans = np.array([chaser_ephem.propagate(d) for d in man_dates])

plt.figure(figsize=(12.8, 4.8))
ax = plt.subplot(111)

# Approach sphere (2 km)
circle = mpatches.Ellipse((0, 0), 4000, 2000, ec="none", fc="#aaaaaa60")
ax.add_patch(circle)

# Keep out sphere (200 m) with corridors
w1 = mpatches.Wedge((0, 0), 200, theta1=-170, theta2=-100, ec="none", fc="#aaaaaa")
w2 = mpatches.Wedge((0, 0), 200, theta1=-80, theta2=-10, ec="none", fc="#aaaaaa")
w3 = mpatches.Wedge((0, 0), 200, theta1=10, theta2=170, ec="none", fc="#aaaaaa")
ax.add_patch(w1)
ax.add_patch(w2)
ax.add_patch(w3)

plt.text(0, -750, "Approach ellipse", ha="center")
plt.text(0, 200, "Keep-out sphere", ha="center")

plt.plot(chaser_ephem[:, 1], chaser_ephem[:, 0])
if len(mans):
    plt.plot(mans[:, 1], mans[:, 0], "o")

for man in cont_man:
    subeph = chaser_ephem.ephem(start=man.start, stop=man.stop, step=step)
    plt.plot(subeph[:, 1], subeph[:, 0], "r")

plt.xlabel("S (m)")
plt.ylabel("Q (m)")
ax.set_aspect("equal")
plt.grid(ls=":")
plt.xlim(-11000, 1000)
plt.ylim(-3200, 500)
plt.tight_layout()

if "no-display" not in sys.argv:
    plt.show()
