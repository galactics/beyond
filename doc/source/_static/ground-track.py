#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt

from beyond.config import config
from beyond.orbits import Tle
from beyond.dates import Date, timedelta

# Bypass the need of Earth Orientation Parameters data
config.update({"eop": {"missing_policy": "pass"}})

# Parsing of TLE
tle = Tle("""ISS (ZARYA)
1 25544U 98067A   16086.49419020  .00003976  00000-0  66962-4 0  9998
2 25544  51.6423 110.4590 0001967   0.7896 153.8407 15.54256299992114""")

# Conversion into `Orbit` object
orb = tle.orbit()

# Tables containing the positions of the ground track
latitudes, longitudes = [], []
for point in orb.ephemeris(Date.now(), timedelta(minutes=120), timedelta(minutes=1)):

    # Conversion to earth rotating frame
    point.frame = 'ITRF'

    # Conversion from cartesian to spherical coordinates (range, latitude, longitude)
    point.form = 'spherical'

    # Conversion from radians to degrees
    lon, lat = np.degrees(point[1:3])

    latitudes.append(lat)
    longitudes.append(lon)

im = plt.imread("earth.png")
plt.figure(figsize=(15.2, 8.2))
plt.imshow(im, extent=[-180, 180, -90, 90])
plt.plot(longitudes, latitudes, 'r.')

plt.xlim([-180, 180])
plt.ylim([-90, 90])
plt.grid(True, color='w', linestyle=":", alpha=0.4)
plt.xticks(range(-180, 181, 30))
plt.yticks(range(-90, 91, 30))
plt.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
plt.show()
