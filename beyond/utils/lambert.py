"""Lambert's problem solvers
"""

import logging
import numpy as np

log = logging.getLogger(__name__)


def _F(nr0, nr1, A, z, duration, mu):
    y_z = _y(nr0, nr1, A, z)
    return (
        (y_z / _C(z)) ** 1.5 * _S(z)
        + A * np.sqrt(y_z)
        - np.sqrt(mu) * duration.total_seconds()
    )


def _dF(nr0, nr1, A, z):
    if z == 0:
        y_z = _y(nr0, nr1, A, 0)
        r = np.sqrt(2) * 40 * y_z ** 1.5 + A / 8 * (
            np.sqrt(y_z) + A * np.sqrt(1 / 2 / y_z)
        )
    else:
        y_z = _y(nr0, nr1, A, z)
        r = (y_z / _C(z)) ** 1.5 * (
            1 / 2 / z * (_C(z) - 3 * _S(z) / 2 / _C(z)) + 3 * _S(z) ** 2 / 4 / _C(z)
        ) + A / 8 * (3 * _S(z) / _C(z) * np.sqrt(y_z) + A * np.sqrt(_C(z) / y_z))

    return r


def _y(nr0, nr1, A, z):
    return nr0 + nr1 + A * (z * _S(z) - 1) / np.sqrt(_C(z))


def _C(z):
    if z > 0:
        c = (1 - np.cos(np.sqrt(z))) / z
    elif z < 0:
        c = (np.cosh(np.sqrt(-z)) - 1) / (-z)
    else:
        c = 1 / 2

    return c


def _S(z):
    if z > 0:
        s = (np.sqrt(z) - np.sin(np.sqrt(z))) / (np.sqrt(z)) ** 3
    elif z < 0:
        s = (np.sinh(np.sqrt(-z)) - np.sqrt(-z)) / (np.sqrt(-z)) ** 3
    else:
        s = 1 / 6

    return s


def lambert(orb0, orb1, prograde=True):
    """Solve `Lamber's problem <https://en.wikipedia.org/wiki/Lambert%27s_problem>`__,
    with the solution provided by Howard D. Curtis in chapter 5.3 of his book,
    "Orbital Mechanics for Engineering Students" (ed. 2014)

    Args:
        orb0 (Orbit) : Initial orbit
        orb1 (Orbit) : Target orbit
        prograde (bool) : If True, provides a prograde solution. retrograde
            otherwise
    Return
        Tuple : Initial and Target :py:class:`Orbits <beyond.orbits.orbit.Orbit>` patched with solution's velocities

    The initial orbit reference frame is the one used for the computation.
    So if one desires to compute an interplanetary opportunity, orb0 should
    be expressed in the "Sun" or "SolarSystemBarycenter" reference frame.

    .. warning:: This is only compatible with elliptical orbits
    """

    orb0 = orb0.copy(form="cartesian")
    orb1 = orb1.copy(frame=orb0.frame, form="cartesian")
    duration = orb1.date - orb0.date
    mu = orb0.frame.center.body.mu

    r0, r1 = np.asarray(orb0[:3]), np.asarray(orb1[:3])

    v0, v1 = _lambert(r0, r1, duration, mu, prograde)

    orb0[3:] = v0
    orb1[3:] = v1

    return orb0, orb1


def _lambert(r0, r1, duration, mu, prograde=True):
    """Solve `Lamber's problem <https://en.wikipedia.org/wiki/Lambert%27s_problem>`__,
    with the solution provided by Howard D. Curtis in chapter 5.3 of his book,
    "Orbital Mechanics for Engineering Students" (ed. 2014)

    Args:
        r0 (List[float]) : Initial cartesian coordinates
        r1 (List[float]) : Target cartesian coordinates
        duration (datetime.timedelta) : Duration of the transfer
        mu (float) : Standard gravitational parameter applied
        prograde (bool) : If True, provides a prograde solution. retrograde
            otherwise
    Return:
        Tuple[numpy.array] : Initial and Target cartesian velocity

    .. warning:: This is only compatible with elliptical orbits
    """

    nr0, nr1 = np.linalg.norm(r0), np.linalg.norm(r1)

    cr = np.cross(r0, r1)
    dtheta = np.arccos(r0 @ r1 / (nr0 * nr1))

    if prograde and cr[2] < 0:
        dtheta = 2 * np.pi - dtheta
    elif not prograde and cr[2] >= 0:
        dtheta = 2 * np.pi - dtheta

    A = np.sin(dtheta) * np.sqrt(nr0 * nr1 / (1 - np.cos(dtheta)))

    # z < 0 hyperbola
    # z = 0 parabola
    # z > 0 ellipse

    # In Curtis, the initial value is -100, with z an angle in degrees.
    # By initializing at 0, we cut off potential hyperbolic solutions
    z = 0  # - np.pi / 2

    # This dichotomy should better be rewritten, with an efficient
    # numpy-friendly implementation
    while _F(nr0, nr1, A, z, duration, mu) < 0:
        # z += 0.01
        z += 0.05

    tol = 1e-8
    nmax = 5000
    ratio = 1

    for n in range(nmax):
        ratio = _F(nr0, nr1, A, z, duration, mu) / _dF(nr0, nr1, A, z)
        z -= ratio
        if abs(ratio) > tol:
            break
    else:  # pragma: no cover
        log.warning("Max iteration exceeded")

    f = 1 - _y(nr0, nr1, A, z) / nr0
    g = A * np.sqrt(abs(_y(nr0, nr1, A, z)) / mu)
    gdot = 1 - _y(nr0, nr1, A, z) / nr1
    v0 = 1 / g * (r1 - f * r0)
    v1 = 1 / g * (gdot * r1 - r0)

    return v0, v1
