import numpy as np
from numpy.linalg import norm as norm


def _split_state_vector(state_vector):
    state_vector = np.array(state_vector)
    return state_vector[:3], state_vector[3:]


def inertial_to_tnw(state_vector):
    """
    Args:
        state_vector (list): Array of length 6
    Returns:
        numpy.ndarray: matrix to convert from inertial frame to TNW.

    >>> delta_tnw = [1, 0, 0]
    >>> p = [-6142438.668, 3492467.560, -25767.25680]
    >>> v = [505.8479685, 942.7809215, 7435.922231]
    >>> pv = p + v
    >>> mat = inertial_to_tnw(pv).T
    >>> delta_inert = mat @ delta_tnw
    >>> all(delta_inert == v / norm(v))
    True
    """

    pos, vel = _split_state_vector(state_vector)

    t = vel / norm(vel)
    w = np.cross(pos, vel) / (norm(pos) * norm(vel))
    n = np.cross(w, t)

    return np.array([t, n, w])


def inertial_to_qsw(state_vector):
    """
    Args:
        state_vector (list): Array of length 6
    Returns:
        numpy.ndarray: matrix to convert from inertial frame to QSW

    >>> delta_qsw = [1, 0, 0]
    >>> p = [-6142438.668, 3492467.560, -25767.25680]
    >>> v = [505.8479685, 942.7809215, 7435.922231]
    >>> pv = p + v
    >>> mat = inertial_to_qsw(pv).T
    >>> delta_inert = mat @ delta_qsw
    >>> all(delta_inert == p / norm(p))
    True
    """

    pos, vel = _split_state_vector(state_vector)

    q = pos / norm(pos)
    w = np.cross(pos, vel) / (norm(pos) * norm(vel))
    s = np.cross(w, q)

    return np.array([q, s, w])
