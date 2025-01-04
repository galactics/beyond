#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pytest import raises, fixture

import numpy as np
from pickle import loads, dumps

from beyond.errors import UnknownFormError, OrbitError
from beyond.constants import Earth
from beyond.dates.date import Date
from beyond.io.tle import Tle
from beyond.orbits.orbit import Orbit
from beyond.orbits.cov import Cov
from beyond.orbits.forms import Form, CART, KEPL_M, KEPL, TLE
from beyond.frames.frames import ITRF, MOD, EME2000

ref_coord = [
    7192631.11295, 0.00218439, np.deg2rad(98.50639978),
    np.deg2rad(315.72521309), np.deg2rad(67.54633938), np.deg2rad(174.37062038)
]
ref_cart = np.array([
    -1.77079285e+06, 3.04066799e+06, -6.29108469e+06,
    5.05386500e+03, -4.20539671e+03, -3.45695733e+03
])
ref_form = KEPL_M
ref_frame = "EME2000"
ref_propagator = 'Sgp4'


@fixture
def ref_date():
    return Date(2015, 9, 21, 12)


@fixture
def ref_orbit(ref_date):
    return Orbit(ref_coord, ref_date, ref_form, ref_frame, ref_propagator)


def test_coord_init(ref_date, ref_orbit):

    assert ref_orbit['a'] == 7192631.11295
    assert ref_orbit['e'] == 0.00218439
    assert ref_orbit['i'] == 1.7192610104468178
    assert ref_orbit['Ω'] == 5.5104444999812001
    assert ref_orbit['ω'] == 1.1789060198505055
    assert ref_orbit['M'] == 3.043341444376126

    with raises(UnknownFormError) as e:
        Orbit(ref_coord, ref_date, "Dummy", ref_frame, ref_propagator)

    assert str(e.value) == "Unknown form 'Dummy'"

    with raises(OrbitError) as e:
        Orbit(ref_coord[:-1], ref_date, ref_form, ref_frame, ref_propagator)
    assert str(e.value) == "Should be 6 in length, got 5"


def test_init_cart(ref_date):
    a = Orbit(ref_cart, ref_date, CART.name, ref_frame, ref_propagator)
    assert a.form == CART


def test_coord_unit_transform(ref_orbit):

    kep_e = Form._keplerian_mean_to_keplerian_eccentric(ref_orbit, Earth)
    kep = Form._keplerian_eccentric_to_keplerian(kep_e, Earth)
    assert np.allclose(ref_orbit.base[:5], kep[:5])

    tmp_kep_e = Form._keplerian_to_keplerian_eccentric(kep, Earth)
    new = Form._keplerian_eccentric_to_keplerian_mean(tmp_kep_e, Earth)
    assert np.allclose(ref_orbit.base, new)

    tle = Form._keplerian_mean_to_tle(ref_orbit, Earth)
    tle_dict = dict(zip(TLE.param_names, tle))
    assert tle_dict['i'] == ref_orbit['i']
    assert tle_dict['Ω'] == ref_orbit['Ω']
    assert tle_dict['e'] == ref_orbit['e']
    assert tle_dict['ω'] == ref_orbit['ω']
    assert tle_dict['M'] == ref_orbit['M']

    new = Form._tle_to_keplerian_mean(tle, Earth)
    assert np.allclose(new, ref_orbit.base)

    cart = Form._keplerian_to_cartesian(kep, Earth)
    assert np.allclose(cart, ref_cart)

    new = Form._cartesian_to_keplerian(cart, Earth)
    assert np.allclose(new, kep)


def test_coord_global_transform(ref_orbit):

    backup = ref_orbit.copy()

    # Useless transformation, no effect
    ref_orbit.form = 'keplerian_mean'
    assert all(ref_orbit == backup)

    ref_orbit.form = CART
    assert np.allclose(ref_orbit.base, ref_cart)


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

    ref_orbit.form = KEPL
    assert ref_orbit.ν == ref_orbit[5]


def test_orbit_change_form(ref_orbit):

    ref_orbit.form = CART.name
    assert ref_orbit.form == CART
    assert np.allclose(ref_orbit.base, ref_cart)


def test_tle_to_and_from():

    txt = """1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927
2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"""
    orb = Tle(txt).orbit()
    new_txt = Tle.from_orbit(orb, norad_id=25544, cospar_id='1998-067A')

    assert str(new_txt) == txt


def test_pickle(ref_orbit):

    # Pickling is used when distributing objects to multprocesses, so it's useful to check if
    # we can still do it
    txt = dumps(ref_orbit)
    orb = loads(txt)

    assert all(ref_orbit == orb)
    assert ref_orbit.date == orb.date
    assert ref_orbit.frame.name == orb.frame.name
    assert ref_orbit.form.name == orb.form.name
    assert ref_orbit.propagator.__class__ == orb.propagator.__class__


