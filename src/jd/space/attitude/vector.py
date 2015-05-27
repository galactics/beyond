#!/usr/bin/env python

import numpy as np

__all__ = ['Vector']


class Vector(object):
    """Object representing a 3D vector
    """

    _value = []

    def __init__(self, value=None):
        """
        >>> import numpy
        >>> Vector(numpy.array([1, 2, 3]))
        Vector : [1 2 3]
        >>> Vector([1, 2, 3])
        Vector : [1 2 3]
        >>> Vector((1, 2, 3))
        Vector : [1 2 3]
        >>> Vector((1, 2, 3, 4))
        Traceback (most recent call last):
            ...
        ValueError: Vector accepts only iterable of length 3
        >>> Vector(1)
        Traceback (most recent call last):
            ...
        TypeError: Vector accepts only numpy.ndarray, list or tuple.
        >>> Vector()
        Vector : [0 0 0]
        """

        if value is None:
            value = [0, 0, 0]
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if type(value) in (np.ndarray, list, tuple):
            if len(value) == 3:
                if type(value) is np.ndarray:
                    self._value = value
                else:
                    self._value = np.array(value)
            else:
                raise ValueError("Vector accepts only iterable of length 3")
        else:
            raise TypeError("Vector accepts only numpy.ndarray, list or tuple.")

    def __add__(self, v2):
        """Addition

        >>> v1 = Vector((1, 0, 0))
        >>> v2 = Vector((0, 1, 1))
        >>> v1 + v2
        Vector : [1 1 1]
        >>> v1 + 5
        Traceback (most recent call last):
            ...
        TypeError: Vectors only sum with themselves
        """
        if not isinstance(v2, Vector):
            raise TypeError("Vectors only sum with themselves")

        v3 = Vector()
        v3.value = self.value + v2.value
        return v3

    def __mul__(self, v2):
        """Scalar product

        >>> v1 = Vector((1, 0, 0))
        >>> v2 = Vector((0, 1, 0))
        >>> v1 * v2
        0

        >>> v1 * 2
        Vector : [2 0 0]
        >>> v1 * [1, 2, 3]
        Traceback (most recent call last):
            ...
        TypeError: Scalar product only accepts Vectors or numeric
        """
        if isinstance(v2, Vector):
            x1, y1, z1 = self.value
            x2, y2, z2 = v2.value
            return x1 * x2 + y1 * y2 + z1 * z2
        elif isinstance(v2, (int, float)):
            return Vector(self.value * v2)
        else:
            raise TypeError("Scalar product only accepts Vectors or numeric")

    def __rmul__(self, v2):
        """
        >>> 2 * Vector([1, 0, 0])
        Vector : [2 0 0]
        """

        return self * v2

    def __xor__(self, v2):
        """Cross product

        >>> v1 = Vector([1, 0, 0])
        >>> v2 = Vector([0, 1, 0])
        >>> v1 ^ v2
        Vector : [0 0 1]

        >>> v1 ^ 3
        Traceback (most recent call last):
            ...
        TypeError: Cross-product only accepts Vectors
        """
        if not isinstance(v2, Vector):
            raise TypeError("Cross-product only accepts Vectors")

        x1, y1, z1 = self.value
        x2, y2, z2 = v2.value
        return Vector(
            [y1 * z2 - y2 * z1,
             z1 * x2 - x1 * z2,
             x1 * y2 - x2 * y1])

    def __neg__(self):
        """
        >>> - Vector([1, 0, 0])
        Vector : [-1  0  0]
        """
        return Vector(- self.value)

    def __str__(self):
        """
        >>> print(Vector([1, 0, 0]))
        [1 0 0]
        """
        return str(self.value)

    def __repr__(self):
        return "Vector : "+str(self.value)

    def norm(self):
        """
        Compute the norm of the vector

        >>> v1 = Vector([1, 2, 3])
        >>> v1.norm()
        6
        """
        return sum(self.value)
