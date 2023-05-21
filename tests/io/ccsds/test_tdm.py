
from pytest import fixture

from beyond.dates import Date, timedelta
from beyond.io.ccsds import dumps, loads
from beyond.utils.measures import MeasureSet, Range, Azimut, Elevation


@fixture
def measureset(tle, station):

    path = "{0} {1} {0}".format(station.name, tle.cospar_id).split()

    aos = Date(2008, 9, 20, 18, 16, 3, 690790)
    los = Date(2008, 9, 20, 18, 24, 58, 852563)

    measures = MeasureSet([])
    for orb in tle.iter(start=aos, stop=los, step=timedelta(seconds=5)):
        sph = orb.copy(frame=station, form='spherical')
        measures.append(Range(path, orb.date, sph.r * 2))
        measures.append(Azimut(path, orb.date, sph.theta))
        measures.append(Elevation(path, orb.date, sph.phi))

    return measures


def test_dump(measureset, station, ccsds_format, datafile, helper):

    ref = datafile("tdm")
    txt = dumps(measureset, fmt=ccsds_format)

    helper.assert_string(ref, txt)


def test_load(measureset, datafile):

    data = loads(datafile("tdm"))

    assert len(measureset) == len(data)
    assert measureset.types == data.types
    assert measureset.start == data.start
    assert measureset.stop == data.stop
    assert measureset.sources == data.sources
    assert measureset.paths == data.paths