def test_orbit_infos(ref_orbit):

    ref_apocenter = 7208342.6244268175
    ref_pericenter = 7176919.6014731824

    assert ref_orbit.infos.apocenter == ref_apocenter
    assert ref_orbit.infos.pericenter == ref_pericenter
    assert ref_orbit.infos.apocenter > ref_orbit.infos.pericenter

    ref_orbit.form = "Cartesian"
    assert np.allclose(ref_orbit.infos.apocenter, ref_apocenter)
    assert np.allclose(ref_orbit.infos.pericenter, ref_pericenter)
    assert ref_orbit.infos.apocenter > ref_orbit.infos.pericenter


def test_cov(ref_orbit):

    cov = np.array([
        [2.06425972e+04, -2.17645124e+05, 2.09095698e+04, 2.32394582e+02, -2.30899159e+01, -5.24016849e+01],
        [-2.17645124e+05, 7.82259109e+08, -1.09026368e+06, -8.82448779e+05, 5.94453113e+03, 9.79109455e+02],
        [ 2.09095698e+04, -1.09026368e+06, 2.48261626e+04, 1.21445858e+03, -3.15835320e+01, -5.61469192e+01],
        [ 2.32394582e+02, -8.82448779e+05, 1.21445858e+03, 9.95481364e+02, -6.68934414e+00, -1.06654468e+00],
        [-2.30899159e+01, 5.94453113e+03, -3.15835320e+01, -6.68934414e+00, 7.51789642e-02, 7.12271449e-02],
        [-5.24016849e+01, 9.79109455e+02, -5.61469192e+01, -1.06654468e+00, 7.12271449e-02, 1.85992455e-01]
    ])
    ref_orbit.cov = Cov(ref_orbit, cov, "QSW")

    assert np.allclose(ref_orbit.cov, cov)

    ref_orbit.cov.frame = "TNW"
    # As ref_orbit is nearly circular, T and S are equivalent
    assert np.allclose(ref_orbit.cov[0, 0], cov[1, 1])

    ref_orbit.cov.frame = "QSW"
    assert np.allclose(ref_orbit.cov, cov)

    # No modification when source frame is the same as target frame
    ref_orbit.cov.frame = "QSW"
    assert np.allclose(ref_orbit.cov, cov)

    # conversion into same frame as ref_orbit.frame
    ref_orbit.cov.frame = ref_orbit.frame
    # assert np.linalg.norm(ref_orbit.cov) == np.linalg.norm(cov)

    ref_orbit.cov.frame = "QSW"
    assert np.allclose(ref_orbit.cov, cov)

    cov_tnw = ref_orbit.cov.copy(frame='TNW')
    ref_orbit.cov.frame = "TNW"
    assert np.allclose(cov_tnw, ref_orbit.cov)

    cov_parent = ref_orbit.cov.copy(frame=ref_orbit.frame)
    ref_orbit.cov.frame = ref_orbit.frame
    assert np.allclose(cov_parent, ref_orbit.cov)

    ref_orbit.cov = cov_parent
    assert np.allclose(ref_orbit.cov, cov_parent)


def test_cov_frame(ref_orbit):

    cov = np.array([
        [2.06425972e+04, -2.17645124e+05, 2.09095698e+04, 2.32394582e+02, -2.30899159e+01, -5.24016849e+01],
        [-2.17645124e+05, 7.82259109e+08, -1.09026368e+06, -8.82448779e+05, 5.94453113e+03, 9.79109455e+02],
        [ 2.09095698e+04, -1.09026368e+06, 2.48261626e+04, 1.21445858e+03, -3.15835320e+01, -5.61469192e+01],
        [ 2.32394582e+02, -8.82448779e+05, 1.21445858e+03, 9.95481364e+02, -6.68934414e+00, -1.06654468e+00],
        [-2.30899159e+01, 5.94453113e+03, -3.15835320e+01, -6.68934414e+00, 7.51789642e-02, 7.12271449e-02],
        [-5.24016849e+01, 9.79109455e+02, -5.61469192e+01, -1.06654468e+00, 7.12271449e-02, 1.85992455e-01]
    ])
    ref_cov = Cov(ref_orbit, cov, "QSW")
    cov = ref_cov.copy()

    # Check if no transformation are done when copying
    assert np.allclose(ref_cov, cov)

    cov.frame = "TNW"
    cov.frame = "QSW"
    assert np.allclose(ref_cov, cov)

    cov_eme = cov.copy(frame=EME2000)
    cov.frame = "ITRF"
    cov.frame = EME2000

    assert np.allclose(cov_eme, cov)

    # Covariance attached to an orbit object follows its frame change
    ref_orbit.cov = ref_cov.copy(frame=ref_orbit.frame)
    ref_orbit.frame = "ITRF"

    assert ref_orbit.frame == ref_orbit.cov.frame
