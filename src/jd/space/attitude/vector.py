#!/usr/bin/env python

import numpy as np

__all__ = ['Vector']


class Vector(object):
    def __init__(self, new_value=None):
        if not new_value:
            new_value = [0, 0, 0]
        self.set_value(new_value)

    def __add__(self, v2):
        if isinstance(v2, Vector):
            v3 = Vector()
            v3.value = self.value + v2.value
            return v3

    def __mul__(self, v2):
        """Scalar product"""
        if isinstance(v2, Vector):
            x1, y1, z1 = self.value
            x2, y2, z2 = v2.value
            return x1 * x2 + y1 * y2 + z1 * z2
        elif isinstance(v2, (int, float)):
            return Vector(self.value * v2)

    def __rmul__(self, v2):
        return self * v2

    def __xor__(self, v2):
        """Cross product"""
        if isinstance(v2, Vector):
            x1, y1, z1 = self.value
            x2, y2, z2 = v2.value
            return Vector(
                [y1 * z2 - y2 * z1,
                 z1 * x2 - x1 * z2,
                 x1 * y2 - x2 * y1])

    def __neg__(self):
        return Vector(- self.value)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "Vector : "+str(self.value)

    def set_value(self, new_value):
        if isinstance(new_value, list):
            if len(new_value) == 3:
                self.value = np.array(new_value)
        elif isinstance(new_value, np.ndarray):
            if new_value.size == 3:
                self.value = new_value

    def norm(self):
        return sum(self.value)
