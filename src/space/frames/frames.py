#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta
from space.utils.tree import Node


# Séparation Transformation des instances

class FrameNode(Node):
    pass


# ... et implémentation des instances

class Frame(metaclass=ABCMeta):

    _instances = {}

    def __new__(cls, *args, **kwargs):

        if cls.__name__ not in cls._instances:
            cls._instances[cls.__name__] = super().__new__(cls, *args, **kwargs)
        return cls._instances[cls.__name__]


class InertialFrame(Frame):
    pass


class RotatingFrame(Frame):
    pass


class TopocentricFrame(Frame):

    def __init__(self, name, based_on, coordinates):

        if type(based_on) is not RotatingFrame:
            raise TypeError()

        self.name = name
        self.coord = coordinates


class EME2000(InertialFrame):
    pass


class TEME(InertialFrame):
    pass


class ITRF(RotatingFrame):
    pass
