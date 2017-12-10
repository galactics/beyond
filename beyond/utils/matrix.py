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
    return np.array([
        [1, 0, 0],
        [0, np.cos(theta), np.sin(theta)],
        [0, -np.sin(theta), np.cos(theta)]
    ])


def rot2(theta):
    """
    Args:
        theta (float): Angle in radians
    Return:
        Rotation matrix of angle theta around the Y-axis
    """
    return np.array([
        [np.cos(theta), 0, -np.sin(theta)],
        [0, 1, 0],
        [np.sin(theta), 0, np.cos(theta)]
    ])


def rot3(theta):
    """
    Args:
        theta (float): Angle in radians
    Return:
        Rotation matrix of angle theta around the Z-axis
    """
    return np.array([
        [np.cos(theta), np.sin(theta), 0],
        [-np.sin(theta), np.cos(theta), 0],
        [0, 0, 1]
    ])
