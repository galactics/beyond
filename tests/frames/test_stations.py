import numpy as np

from pytest import fixture, raises

from beyond.dates import Date, timedelta
from beyond.orbits import Orbit
from beyond.io.tle import Tle
from beyond.propagators.listeners import SignalEvent, MaxEvent, MaskEvent, stations_listeners
from beyond.frames.stations import TopocentricFrame


def test_station(station, helper):

    # lines = """ISS (ZARYA)
    #            1 25544U 98067A   16038.20499631  .00009950  00000-0  15531-3 0  9993
    #            2 25544  51.6445 351.2284 0006997  89.9621  48.8570 15.54478078984606"""
    # orb = Tle(lines).orbit()
    # orb = orb.propagate(Date(2016, 2, 7, 16, 55))

    # from beyond.dates.eop import get_pole

    # print(get_pole(Date(2016, 2, 7, 16, 55).mjd))
    # assert False

    orb = Orbit(
        [4225679.11976, 2789527.13836, 4497182.71156,
         -5887.93077439, 3748.50929999, 3194.45322378],
        Date(2016, 2, 7, 16, 55),
        'cartesian', 'TEME', 'Sgp4'
    )
    archive = orb.copy()

    assert station.orientation.name == "Toulouse"

    orb.frame = station
    orb.form = 'spherical'

    # azimuth
    assert np.isclose(np.degrees(orb.theta), -157.913470813252)
    # elevation
    assert np.isclose(np.degrees(orb.phi), 59.99310662752075)
    # range
    assert np.isclose(orb.r, 461220.80468740925)

    orb.frame = archive.frame
    orb.form = archive.form
    helper.assert_vector(archive, orb)


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
    assert (points[10].date - Date(2018, 4, 5, 21, 9, 7, 895781)).total_seconds() <= 1e-5

    assert isinstance(points[13].event, MaxEvent)
    assert points[13].event.info == "MAX"
    assert points[13].event.station == station
    assert (points[13].date - Date(2018, 4, 5, 21, 10, 4, 514666)).total_seconds() <= 1e-5

    assert isinstance(points[23].event, MaskEvent)
    assert points[23].event.info == "LOS"
    assert points[23].event.elev == "Mask"
    assert points[23].event.station == station
    assert (points[23].date - Date(2018, 4, 5, 21, 14, 35, 771010)).total_seconds() <= 5e-5

    assert isinstance(points[-1].event, SignalEvent)
    assert points[-1].event.info == 'LOS'
    assert points[-1].event.elev == 0
    assert abs(points[-1].phi) < 1e-5
    assert points[-1].event.station == station
    assert (points[-1].date - Date(2018, 4, 5, 21, 15, 25, 183817)).total_seconds() <= 5e-5


def test_station_no_mask(orbit, station):

    station.mask = np.array([
        [1.97222205, 2.11184839, 2.53072742, 2.74016693, 3.00196631,
         3.42084533, 3.71755131, 4.15388362, 4.71238898, 6.28318531],
        [0.35255651, 0.34906585, 0.27401669, 0.18675023, 0.28099801,
         0.16580628, 0.12915436, 0.03490659, 0.62831853, 1.3962634]])

    listeners = stations_listeners(station)
    station.mask = None

    points = station.visibility(
        orbit,
        start=Date(2018, 4, 5, 21),
        stop=timedelta(minutes=30),
        step=timedelta(seconds=30),
        events=listeners,
    )

    with raises(ValueError):
        points = list(points)


_cases = {    
    "3.2": ((56, np.radians(345 + 35/60 + 51/3600), np.radians(-7 -54/60-23.886/3600)), [6119400.27666, -1571479.55734, -871561.12598, 0, 0, 0]),
    "7.1": ((2187, np.radians(-104.883), np.radians(39.007)), [-1275121.9, -4797989.0, 3994297.5, 0, 0, 0]),
}

@fixture(params=_cases.keys())
def case(request):
    return _cases[request.param]


def test_geodetic_cartesian(case):

    (r, theta, phi), ref = case

    sv_station = TopocentricFrame._geodetic_to_cartesian(phi, theta, r)

    assert np.linalg.norm(sv_station) - np.linalg.norm(ref) < 1e-1
    assert np.allclose(sv_station, ref)