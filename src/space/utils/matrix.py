#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np


def rot1(x):
    return np.array([
        [1, 0, 0],
        [0, np.cos(x), np.sin(x)],
        [0, -np.sin(x), np.cos(x)]
    ])


def rot2(x):
    return np.array([
        [np.cos(x), 0, -np.sin(x)],
        [0, 1, 0],
        [np.sin(x), 0, np.cos(x)]
    ])


def rot3(x):
    return np.array([
        [np.cos(x), np.sin(x), 0],
        [-np.sin(x), np.cos(x), 0],
        [0, 0, 1]
    ])
