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


def expand(m):
    """Duplicate a 3x3 matrix diagonaly into a 6x6 matrix

    Args:
        m1 (numpy.ndarray) : 3x3 matrix
    Return:
        numpy.ndarray : 6x6

    Example:

    >>> m = np.array([[0, -1, 0], [-1, 0, 0], [0, 0, 1]])
    >>> print(expand(m))
    [[ 0. -1.  0.  0.  0.  0.]
     [-1.  0.  0.  0.  0.  0.]
     [ 0.  0.  1.  0.  0.  0.]
     [ 0.  0.  0.  0. -1.  0.]
     [ 0.  0.  0. -1.  0.  0.]
     [ 0.  0.  0.  0.  0.  1.]]
    """

    out = np.identity(6)
    out[:3, :3] = m
    out[3:, 3:] = m

    return out
