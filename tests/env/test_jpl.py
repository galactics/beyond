
import numpy as np
from pytest import fixture, raises, mark

from beyond.errors import UnknownFrameError, UnknownBodyError
from beyond.config import config
from beyond.env.jpl import get_orbit, list_frames, create_frames
from beyond.dates import Date
from beyond.orbits import Orbit
from beyond.utils.units import AU
from beyond.frames import get_frame


@mark.jpl
def test_get(jplfiles):

    mars = get_orbit('Mars', Date(2018, 1, 14))

    assert isinstance(mars, Orbit)
    assert mars.date.scale.name == "TDB"
    assert abs(32.184313430881999806842941325158 + mars.date._offset) <= np.finfo(float).eps
    assert mars.date.change_scale("UTC") == Date(2018, 1, 14)
    assert str(mars.frame) == "MarsBarycenter"
    assert mars.frame.center.name == "MarsBarycenter"
    assert str(mars.form) == "cartesian"

    # Check if conversion to other frame works as espected
    mars.frame = "EME2000"

    assert np.allclose(mars.base, [
        -1.69346160e+11, -2.00501413e+11, -8.26925988e+10,
        36908.14137465, -7756.92562483, -4081.22549533
    ])

    with raises(UnknownBodyError):
        get_orbit('Jupiter', Date(2018, 1, 14))


@mark.jpl
def test_propagate(jplfiles):
    venus = get_orbit('VenusBarycenter', Date(2018, 1, 14))
    venus = venus.propagate(Date(2018, 1, 15, 12, 27))

    assert abs(32.18435609745404946124835987575 + venus.date._offset) <= np.finfo(float).eps
    assert str(venus.frame) == "SolarSystemBarycenter"
    assert str(venus.form) == "cartesian"
    assert np.allclose(venus.base, [
        5.23110445e+10, -8.51235950e+10, -4.16279990e+10,
        3.05086795e+04, 1.58745616e+04, 5.21182159e+03
    ])


@mark.jpl
def test_transform(jplfiles):

    mars = get_orbit('Mars', Date(2018, 2, 25))
    mars.frame = "SolarSystemBarycenter"
    mars.form = "keplerian"

    assert mars.frame.center.body.name == "Sun"
    assert mars.frame.center.body.m > 1.9e30

    assert 1.3 * AU <= mars.a <= 1.7 * AU


@mark.jpl
def test_list(jplfiles):

    l = list(list_frames())
    assert len(l) == 16


@mark.jpl
def test_create_frames(jplfiles):

    mars = get_frame('Mars')
    assert mars.name == "Mars"

    venus = get_frame('Venus')
    assert venus.name == "Venus"
