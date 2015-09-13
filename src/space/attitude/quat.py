#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This packages allows python to handle quaternions"""

import numpy as np
from math import cos, sin, asin, atan2
from sys import float_info

from .vector import Vector

__all__ = ['Quat']


class Quat(object):
    """Class representing the quaternion"""

    _value = None

    def __init__(self, value=None):

        if value is None:
            value = [1, 0, 0, 0]

        self.value = value

    @property
    def real(self):  # pragma: no cover
        return self._value[0]

    @property
    def vector(self):  # pragma: no cover
        return Vector(self._value[1:])

    @property
    def value(self):
        return self._value

    @real.setter
    def real(self, value):  # pragma: no cover
        if type(value) not in (float, int):
            raise TypeError("Quarternion real-part should be a float.\
                    `{0}` given".format(type(value)))

        self._value[0] = value

    @vector.setter
    def vector(self, value):  # pragma: no cover
        if type(value) in (tuple, list):
            value = np.array(value)
        elif isinstance(value, np.ndarray):
            pass
        elif isinstance(value, Vector):
            value = value.value
        else:
            raise TypeError("'{0}' is not a correct type of value.\n\
                Only 'list', 'numpy.ndarray' and 'Vector' are allowed.\
                ".format(type(value)))

        if len(value) != 3:
            raise ValueError("Quaternion vector-part length should be 3")

        self._value[1:] = value

    @value.setter
    def value(self, value):  # pragma: no cover
        if type(value) in (tuple, list):
            value = np.array(value)
        elif isinstance(value, np.ndarray):
            value = value
        else:
            raise TypeError("'{0}' is not a correct type of value.\
                \nOnly 'list' and 'numpy.ndarray' are allowed.\
                ".format(type(value)))

        if len(value) != 4:
            raise ValueError("Quaternion length must be of 4")

        super(Quat, self).__setattr__('_value', value)
        self.normalize()

    @property
    def r(self):
        return self.real

    @property
    def v(self):
        return self.vector

    @r.setter
    def r(self, value):
        self.real = value

    @v.setter
    def v(self, value):
        self.vector = value

    def __add__(self, q2):
        """Addition override

        >>> q1 = Quat([1, 0, 0, 0])
        >>> q2 = Quat([0, 1, 0, 0])
        >>> q1 + q2
        Quaternion : [ 0.70710678  0.70710678  0.          0.        ]
        >>> q2 + q1
        Quaternion : [ 0.70710678  0.70710678  0.          0.        ]

        >>> q1 + 2
        Traceback (most recent call last):
            ...
        TypeError: Only a Quat instance could be added to a Quat
        """
        if not isinstance(q2, Quat):
            raise TypeError("Only a Quat instance could be added to a Quat")

        q3 = Quat()
        q3.value = self.value + q2.value
        return q3

    def __mul__(self, q2):
        """Hamilton's product
        q3 = q1 x q2

        >>> q1 = Quat([1, 0, 0, 0])
        >>> q2 = Quat([0, 1, 0, 0])
        >>> q1 * q2
        Quaternion : [ 0.  1.  0.  0.]
        >>> q2 * q1
        Quaternion : [ 0.  1.  0.  0.]

        >>> q1 * 2
        Traceback (most recent call last):
            ...
        TypeError: The Hamilton product only accepts Quat instances
        """

        if not isinstance(q2, Quat):
            raise TypeError("The Hamilton product only accepts Quat instances")

        q3 = Quat()
        q3.r = float(self.r * q2.r - self.v * q2.v)
        q3.v = (self.r * q2.v) + (q2.r * self.v) + (self.v ^ q2.v)
        return q3

    def __invert__(self):
        """
        >>> quat = Quat((0,1,0,0))
        >>> ~ quat
        Quaternion : [ 0. -1. -0. -0.]
        """
        return self.conj()

    def normalize(self):
        """Normalize in place

        >>> q = Quat()
        >>> q.r = 2
        >>> q
        Quaternion : [ 2.  0.  0.  0.]
        >>> q.normalize()
        >>> q
        Quaternion : [ 1.  0.  0.  0.]
        """
        for i, v in enumerate(self.value):
            # If the value is lower than the precision
            # it's rounded to zero

            if abs(v) < float_info.epsilon * 10:
                self.value[i] = 0.

        super(Quat, self).__setattr__('_value', self.value / self.norm())

    def conj(self):
        q = Quat(self.value)
        q.value[1:] = -self.value[1:]
        return q

    def norm(self):
        return np.sqrt(np.sum(self.value**2))

    def to_euler_angles(self, degrees=False):
        """Convert quaternion to Euler's angles

        Returns:
            numpy.ndarray : Euler angles in radians

        >>> quat = Quat([1, 0, 0, 0])
        >>> quat.to_euler_angles()
        array([ 0.,  0.,  0.])


        >>> quat = Quat([0, 1, 0, 0])
        >>> quat.to_euler_angles(degrees=True)
        array([ 180.,    0.,    0.])

        >>> quat = Quat([0, 0.5, 0.5, 0])
        >>> quat.to_euler_angles(degrees=True)
        array([ 180.,    0.,   90.])

        """
        q0, q1, q2, q3 = self.value
        phi = atan2(2 * (q0 * q1 + q2 * q3), 1 - 2 * (q1**2 + q2**2))
        theta = asin(2 * (q0 * q2 - q3 * q1))
        psi = atan2(2 * (q0 * q3 + q1 * q2), 1 - 2 * (q2**2 + q3**2))

        euler = np.array([phi, theta, psi])
        if degrees:
            euler = np.degrees(euler)

        return euler

    def to_matrix(self):
        """Convert quaternion to 4x4 rotation matrix

        Returns:
            numpy.ndarray : 4x4 rotation matrix

        >>> q = Quat.from_euler_angles((0, 90, 0), degrees=True)
        >>> q.to_matrix()
        array([[ 0.70710678,  0.        ,  0.70710678,  0.        ],
               [-0.        ,  0.70710678, -0.        ,  0.70710678],
               [-0.70710678,  0.        ,  0.70710678, -0.        ],
               [-0.        , -0.70710678,  0.        ,  0.70710678]])
        """

        q0, q1, q2, q3 = self.value

        return np.array([[q0,  q1,  q2,  q3],
                         [-q1, q0,  -q3, q2],
                         [-q2, q3,  q0,  -q1],
                         [-q3, -q2, q1,  q0]])

    @classmethod
    def from_euler_angles(cls, euler, degrees=False):
        """Create a Quat instance from Euler angles

        Args:
            euler (iterable) :

        >>> Quat.from_euler_angles([0, 0, 0])
        Quaternion : [ 1.  0.  0.  0.]

        >>> Quat.from_euler_angles([180, 0, 0], degrees=True)
        Quaternion : [ 0.  1.  0.  0.]
        """

        if degrees:
            phi, theta, psi = np.radians(euler)
        else:
            phi, theta, psi = euler

        q = [None] * 4
        q[0] = cos(phi/2.) * cos(theta/2.) * cos(psi/2.) \
            + sin(phi/2.) * sin(theta/2.) * sin(psi/2.)
        q[1] = sin(phi/2.) * cos(theta/2.) * cos(psi/2.) \
            - cos(phi/2.) * sin(theta/2.) * sin(psi/2.)
        q[2] = cos(phi/2.) * sin(theta/2.) * cos(psi/2.) \
            + sin(phi/2.) * cos(theta/2.) * sin(psi/2.)
        q[3] = cos(phi/2.) * cos(theta/2.) * sin(psi/2.) \
            - sin(phi/2.) * sin(theta/2.) * cos(psi/2.)
        return cls(q)

    def __str__(self):
        """
        >>> print(Quat([1, 0, 0, 0]))
        [ 1.  0.  0.  0.]
        """
        return str(self.value)

    def __repr__(self):
        return "Quaternion : "+str(self.value)
