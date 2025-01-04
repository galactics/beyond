
"""Example of Hohmann transfer

The orbit we are starting with is a Tle of the ISS. The amplitude of the maneuver is greatly
exagerated regarding the ISS's capability, but has the convenience to be particularly visual.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from beyond.io.tle import Tle
from beyond.dates import timedelta
from beyond.propagators.numerical import KeplerNum
from beyond.env.solarsystem import get_body
from beyond.orbits.man import ImpulsiveMan
from beyond.propagators.listeners import ApsideListener, find_event


orb = Tle("""ISS (ZARYA)
1 25544U 98067A   18124.55610684  .00001524  00000-0  30197-4 0  9997
2 25544  51.6421 236.2139 0003381  47.8509  47.6767 15.54198229111731""").orbit()

start = orb.date
stop = timedelta(minutes=300)
step = timedelta(seconds=60)

# Changing the propagator to Keplerian, as SGP4 is not able to perform maneuvers
orb.propagator = KeplerNum(step, bodies=get_body("Earth"))

# Research for the next perigee
perigee = find_event(orb.iter(stop=stop, listeners=ApsideListener()), 'Periapsis')

man1 = ImpulsiveMan(perigee.date, (280, 0, 0), frame="TNW")
orb.maneuvers = [man1]

dates1, alt1 = [], []

# Research for the next apogee after the first maneuver
apogee = find_event(orb.iter(start=perigee.date - step * 10, stop=stop, listeners=ApsideListener()), 'Apoapsis')
# apogee = find_event(orb.iter(stop=stop, listeners=ApsideListener()), 'Apoapsis', offset=1)

# Adding the second maneuver to the orbit
man2 = ImpulsiveMan(apogee.date, (270, 0, 0), frame="TNW")
orb.maneuvers.append(man2)

print(man1.date)
print(man2.date)

# Propagation throught the two maneuvers
ephem = orb.ephem(start=start, stop=stop, step=step)

# graphs
plt.figure()

data = np.array(ephem)
dates = [x.date for x in ephem]
# Altitude in km
alt = (np.linalg.norm(data[:, :3], axis=1) - orb.frame.center.body.r) / 1000
events_dates = [perigee.date, apogee.date]
events_alt = (np.linalg.norm([perigee[:3], apogee[:3]], axis=1) - orb.frame.center.body.r) / 1000

plt.plot(dates, alt)
plt.plot([events_dates[0]], [events_alt[0]], 'ro', label="perigee")
plt.plot([events_dates[1]], [events_alt[1]], 'ko', label="apogee")

plt.ylabel("altitude (km)")
plt.legend()
plt.grid(linestyle=':', alpha=0.4)
plt.tight_layout()

fig = plt.figure()
ax = plt.subplot(projection='3d')
ax.view_init(elev=52, azim=140)

x, y, z = zip(perigee[:3], apogee[:3])

plt.plot(data[:, 0], data[:, 1], data[:, 2])
plt.plot([perigee[0]], [perigee[1]], [perigee[2]], 'ro')
plt.plot([apogee[0]], [apogee[1]], [apogee[2]], 'ko')

if "no-display" not in sys.argv:
    plt.show()
