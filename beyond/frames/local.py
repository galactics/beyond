"""Local orbital reference frame
"""

from numpy.linalg import norm

import numpy as np

from ..utils.matrix import expand


def _split(orbit):
    return orbit[:3], orbit[3:]


def to_local(frame, orbit, expanded=True):
    """Provide the transformation matrix to convert a vector from an inertial frame
    to a local orbital reference frame of choice

    Args:
        frame (str): Name of the local orbital frame ('QSW' or 'TNW')
        orbit (List[float]) : cartesian coordinates (length 6)
        expanded (bool) : If ``True`` the returned matrix is 6x6, 3x3 otherwise
    Return:
        numpy.ndarray : Transformation matrix

    >>> delta_tnw = [1, 0, 0]
    >>> p = [-6142438.668, 3492467.560, -25767.25680]
    >>> v = [505.8479685, 942.7809215, 7435.922231]
    >>> pv = p + v
    >>> mat = to_local("TNW", pv, expanded=False).T
    >>> delta_inert = mat @ delta_tnw
    >>> all(delta_inert == v / norm(v))
    True
    """

    if frame.upper() == "QSW":
        m = to_qsw(orbit)
    elif frame.upper() == "TNW":
        m = to_tnw(orbit)
    else:
        raise ValueError(f"Unknown local orbital frame : {frame}")

    if expanded:
        m = expand(m)

    return m


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

    .. image:: /_static/tnw.svg
        :align: center
        :width: 30%
    """

    pos, vel = _split(orbit)

    t = vel / norm(vel)
    w = np.cross(pos, vel)
    w /= norm(w)
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

    .. image:: /_static/qsw.svg
        :align: center
        :width: 30%
    """

    pos, vel = _split(orbit)

    q = pos / norm(pos)
    w = np.cross(pos, vel)
    w /= norm(w)
    s = np.cross(w, q)

    return np.array([q, s, w])
