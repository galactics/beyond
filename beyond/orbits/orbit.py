#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Orbit description
"""

import numpy as np
from textwrap import indent

from .ephem import Ephem
from .statevector import StateVector
from ..frames.frames import orbit2frame
from ..propagators import Propagator, get_propagator, UnknownPropagatorError


class Orbit(StateVector):
    """Extrapolable coordinates (i.e. a :py:class:`~beyond.orbits.statevector.StateVector`
    associated to a :py:class:`~beyond.propagators.base.Propagator` via the :py:meth:`Orbit.propagate` method)
    """

    def __new__(cls, coord, date, form, frame, propagator, **kwargs):
        """
        Args:
            coord (list): 6-length state vector
            date (Date): Date associated with the state vector
            form (str or Form): Name of the form of the state vector
            frame (str or Frame): Name of the frame of reference of the state vector
            propagator (str or Propagator): Name of the propagator to be used to extrapolate
        """

        obj = super().__new__(cls, coord, date, form, frame, **kwargs)
        obj.propagator = propagator

        return obj

    def __str__(self):
        return str(self.base)

    def __repr__(self):  # pragma: no cover
        coord_str = "\n".join(
            [
                "    %s = %s" % (name, arg)
                for name, arg in zip(self.form.param_names, self)
            ]
        )

        if self.propagator is None:
            # No propagator defined
            propagator = self.propagator
        elif self.propagator.orbit is None:
            propagator = self.propagator.__class__.__name__
        else:
            propagator = f"{self.propagator.__class__.__name__} (initialised)"

        fmt = f"""
Orbit =
  date = {self.date}
  form = {self.form}
  frame = {self.frame}
  propag = {propagator}
  coord =
{coord_str}
"""

        # Add covariance to the repr
        if self.cov is not None:
            fmt += indent(repr(self.cov), " " * 2)

        # Add man to the repr if there is some
        if self.maneuvers:
            fmt += "  maneuvers =\n"
            for man in self.maneuvers:
                fmt += indent(repr(man), " " * 4)

        return fmt

    @property
    def propagator(self):
        """:py:class:`~beyond.propagators.base.Propagator`: Propagator of the orbit.
        If set as a string (e.g. ``"Sgp4"``) will be automatically converted to the corresponding
        propagator class and instantiated without arguments.
        """
        return self._data["propagator"]

    @propagator.setter
    def propagator(self, new_propagator):

        if isinstance(new_propagator, str):
            new_propagator = get_propagator(new_propagator)()

        self._data["propagator"] = new_propagator

    def propagate(self, date):
        """Propagate the orbit to a new date

        Args:
            date (Date)
        Return:
            StateVector
        """

        if not isinstance(self.propagator, Propagator):
            raise UnknownPropagatorError(self.propagator)

        if self.propagator.orbit is not self:
            self.propagator.orbit = self

        return self.propagator.propagate(date)

    def iter(self, **kwargs):
        """see :py:meth:`Propagator.iter() <beyond.propagators.base.Propagator.iter>`"""
        if self.propagator.orbit is not self:
            self.propagator.orbit = self

        return self.propagator.iter(**kwargs)

    def ephemeris(self, **kwargs):
        """Generator giving the propagation of the orbit at different dates

        Args:
            start (Date)
            stop (Date or timedelta)
            step (timedelta)
        Yield:
            Orbit
        """

        for orb in self.iter(inclusive=True, **kwargs):
            yield orb

    def ephem(self, **kwargs):
        """Tabulation of Orbit at a given step and on a given date range

        Args:
            start (Date)
            stop (Date or timedelta)
            step (timedelta)
        Return:
            Ephem:
        """
        return Ephem(self.ephemeris(**kwargs))

    def as_frame(self, name, **kwargs):  # pragma: no cover
        """Register the orbit as frame.

        see :py:func:`beyond.frames.frames.orbit2frame` for details of the arguments
        """
        return orbit2frame(name, self, **kwargs)

    def as_statevector(self):
        new_dict = self._data.copy()
        new_dict.pop("propagator")
        return StateVector(self.base, **new_dict)
