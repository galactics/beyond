
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
from beyond.orbits.man import DeltaCombined
from beyond.orbits.listeners import ApsideListener
from beyond.config import config

config.update({"eop": {"missing_policy": "pass"}})

orb = Tle("""ISS (ZARYA)
1 25544U 98067A   18124.55610684  .00001524  00000-0  30197-4 0  9997
2 25544  51.6421 236.2139 0003381  47.8509  47.6767 15.54198229111731""").orbit()

start = orb.date
stop = timedelta(minutes=9000)
step = timedelta(seconds=60)

# Changing the propagator to Keplerian, as SGP4 is not able to perform maneuvers
orb.propagator = Kepler(step, bodies=get_body("Earth"))

dates = []
for p in orb.iter(start, stop, step, listeners=ApsideListener()):
    if p.event and p.event.info == "Apoapsis":
        dates.append(p.date)

for d in dates:
    orb.maneuvers.append(DeltaCombined(d, delta_angle=np.radians(20)))

# Propagation throught the maneuver
ephem = orb.ephem(start=start, stop=stop, step=step)

# graphs
plt.figure()

data = np.array(ephem)
dates = [x.date.datetime for x in ephem]
# Altitude in km
alt = (np.linalg.norm(data[:, :3], axis=1) - orb.frame.center.r) / 1000
# events_dates = [perigee.date.datetime, apogee.date.datetime]
# events_alt = (np.linalg.norm([perigee[:3], apogee[:3]], axis=1) - orb.frame.center.r) / 1000

plt.plot(dates, alt)
# plt.plot(events_dates, events_alt, 'ro')

plt.ylabel("altitude (km)")

fig = plt.figure()
ax = plt.gca(projection='3d')
ax.view_init(elev=52, azim=140)

# x, y, z = zip(perigee[:3], apogee[:3])

plt.plot(data[:, 0], data[:, 1], data[:, 2])
# plt.plot(x, y, z, 'ro')
scaling = np.array([getattr(ax, 'get_{}lim'.format(dim))() for dim in 'xyz'])
ax.auto_scale_xyz(*[[np.min(scaling), np.max(scaling)]] * 3)

plt.show()
