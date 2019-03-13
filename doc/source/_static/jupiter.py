"""Follow the informations provided in the `beyond.env.jpl` module about configuration
in order to supply the data needed.
"""

import numpy as np
import matplotlib.pyplot as plt

from beyond.dates import Date
from beyond.env.jpl import get_body
from beyond.frames import create_station
from beyond.config import config

# Load the ".bsp" file
config.update({
    "env": {
        "jpl": [
            "/path/to/jup310.bsp"
        ]
    }
})


date = Date.now()

# Definition of the location of observation
station = create_station('TLS', (43.428889, 1.497778, 178.0))

# Retrieve Jupiter and its moons state-vectors
jupiter = get_body('Jupiter', date)
io = get_body('Io', date)
europa = get_body('Europa', date)
ganymede = get_body('Ganymede', date)
callisto = get_body('Callisto', date)

# Convert them to the observer frame
jupiter.frame = station
io.frame = station
europa.frame = station
ganymede.frame = station
callisto.frame = station

# Change the orbit form in order to get azimuth and elevation
europa.form = 'spherical'
io.form = 'spherical'
ganymede.form = 'spherical'
callisto.form = 'spherical'
jupiter.form = 'spherical'

plt.figure()

# The size of the dots is not on scale
plt.plot([-np.degrees(io.theta)], [np.degrees(io.phi)], 'o', zorder=-io.r, label="Io")
plt.plot([-np.degrees(europa.theta)], [np.degrees(europa.phi)], 'o', zorder=-europa.r, label="Europa")
plt.plot([-np.degrees(ganymede.theta)], [np.degrees(ganymede.phi)], 'o', zorder=-ganymede.r, label="Ganymede")
plt.plot([-np.degrees(callisto.theta)], [np.degrees(callisto.phi)], 'o', zorder=-callisto.r, label="Callisto")
plt.plot([-np.degrees(jupiter.theta)], [np.degrees(jupiter.phi)], 'o', zorder=-jupiter.r, ms=12, label="Jupiter")

plt.suptitle("Jupiter as seen from Toulouse")
plt.title("{:%Y-%m-%d %H:%M:%S UTC}".format(date))
plt.legend()
plt.axis('equal')
plt.show()
