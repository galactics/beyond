"""Local orbital reference frame
"""

from numpy.linalg import norm

import numpy as np


def _split(orbit):
    return orbit[:3], orbit[3:]


def to_tnw(orbit):
    """In the TNW Local Orbital Reference Frame, x is oriented along the velocity vector,
    z along the angular momentum, and y complete the frame.

    Args:
        orbit (list): Array of length 6
    Return:
        numpy.ndarray: matrix to convert from inertial frame to TNW.

    >>> delta_tnw = [1, 0, 0]
    >>> p = [-6142438.668, 3492467.560, -25767.25680]
    >>> v = [505.8479685, 942.7809215, 7435.922231]
    >>> pv = p + v
    >>> mat = to_tnw(pv).T
    >>> delta_inert = mat @ delta_tnw
    >>> all(delta_inert == v / norm(v))
    True
    """

    pos, vel = _split(orbit)

    t = vel / norm(vel)
    w = np.cross(pos, vel) / (norm(pos) * norm(vel))
    n = np.cross(w, t)

    return np.array([t, n, w])


def to_qsw(orbit):
    """In the QSW Local Orbital Reference Frame, x is oriented along the position vector,
    z along the angular momentum, and y complete the frame.

    The frame is sometimes also called RSW (where R stands for radial) or LVLH (Local
    Vertical Local Horizontal).

    Args:
        orbit (list): Array of length 6
    Return:
        numpy.ndarray: matrix to convert from inertial frame to QSW

    >>> delta_qsw = [1, 0, 0]
    >>> p = [-6142438.668, 3492467.560, -25767.25680]
    >>> v = [505.8479685, 942.7809215, 7435.922231]
    >>> pv = p + v
    >>> mat = to_qsw(pv).T
    >>> delta_inert = mat @ delta_qsw
    >>> all(delta_inert == p / norm(p))
    True
    """

    pos, vel = _split(orbit)

    q = pos / norm(pos)
    w = np.cross(pos, vel) / (norm(pos) * norm(vel))
    s = np.cross(w, q)

    return np.array([q, s, w])
