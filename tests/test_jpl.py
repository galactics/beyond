
import numpy as np
from pytest import fixture
from pathlib import Path

from beyond.config import config
from beyond.env.jpl import get_body, list_bodies
from beyond.dates import Date
from beyond.orbits import Orbit


@fixture
def jplfiles():
    config['env'].update({
        'jpl': [
            str(Path(__file__).parent / "data" / "jpl" / "de403_2000-2020.bsp")
        ]
    })


def test_get(jplfiles):

    mars = get_body('Mars', Date(2018, 1, 14))

    assert isinstance(mars, Orbit)
    assert mars.date.scale.name == "TDB"
    assert mars.date.change_scale("UTC") == Date(2018, 1, 14)
    assert str(mars.frame) == "MarsBarycenter"
    assert str(mars.form) == "cartesian"

    # Check if conversion to other frame works as espected
    mars.frame = "EME2000"

    assert np.allclose(mars, [
        -1.69346160e+11, -2.00501413e+11, -8.26925988e+10,
        -3.18886341e+09, 6.70198374e+08, 3.52617883e+08
    ])


def test_propagate(jplfiles):
    venus = get_body('VenusBarycenter', Date(2018, 1, 14))
    venus = venus.propagate(Date(2018, 1, 15, 12, 27))

    assert str(venus.frame) == "SolarSystemBarycenter"
    assert str(venus.form) == "cartesian"
    assert np.allclose(venus, [
        5.23110445e+10, -8.51235950e+10, -4.16279990e+10,
        -2.63594991e+09, -1.37156213e+09, -4.50301386e+08
    ])


def test_list(jplfiles):

    l = list(list_bodies())
    assert len(l) == 15
