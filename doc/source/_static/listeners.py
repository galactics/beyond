#!/usr/bin/env python

from beyond.dates import Date, timedelta
from beyond.io.tle import Tle
from beyond.frames import create_station
from beyond.propagators.listeners import stations_listeners, NodeListener, ApsideListener, LightListener


tle = Tle("""ISS (ZARYA)
1 25544U 98067A   17153.89608442  .00001425  00000-0  28940-4 0  9997
2 25544  51.6419 109.5559 0004850 223.1783 180.8272 15.53969766 59532""").orbit()

# Station definition
station = create_station('TLS', (43.428889, 1.497778, 178.0))

# Listeners declaration
listeners = stations_listeners(station)  # AOS, LOS and MAX elevation
listeners.append(NodeListener())         # Ascending and Descending Node
listeners.append(ApsideListener())       # Apogee and Perigee
listeners.append(LightListener())        # Illumination events

start = Date.now()
stop = timedelta(minutes=100)
step = timedelta(seconds=180)

for orb in tle.iter(start=start, stop=stop, step=step, listeners=listeners):
    event = orb.event if orb.event is not None else ""
    print(f"{orb.date:%Y-%m-%d %H:%M:%S} {event}")
