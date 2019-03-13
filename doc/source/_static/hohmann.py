
"""Example of Hohmann transfer

The orbit we are starting with is a Tle of the ISS. The amplitude of the maneuver is greatly
exagerated regarding the ISS's capability, but has the convenience to be particularly visual.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from beyond.orbits import Tle
from beyond.dates import timedelta
from beyond.propagators.kepler import Kepler
from beyond.env.solarsystem import get_body
from beyond.orbits.man import Maneuver
from beyond.orbits.listeners import ApsideListener


orb = Tle("""ISS (ZARYA)
1 25544U 98067A   18124.55610684  .00001524  00000-0  30197-4 0  9997
2 25544  51.6421 236.2139 0003381  47.8509  47.6767 15.54198229111731""").orbit()

start = orb.date
stop = timedelta(minutes=300)
step = timedelta(seconds=60)

# Changing the propagator to Keplerian, as SGP4 is not able to perform maneuvers
orb.propagator = Kepler(step, bodies=get_body("Earth"))

# Research for the next perigee
for p in orb.iter(start=start, stop=stop, step=step, listeners=ApsideListener()):
    if p.event and p.event.info == "Periapsis":
        perigee = p
        break

man1 = Maneuver(perigee.date, (280, 0, 0), frame="TNW")
orb.maneuvers = [man1]

dates1, alt1 = [], []
# Research for the next apogee after the first maneuver
for p in orb.iter(start=perigee.date, stop=stop, step=step, listeners=ApsideListener()):
    if p.event and p.event.info == "Apoapsis":
        apogee = p
        break

man2 = Maneuver(apogee.date, (270, 0, 0), frame="TNW")

print(man1.date)
print(man2.date)

# Adding both maneuvers to the orbit
orb.maneuvers = [man1, man2]

# Propagation throught the two maneuvers
ephem = orb.ephem(start=start, stop=stop, step=step)

# graphs
plt.figure()

data = np.array(ephem)
dates = [x.date for x in ephem]
# Altitude in km
alt = (np.linalg.norm(data[:, :3], axis=1) - orb.frame.center.r) / 1000
events_dates = [perigee.date, apogee.date]
events_alt = (np.linalg.norm([perigee[:3], apogee[:3]], axis=1) - orb.frame.center.r) / 1000

plt.plot(dates, alt)
plt.plot(events_dates, events_alt, 'ro')

plt.ylabel("altitude (km)")

fig = plt.figure()
ax = plt.gca(projection='3d')
ax.view_init(elev=52, azim=140)

x, y, z = zip(perigee[:3], apogee[:3])

plt.plot(data[:, 0], data[:, 1], data[:, 2])
plt.plot(x, y, z, 'ro')


plt.show()
