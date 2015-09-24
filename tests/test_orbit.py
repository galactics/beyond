#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import raises

from datetime import datetime
import numpy as np

from space.orbits.orbit import Orbit, Coord, CoordForm

ref_coord = [
    7192631.11295, 0.00218439, np.deg2rad(98.50639978),
    np.deg2rad(315.72521309), np.deg2rad(67.54633938), np.deg2rad(174.37062038)
]
ref_cart = np.array([
    -1.77079285e+06, 3.04066799e+06, -6.29108469e+06,
    5.05386500e+03, -4.20539671e+03, -3.45695733e+03
])
ref_date = datetime(2015, 9, 21, 12)
ref_form = Coord.F_KEPL_M


def test_coord_init():

    coord = Coord(ref_coord, ref_form)

    dic = dict(coord._to_list())
    assert dic['a'] == 7192631.11295
    assert dic['e'] == 0.00218439
    assert dic['i'] == 1.7192610104468178
    assert dic['Ω'] == 5.5104444999812001
    assert dic['ω'] == 1.1789060198505055
    assert dic['M'] == 3.043341444376126

    unknown_form = CoordForm("Dummy", None, None)

    with raises(ValueError) as e:
        Coord(ref_coord, unknown_form)
    assert str(e.value) == "Unknown form"

    with raises(ValueError) as e:
        Coord(ref_coord[:-1], ref_form)
    assert str(e.value) == "Should be 6 in length"


def test_coord_unit_transform():

    ref = Coord(ref_coord, ref_form)

    kep = Coord.keplerian_m_to_keplerian(ref)
    assert np.allclose(ref[:5], kep[:5])

    new = Coord.keplerian_to_keplerian_m(kep)
    assert np.allclose(ref, new)

    tle = Coord.keplerian_m_to_tle(ref)
    tle_dict = dict(zip(Coord.F_TLE.param_names, tle))
    ref_dict = dict(ref._to_list())
    assert tle_dict['i'] == ref_dict['i']
    assert tle_dict['Ω'] == ref_dict['Ω']
    assert tle_dict['e'] == ref_dict['e']
    assert tle_dict['ω'] == ref_dict['ω']
    assert tle_dict['M'] == ref_dict['M']

    new = Coord.tle_to_keplerian_m(tle)
    assert np.allclose(new, ref)

    cart = Coord.keplerian_to_cartesian(kep)
    assert np.allclose(cart, ref_cart)

    new = Coord.cartesian_to_keplerian(cart)
    assert np.allclose(new, kep)


def test_coord_global_transform():

    coord = Coord(ref_coord, ref_form)
    backup = coord.copy()

    # Useless transformation, no effect
    coord.transform(Coord.F_KEPL_M)
    assert all(coord == backup)

    coord.transform(Coord.F_CART)
    assert np.allclose(coord, ref_cart)


def test_coord_getattr():
    coord = Coord(ref_coord, ref_form)
    assert coord.a == coord[0]
    assert coord.e == coord[1]
    assert coord.i == coord[2]
    assert coord.Ω == coord[3]
    assert coord.ω == coord[4]
    assert coord.M == coord[5]

    with raises(AttributeError):
        coord.ν == coord[5]

    coord.transform(Coord.F_KEPL)
    assert coord.ν == coord[5]


def test_orbit_change_form():

    orb = Orbit(ref_date, ref_coord, ref_form)

    orb.change_form(Coord.F_CART)
    assert orb.coord.form == Coord.F_CART
    assert np.allclose(orb.coord, ref_cart)


def test_orbit_properties():

    ref_apoapsis = 7208342.6244268175
    ref_periapsis = 7176919.6014731824

    orb = Orbit(ref_date, ref_coord, ref_form)
    assert orb.apoapsis == ref_apoapsis
    assert orb.periapsis == ref_periapsis
    assert orb.apoapsis > orb.periapsis

    orb.change_form(Coord.F_CART)
    assert np.allclose(orb.apoapsis, ref_apoapsis)
    assert np.allclose(orb.periapsis, ref_periapsis)
    assert orb.apoapsis > orb.periapsis
