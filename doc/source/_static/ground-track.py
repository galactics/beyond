#!/usr/bin/env python

"""Script showing the position of the ISS at the time of the TLE
and the ground track for the previous and the next orbit
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from beyond.io.tle import Tle
from beyond.dates import Date, timedelta


# Parsing of TLE
tle = Tle("""ISS (ZARYA)
1 25544U 98067A   19004.59354167  .00000715  00000-0  18267-4 0  9995
2 25544  51.6416  95.0104 0002419 236.2184 323.8248 15.53730729149833""")

# Conversion into `Orbit` object
orb = tle.orbit()

# Tables containing the positions of the ground track
latitudes, longitudes = [], []
prev_lon, prev_lat = None, None

period = orb.infos.period
start = orb.date - period
stop = 2 * period
step = period / 100

for point in orb.ephemeris(start=start, stop=stop, step=step):

    # Conversion to earth rotating frame
    point.frame = 'ITRF'

    # Conversion from cartesian to spherical coordinates (range, latitude, longitude)
    point.form = 'spherical'

    # Conversion from radians to degrees
    lon, lat = np.degrees(point[1:3])

    # Creation of multiple segments in order to not have a ground track
    # doing impossible paths
    if prev_lon is None:
        lons = []
        lats = []
        longitudes.append(lons)
        latitudes.append(lats)
    elif orb.i < np.pi /2 and (np.sign(prev_lon) == 1 and np.sign(lon) == -1):
        lons.append(lon + 360)
        lats.append(lat)
        lons = [prev_lon - 360]
        lats = [prev_lat]
        longitudes.append(lons)
        latitudes.append(lats)
    elif orb.i > np.pi/2 and (np.sign(prev_lon) == -1 and np.sign(lon) == 1):
        lons.append(lon - 360)
        lats.append(lat)
        lons = [prev_lon + 360]
        lats = [prev_lat]
        longitudes.append(lons)
        latitudes.append(lats)

    lons.append(lon)
    lats.append(lat)
    prev_lon = lon
    prev_lat = lat

img = Path(__file__).parent / "earth.png"

im = plt.imread(str(img))
plt.figure(figsize=(15.2, 8.2))
plt.imshow(im, extent=[-180, 180, -90, 90])

for lons, lats in zip(longitudes, latitudes):
    plt.plot(lons, lats, 'r')

lon, lat = np.degrees(orb.copy(frame='ITRF', form='spherical')[1:3])
plt.plot([lon], [lat], 'ro')

plt.xlim([-180, 180])
plt.ylim([-90, 90])
plt.grid(True, color='w', linestyle=":", alpha=0.4)
plt.xticks(range(-180, 181, 30))
plt.yticks(range(-90, 91, 30))
plt.tight_layout()

if "no-display" not in sys.argv:
    plt.show()
