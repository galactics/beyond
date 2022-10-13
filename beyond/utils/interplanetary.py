"""Module to compute planetary captures and flybys

.. image:: /_static/bplane.svg
    :width: 50%
    :align: center
"""

import numpy as np
from collections import namedtuple

norm = np.linalg.norm


class BPlane(namedtuple("BPlane", "B theta S T R e h")):
    """B-plane characteristics

    Args:
        B : 3d B vector
        theta : angle
        S : vector collinear to v_infinity
        T : vector along the ecliptic
        R : S x T
        e : 3d eccentricity vector
        h : angular momentum vector
    """


def bplane(orb):
    """Compute the B vector details

    Args:
        orb (Orbit) :
    Return:
        BPlane : B-plane characteristics as a namedtuple
    """

    orb = orb.copy(form="cartesian")

    µ = orb.frame.center.body.mu
    r, v = orb[:3], orb[3:]
    rn = norm(r)
    vn = norm(v)
    e = (vn**2 * r - (r @ v) * v) / µ - r / rn
    e_norm = norm(e)
    ê = e / e_norm

    h = np.cross(r, v)
    h_norm = norm(h)
    ĥ = h / h_norm

    β = np.arccos(1 / e_norm)

    S = ê * np.cos(β) + np.cross(ĥ, ê) * np.sin(β)
    N = np.array([0, 0, 1])
    T = np.cross(S, N) / norm(np.cross(S, N))
    R = np.cross(S, T)

    B_norm = abs(orb.infos.kep.a) * np.sqrt(e_norm**2 - 1)
    B = B_norm * np.cross(S, ĥ)

    BT = B @ T
    θ = np.arccos(BT / (norm(B) * norm(T)))

    return BPlane(B, θ, S, T, R, e, h)


def flyby(v_inf_in, v_inf_out, µ):
    """Compute B vector characteristics for a flyby

    Args:
        v_inf_in (numpy.array, shape 3) : arrival excess velocity
        v_inf_out (numpy.array, shape 3) : exit excess velocity
        µ (float) : standard gravitational parameter of the body flown-by
    Return:
        tuple : tuple with length 2, the first element being the B vector
        (a numpy array), the second being the periapsis radius
    """

    vin_n = norm(v_inf_in)
    vout_n = norm(v_inf_out)

    S = v_inf_in / norm(v_inf_in)
    h = np.cross(r, v)
    h_norm = norm(h)
    ĥ = h / h_norm

    Bu = np.cross(S, ĥ)
    N = np.array([0, 0, 1])
    T = np.cross(S, K)
    R = np.cross(S, T)

    # Turn angle
    δ = np.arccos(v_inf_in @ v_inf_out / (vin_n * vout_n))

    rp = µ / (vin_n**2) * (1 / np.cos((np.pi - δ) / 2) - 1)
    B = µ / (vin_n**2) * np.sqrt((1 + vin_n**2 * rp / µ) ** 2 - 1)

    B = B * Bu

    return B, rp
