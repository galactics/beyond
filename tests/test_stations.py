

import numpy as np
from numpy.testing import assert_almost_equal

from pytest import fixture

from beyond.dates import Date, timedelta
from beyond.orbits import Orbit
from beyond.orbits.tle import Tle
from beyond.orbits.listeners import SignalEvent, MaxEvent, MaskEvent


def assert_vector(ref, pv, precision=(4, 6)):

    if isinstance(ref, Orbit):
        ref = ref.base
    if isinstance(pv, Orbit):
        pv = pv.base

    assert_almost_equal(ref[:3], pv[:3], precision[0], "Position")
    assert_almost_equal(ref[3:], pv[3:], precision[1], "Velocity")


def test_station(station):

    # lines = """ISS (ZARYA)
    #            1 25544U 98067A   16038.20499631  .00009950  00000-0  15531-3 0  9993
    #            2 25544  51.6445 351.2284 0006997  89.9621  48.8570 15.54478078984606"""
    # orb = Tle(lines).orbit()
    # orb = orb.propagate(Date(2016, 2, 7, 16, 55))

    # from beyond.dates.eop import get_pole

    # print(get_pole(Date(2016, 2, 7, 16, 55).mjd))
    # assert False

    orb = Orbit(
        Date(2016, 2, 7, 16, 55),
        [4225679.11976, 2789527.13836, 4497182.71156,
         -5887.93077439, 3748.50929999, 3194.45322378],
        'cartesian', 'TEME', 'Sgp4'
    )
    archive = orb.copy()

    assert station.orientation == "N"

    orb.frame = station
    orb.form = 'spherical'

    # azimuth
    assert abs(-np.degrees(orb.theta) - 159.75001561831209) <= 1e-9
    # elevation
    assert abs(np.degrees(orb.phi) - 57.894234049230583) <= 1e-9
    # range
    assert abs(orb.r - 471467.65510239213) <= 1e-9

    orb.frame = archive.frame
    orb.form = archive.form
    assert_vector(archive, orb)


def test_station_visibility(orbit, station):

    station.mask = np.array([
        [1.97222205, 2.11184839, 2.53072742, 2.74016693, 3.00196631,
         3.42084533, 3.71755131, 4.15388362, 4.71238898, 6.28318531],
        [0.35255651, 0.34906585, 0.27401669, 0.18675023, 0.28099801,
         0.16580628, 0.12915436, 0.03490659, 0.62831853, 1.3962634]])

    points = list(station.visibility(orbit, start=Date(2018, 4, 5, 21), stop=timedelta(minutes=30), step=timedelta(seconds=30)))
    assert len(points) == 21
    points = list(station.visibility(orbit, start=Date(2018, 4, 5, 21), stop=Date(2018, 4, 5, 21, 30), step=timedelta(seconds=30)))
    assert len(points) == 21

    # Events (AOS, MAX and LOS)
    points = list(station.visibility(orbit, start=Date(2018, 4, 5, 21), stop=timedelta(minutes=70), step=timedelta(seconds=30), events=True))

    # Three more points than precedently, due to the events computation
    assert len(points) == 26

    assert isinstance(points[0].event, SignalEvent)
    assert points[0].event.info == 'AOS'
    assert points[0].event.elev == 0
    assert abs(points[0].phi) < 1e-5
    assert points[0].event.station == station
    assert (points[0].date - Date(2018, 4, 5, 21, 4, 41, 789681)).total_seconds() <= 1e-5

    assert isinstance(points[10].event, MaskEvent)
    assert points[10].event.info == "AOS"
    assert points[10].event.elev == "Mask"
    assert points[10].event.station == station
    assert (points[10].date - Date(2018, 4, 5, 21, 9, 4, 977230)).total_seconds() <= 1e-5

    assert isinstance(points[13].event, MaxEvent)
    assert points[13].event.info == "MAX"
    assert points[13].event.station == station
    assert (points[13].date - Date(2018, 4, 5, 21, 10, 2, 884540)).total_seconds() <= 1e-5

    assert isinstance(points[23].event, MaskEvent)
    assert points[23].event.info == "LOS"
    assert points[23].event.elev == "Mask"
    assert points[23].event.station == station
    assert (points[23].date - Date(2018, 4, 5, 21, 14, 33, 978945)).total_seconds() <= 5e-5

    assert isinstance(points[-1].event, SignalEvent)
    assert points[-1].event.info == 'LOS'
    assert points[-1].event.elev == 0
    assert abs(points[-1].phi) < 1e-5
    assert points[-1].event.station == station
    assert (points[-1].date - Date(2018, 4, 5, 21, 15, 25, 169655)).total_seconds() <= 1e-5
