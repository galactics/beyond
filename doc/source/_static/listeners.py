#!/usr/bin/env python

from datetime import timedelta

from beyond.utils import Date
from beyond.orbits import Tle
from beyond.frames import create_station
from beyond.orbits.listeners import stations_listeners, NodeListener, ApsideListener

tle = Tle("""ISS (ZARYA)
1 25544U 98067A   16086.49419020  .00003976  00000-0  66962-4 0  9998
2 25544  51.6423 110.4590 0001967   0.7896 153.8407 15.54256299992114""").orbit()

# Station definition
station = create_station('TLS', (43.428889, 1.497778, 178.0))
listeners = stations_listeners(station)
listeners.append(NodeListener())
listeners.append(ApsideListener())

for orb in tle.iter(Date.now(), timedelta(minutes=100), timedelta(seconds=180), listeners=listeners):
    print("{orb.info:8} {orb.date:%Y-%m-%d %H:%M:%S}".format(orb=orb))
