import numpy as np
from pytest import raises
from pathlib import Path
from numpy.testing import assert_almost_equal

from beyond.dates import Date
from beyond.io.horizon import load, HorizonParseError

folder = Path(__file__).parent / "data" 

def test_load():

    for idx in range(1, 6):

        ephem = load(folder.joinpath("tess_{}.txt".format(idx)).open())

        assert ephem.start == Date(2019, 4, 29, scale="TDB")
        assert ephem.stop == Date(2019, 5, 29, scale="TDB")
        assert len(ephem) == 31

        if idx == 1:
            # Type 1 has no velocity
            assert_almost_equal(ephem[0,3:], [0, 0, 0])
        elif idx == 5:
            # Type 5 has no position
            assert_almost_equal(ephem[0,:3], [0, 0, 0])

    with raises(HorizonParseError) as excinfo:
        ephem = load(folder.joinpath("tess_6.txt".format(idx)).open())

    assert str(excinfo.value).endswith("Unknown format : '6 (LT, range, and range-rate)'")


def test_nolabel():
    ephem = load(folder.joinpath("tess_nolabel.txt").open())

    assert ephem.start == Date(2019, 4, 29, scale="TDB")
    assert ephem.stop == Date(2019, 5, 29, scale="TDB")
    assert len(ephem) == 31


def test_units():
    ephem1 = load(folder.joinpath("tess_kms.txt").open())

    assert ephem1.start == Date(2019, 4, 29, scale="TDB")
    assert ephem1.stop == Date(2019, 5, 29, scale="TDB")
    assert len(ephem1) == 31

    ephem2 = load(folder.joinpath("tess_kmd.txt").open())

    assert ephem2.start == Date(2019, 4, 29, scale="TDB")
    assert ephem2.stop == Date(2019, 5, 29, scale="TDB")
    assert len(ephem2) == 31

    assert np.allclose(ephem1, ephem2)


def test_ecliptic():
    ref_ephem = load(folder.joinpath("mro_equatorial.txt").open())

    assert ref_ephem.start == Date(2019, 4, 29, scale="TDB")
    assert ref_ephem.stop == Date(2019, 5, 29, scale="TDB")
    assert len(ref_ephem) == 31

    ephem = load(folder.joinpath("mro_ecliptic.txt").open())

    # Identical values along X, because the X axis (the vernal point)
    # is the same in equatorial and equatorial representation
    assert np.allclose(ref_ephem[:, 0], ephem[:, 0])

    # There is slight differences between how the Horizon's
    # conversion and our own, but it is globally consistent
    assert np.allclose(ref_ephem[:, 1], ephem[:, 1], rtol=1e-4)
    assert np.allclose(ref_ephem[:, 2], ephem[:, 2], rtol=1e-3)


def test_no_data():

    with raises(HorizonParseError):
        ephem = load(folder.joinpath("hayabusa.txt").open())