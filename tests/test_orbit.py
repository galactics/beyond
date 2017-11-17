#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import raises, fixture

import numpy as np

from beyond.constants import Earth
from beyond.dates.date import Date
from beyond.orbits.tle import Tle
from beyond.orbits.orbit import Orbit
from beyond.orbits.forms import FormTransform, Form

ref_coord = [
    7192631.11295, 0.00218439, np.deg2rad(98.50639978),
    np.deg2rad(315.72521309), np.deg2rad(67.54633938), np.deg2rad(174.37062038)
]
ref_cart = np.array([
    -1.77079285e+06, 3.04066799e+06, -6.29108469e+06,
    5.05386500e+03, -4.20539671e+03, -3.45695733e+03
])
ref_form = FormTransform.KEPL_M
ref_frame = "EME2000"
ref_propagator = 'Sgp4'


@fixture
def ref_date():
    return Date(2015, 9, 21, 12)


@fixture
def ref_orbit(ref_date):
    return Orbit(ref_date, ref_coord, ref_form, ref_frame, ref_propagator)


def test_coord_init(ref_date, ref_orbit):

    assert ref_orbit['a'] == 7192631.11295
    assert ref_orbit['e'] == 0.00218439
    assert ref_orbit['i'] == 1.7192610104468178
    assert ref_orbit['Ω'] == 5.5104444999812001
    assert ref_orbit['ω'] == 1.1789060198505055
    assert ref_orbit['M'] == 3.043341444376126

    unknown_form = Form("Dummy", None, None)

    with raises(ValueError) as e:
        Orbit(ref_date, ref_coord, unknown_form, ref_frame, ref_propagator)
    assert str(e.value) == "Unknown form 'Dummy'"

    with raises(ValueError) as e:
        Orbit(ref_date, ref_coord[:-1], ref_form, ref_frame, ref_propagator)
    assert str(e.value) == "Should be 6 in length"


def test_init_cart(ref_date):
    a = Orbit(ref_date, ref_cart, FormTransform.CART.name, ref_frame, ref_propagator)
    assert a.form == FormTransform.CART


def test_coord_unit_transform(ref_orbit):

    kep = FormTransform._keplerian_mean_to_keplerian(ref_orbit, Earth)
    assert np.allclose(ref_orbit[:5], kep[:5])

    new = FormTransform._keplerian_to_keplerian_mean(kep, Earth)
    assert np.allclose(ref_orbit, new)

    tle = FormTransform._keplerian_mean_to_tle(ref_orbit, Earth)
    tle_dict = dict(zip(FormTransform.TLE.param_names, tle))
    assert tle_dict['i'] == ref_orbit['i']
    assert tle_dict['Ω'] == ref_orbit['Ω']
    assert tle_dict['e'] == ref_orbit['e']
    assert tle_dict['ω'] == ref_orbit['ω']
    assert tle_dict['M'] == ref_orbit['M']

    new = FormTransform._tle_to_keplerian_mean(tle, Earth)
    assert np.allclose(new, ref_orbit)

    cart = FormTransform._keplerian_to_cartesian(kep, Earth)
    assert np.allclose(cart, ref_cart)

    new = FormTransform._cartesian_to_keplerian(cart, Earth)
    assert np.allclose(new, kep)


def test_coord_global_transform(ref_orbit):

    backup = ref_orbit.copy()

    # Useless transformation, no effect
    ref_orbit.form = 'keplerian_mean'
    assert all(ref_orbit == backup)

    ref_orbit.form = FormTransform.CART
    assert np.allclose(ref_orbit, ref_cart)


def test_coord_attributes_access(ref_orbit):
    assert ref_orbit.a == ref_orbit[0]
    assert ref_orbit.e == ref_orbit[1]
    assert ref_orbit.i == ref_orbit[2]
    assert ref_orbit.Ω == ref_orbit[3]
    assert ref_orbit.Omega == ref_orbit[3]
    assert ref_orbit['Omega'] == ref_orbit[3]
    assert ref_orbit.ω == ref_orbit[4]
    assert ref_orbit.omega == ref_orbit[4]
    assert ref_orbit['omega'] == ref_orbit[4]
    assert ref_orbit.M == ref_orbit[5]

    with raises(AttributeError):
        ref_orbit.ν == ref_orbit[5]

    with raises(KeyError):
        ref_orbit["ν"]

    ref_orbit.form = FormTransform.KEPL
    assert ref_orbit.ν == ref_orbit[5]


def test_orbit_change_form(ref_orbit):

    ref_orbit.form = FormTransform.CART.name
    assert ref_orbit.form == FormTransform.CART
    assert np.allclose(ref_orbit, ref_cart)


def test_tle_back_and_fro():

    txt = """1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
             2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"""
    orb = Tle(txt).orbit()
    new_txt = Tle.from_orbit(orb, norad_id=25544, cospar_id='1998-067A')

    assert str(new_txt) == """1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  9991
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391999990"""

# def test_orbit_properties(ref_orbit):

#     ref_apoapsis = 7208342.6244268175
#     ref_periapsis = 7176919.6014731824

#     assert ref_orbit.apoapsis == ref_apoapsis
#     assert ref_orbit.periapsis == ref_periapsis
#     assert ref_orbit.apoapsis > ref_orbit.periapsis

#     ref_orbit.form = "Cartesian"
#     assert np.allclose(ref_orbit.apoapsis, ref_apoapsis)
#     assert np.allclose(ref_orbit.periapsis, ref_periapsis)
#     assert ref_orbit.apoapsis > ref_orbit.periapsis
