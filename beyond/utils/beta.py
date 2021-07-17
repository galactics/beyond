"""The beta angle is the angle between the plane of the orbit and the direction
of a distant body (see `wikipedia <https://en.wikipedia.org/wiki/Beta_angle>`__).

If the distant body is the Sun, it will be useful to characterize the spacecraft
illumination during its orbit. If the distant body is another spacecraft, it
will be useful to compute the visibility between the two spacecrafts.
"""

import numpy as np

from ..env.solarsystem import get_body


def beta(orb, ref="Sun"):
    """Compute beta angle

    Args:
        orb (Orbit) : Orbit of the primary spacecraft, expressed in a
            reference frame whose centre is the obscuring body.
        ref (str or Orbit or Ephem) : Secondary object
    Return:
        float: Angle beta in radians
    """

    if isinstance(ref, str):
        ref = get_body(ref)

    orb = orb.copy(form="cartesian")
    p, v = orb[:3], orb[3:]

    w = np.asarray(np.cross(p, v))
    ref_pos = np.asarray(ref.propagate(orb.date).copy(frame=orb.frame)[:3])

    return np.arcsin(w @ ref_pos / (np.linalg.norm(w) * np.linalg.norm(ref_pos)))


def beta_limit(orb):
    """Compute minimal beta angle for a constant visibility on
    another body.

    Below this threshold the spacecraft will experience eclipses during
    a portion of its orbit. Above, it will be fully illuminated during
    all its orbit.

    Args:
        orb (Orbit) : Orbit of the primary spacecraft, expressed in a
            reference frame whose centre is the obscuring body.
    Return:
        float : Angle in radians
    """

    return np.arccos(np.sqrt(1 - (orb.frame.center.body.r / orb.infos.r) ** 2))
