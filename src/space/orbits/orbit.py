#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from datetime import timedelta

from .forms import FormTransform
from space.frames.frame import get_frame
from space.propagators import *


class Orbit(np.ndarray):
    """Coordinate representation
    """

    def __new__(cls, date, coord, form, frame, propagator, **kwargs):

        if len(coord) != 6:
            raise ValueError("Should be 6 in length")

        if type(form) is str:
            form = FormTransform._tree[form]
        elif form.name not in FormTransform._tree:
            raise ValueError("Unknown form '{}'".format(form))

        if type(frame) is str:
            frame = get_frame(frame)

        if type(propagator) is str:
            propagator = eval(propagator)

        obj = np.ndarray.__new__(cls, (6,), buffer=np.array(coord), dtype=float)
        obj.date = date
        obj.form = form
        obj.frame = frame
        obj.propagator = propagator
        obj.complements = kwargs

        return obj

    def copy(self):
        """Override :py:meth:`numpy.ndarray.copy()` to include additional
        fields
        """
        new_obj = self.__class__(
            self.date, self.base.copy(), self.form,
            self.frame, self.propagator, **self.complements)
        return new_obj

    @property
    def names(self):
        """Gives the names of the fields
        """
        return self.form.param_names

    def __getattr__(self, name):

        convert = {
            'theta': 'θ',
            'phi': 'φ',
            'Omega': "Ω",
            'omega': 'ω',
            'nu': "ν",
            'theta_dot': 'θ_dot',
            'phi_dot': 'φ_dot',
        }

        # Conversion of variable name to utf-8
        if name in convert:
            name = convert[name]

        # Verification if the variable is available in the current form
        if name not in self.names:
            raise AttributeError("'{}' object has no attribute {!r}".format(self.__class__, name))

        i = self.names.index(name)
        return self[i]

    def __getitem__(self, key):

        if type(key) in (int, slice):
            return super().__getitem__(key)
        else:
            try:
                return self.__getattr__(key)
            except AttributeError as e:
                raise KeyError(str(e))

    def __repr__(self):  # pragma: no cover
        coord_str = '\n'.join(
            [" " * 4 + "%s = %s" % (name, arg) for name, arg in zip(self.names, self)]
        )

        propagator = self.propagator.__name__ if self.propagator is not None else self.propagator

        fmt = "Orbit =\n  date = {date}\n  form = {form}\n  frame = {frame}\n  propag = {propag}\n  coord =\n{coord}".format(
            date=self.date,
            coord=coord_str,
            form=self.form,
            frame=self.frame,
            propag=propagator
        )
        return fmt

    @property
    def pv(self):
        """Get the coordinates of the orbit in terms of position and velocity

        Returns:
            Orbit: 2-length, first element is position, second is velocity.
                The frame is unchanged
        """
        return self.change_form('Cartesian')

    def change_form(self, new_form):
        """Changes the form of the coordinates in-place

        Args:
            new_form (str or Form)
        """
        if type(new_form) is str:
            new_form = FormTransform._tree[new_form]

        ft = FormTransform(self)
        self.base.setfield(ft.transform(new_form), dtype=float)
        self.form = new_form

    def change_frame(self, new_frame):
        """Convert the orbit to a new frame of reference

        Args:
            new_frame (str or Frame)
        """
        old_form = self.form

        if type(new_frame) is str:
            new_frame = get_frame(new_frame)

        try:
            self.change_form('cartesian')
            new_coord = self.frame(self.date, self).transform(new_frame.name)
            self.base.setfield(new_coord, dtype=float)
            self.frame = new_frame
        finally:
            self.change_form(old_form)

    def propagate(self, date):
        """Propagate the orbit to a new date

        Args:
            date (Date)
        Return:
            Orbit
        """
        propag_obj = self.propagator(self)
        return propag_obj.propagate(date)

    def ephemeris(self, start, stop, step):
        """Generator giving the propagation of the orbit at different dates

        Args:
            start (Date)
            stop (Date or timedelta)
            step (timedelta)
        Yield:
            Orbit
        """

        if isinstance(stop, timedelta):
            stop = start + stop

        cursor = start
        while cursor < stop:
            yield self.propagate(cursor)
            cursor += step

    # @property
    # def apoapsis(self):

    #     coord = self.coord.copy()
    #     if coord.form not in (Coord.KEPL, Coord.KEPL_M):
    #         coord.transform(Coord.KEPL)

    #     a, e = coord[:2]
    #     return a * (1 + e)

    # @property
    # def periapsis(self):

    #     coord = self.coord.copy()
    #     if coord.form not in (Coord.KEPL, Coord.KEPL_M):
    #         coord.transform(Coord.KEPL)

    #     a, e = coord[:2]
    #     return a * (1 - e)
