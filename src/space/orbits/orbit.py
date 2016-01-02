#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

from .forms import FormTransform
from space.frames.frame import FrameTransform


class Orbit(np.ndarray):
    """Coordinate representation
    """

    def __new__(cls, date, coord, form, frame, **kwargs):

        if len(coord) != 6:
            raise ValueError("Should be 6 in length")

        if type(form) is str:
            form = FormTransform._tree[form]
        elif form.name not in FormTransform._tree:
            raise ValueError("Unknown form '{}'".format(form))

        if type(frame) is str:
            frame = FrameTransform._tree[frame]
        elif frame.name not in FrameTransform._tree:
            raise ValueError("Unknown frame '{}'".format(frame))

        obj = np.ndarray.__new__(cls, (6,), buffer=np.array(coord), dtype=float)
        obj.date = date
        obj.form = form
        obj.frame = frame
        obj.complements = kwargs

        return obj

    def copy(self):
        new_obj = self.__class__(
            self.date, self.base.copy(), self.form,
            self.frame, **self.complements)
        return new_obj

    @property
    def names(self):
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
        fmt = "Orbit =\n  date = {date}\n  coord =\n    form = {form}\n    frame = {frame}\n{coord}".format(
            date=self.date,
            coord=coord_str,
            form=self.form,
            frame=self.frame,
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
        if type(new_frame) is str:
            new_frame = FrameTransform._tree[new_frame]

        ft = FrameTransform(self)
        self.base.setfield(ft.transform(new_frame), dtype=float)
        self.frame = new_frame

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
