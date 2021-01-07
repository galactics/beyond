#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Some matrix basic operations
"""

import numpy as np


def rot1(theta):
    """
    Args:
        theta (float): Angle in radians
    Return:
        Rotation matrix of angle theta around the X-axis
    """
    return np.array(
        [
            [1, 0, 0],
            [0, np.cos(theta), np.sin(theta)],
            [0, -np.sin(theta), np.cos(theta)],
        ]
    )


def rot2(theta):
    """
    Args:
        theta (float): Angle in radians
    Return:
        Rotation matrix of angle theta around the Y-axis
    """
    return np.array(
        [
            [np.cos(theta), 0, -np.sin(theta)],
            [0, 1, 0],
            [np.sin(theta), 0, np.cos(theta)],
        ]
    )


def rot3(theta):
    """
    Args:
        theta (float): Angle in radians
    Return:
        Rotation matrix of angle theta around the Z-axis
    """
    return np.array(
        [
            [np.cos(theta), np.sin(theta), 0],
            [-np.sin(theta), np.cos(theta), 0],
            [0, 0, 1],
        ]
    )


def expand(m, rate=None):
    """Transform a 3x3 rotation matrix into a 6x6 rotation matrix

    Args:
        m (numpy.ndarray) : 3x3 matrix transforming a position vector
            from frame1 to frame2
        rate (numpy.array) : 1D 3 elements vector rate of frame2
            expressed in frame1
    Return:
        numpy.ndarray : 6x6 rotation matrix

    Example:

    >>> m = np.array([[0, -1, 0], [-1, 0, 0], [0, 0, 1]])
    >>> print(expand(m))
    [[ 0. -1.  0.  0.  0.  0.]
     [-1.  0.  0.  0.  0.  0.]
     [ 0.  0.  1.  0.  0.  0.]
     [ 0.  0.  0.  0. -1.  0.]
     [ 0.  0.  0. -1.  0.  0.]
     [ 0.  0.  0.  0.  0.  1.]]
    >>> print(expand(m, rate=[1,2,3]))
    [[ 0. -1.  0.  0.  0.  0.]
     [-1.  0.  0.  0.  0.  0.]
     [ 0.  0.  1.  0.  0.  0.]
     [-3.  0. -2.  0. -1.  0.]
     [ 0.  3.  1. -1.  0.  0.]
     [ 1. -2.  0.  0.  0.  1.]]
    """

    out = np.zeros((6, 6))
    out[:3, :3] = m
    out[3:, 3:] = m

    if rate is not None:
        R = np.array(
            [[0, -rate[2], rate[1]], [rate[2], 0, -rate[0]], [-rate[1], rate[0], 0]]
        )
        out[3:, :3] = -R @ m

    return out
