
from pytest import yield_fixture
from unittest.mock import patch

import numpy as np
from numpy.testing import assert_almost_equal

from beyond.dates.eop import Eop
from beyond.dates import Date, timedelta
from beyond.orbits import Orbit
from beyond.orbits.tle import Tle
from beyond.frames.stations import create_station


@yield_fixture
def station_env():
    with patch('beyond.frames.iau1980.get_eop') as m, patch('beyond.dates.date.get_eop') as m2:
        m.return_value = Eop(
            x=-0.00951054166666622, y=0.31093590624999734, dpsi=-94.19544791666682, deps=-10.295645833333051,
            dy=-0.10067361111115315, dx=-0.06829513888889051, lod=1.6242802083331438,
            ut1_utc=0.01756018472222477, tai_utc=36.0
        )
        m2.return_value = m.return_value

        yield


def assert_vector(ref, pv, precision=(4, 6)):
    assert_almost_equal(ref[:3], pv[:3], precision[0], "Position")
    assert_almost_equal(ref[3:], pv[3:], precision[1], "Velocity")


def test_station(station_env):

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

    tls = create_station('Toulouse', (43.604482, 1.443962, 172.))

    assert tls.orientation == "N"

    orb.frame = tls
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


def test_station_visibility(station_env):

    lines = """ISS (ZARYA)
               1 25544U 98067A   16038.20499631  .00009950  00000-0  15531-3 0  9993
               2 25544  51.6445 351.2284 0006997  89.9621  48.8570 15.54478078984606"""
    orb = Tle(lines).orbit()

    tls = create_station('Toulouse', (43.604482, 1.443962, 172.))

    points = [point for point in tls.visibility(orb, start=Date(2016, 2, 7, 16, 45), stop=timedelta(minutes=16), step=timedelta(seconds=30))]
    assert len(points) == 21
    points = [point for point in tls.visibility(orb, start=Date(2016, 2, 7, 16, 45), stop=Date(2016, 2, 7, 17, 1), step=timedelta(seconds=30))]
    assert len(points) == 21

    # Events (AOS, MAX and LOS)
    points = [point for point in tls.visibility(orb, start=Date(2016, 2, 7, 16, 45), stop=timedelta(minutes=16), step=timedelta(seconds=30), events=True)]

    # Three more points than precedently, due to the events computation
    assert len(points) == 24

    assert points[0].event.info == 'AOS'
    assert points[0].event.station == tls
    assert points[0].date == Date(2016, 2, 7, 16, 49, 51, 266783)

    assert points[12].event.info == "MAX"
    assert points[12].event.station == tls
    assert points[12].date == Date(2016, 2, 7, 16, 55, 9, 268318)

    assert points[-1].event.info == 'LOS'
    assert points[-1].event.station == tls
    assert points[-1].date == Date(2016, 2, 7, 17, 0, 25, 271351)
