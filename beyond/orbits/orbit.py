#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Orbit description
"""

import numpy as np

from ..constants import c
from ..dates import timedelta
from ..errors import OrbitError
from .forms import get_form, Form
from .ephem import Ephem
from ..frames.frames import get_frame, orbit2frame
from ..propagators import get_propagator
from .man import Maneuver


class Orbit(np.ndarray):
    """Coordinate representation
    """

    def __new__(cls, date, coord, form, frame, propagator, **kwargs):
        """
        Args:
            date (Date): Date associated with the state vector
            coord (list): 6-length state vector
            form (str or Form): Name of the form of the state vector
            frame (str or Frame): Name of the frame of reference of the state vector
            propagator (str or Propagator): Name of the propagator to be used to extrapolate
        """

        if len(coord) != 6:
            raise OrbitError("Should be 6 in length")

        if isinstance(form, str):
            form = get_form(form)

        if isinstance(frame, str):
            frame = get_frame(frame)

        obj = np.ndarray.__new__(cls, (6,), buffer=np.array([float(x) for x in coord]), dtype=float)
        obj.date = date
        obj._form = form
        obj._frame = frame
        obj.propagator = propagator
        obj.complements = kwargs
        obj.event = None

        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return

        self.date = obj.date
        self._form = obj._form
        self._frame = obj._frame
        self._propagator = obj._propagator
        self.complements = obj.complements.copy()

    def __reduce__(self):
        """For pickling

        see http://stackoverflow.com/questions/26598109
        """
        reconstruct, clsinfo, state = super().__reduce__()

        new_state = {
            'basestate': state,
            'date': self.date,
            '_form': self._form,
            '_frame': self._frame,
            '_propagator': self._propagator,
            'complements': self.complements,
        }

        return reconstruct, clsinfo, new_state

    def __setstate__(self, state):
        """For pickling

        see http://stackoverflow.com/questions/26598109
        """
        super().__setstate__(state['basestate'])
        self.date = state['date']
        self._form = state['_form']
        self._frame = state['_frame']
        self._propagator = state['_propagator']
        self.complements = state['complements']

    def copy(self, *, frame=None, form=None):
        """Provide a new instance of the same point in space-time

        Keyword Args:
            frame (str or Frame): Frame to convert the new instance into
            form (str or Form): Form to convert the new instance into
        Return:
            Orbit:

        Override :py:meth:`numpy.ndarray.copy()` to include additional
        fields
        """
        new_obj = self.__class__(
            self.date, self.base.copy(), self.form,
            self.frame, self.propagator.copy() if self.propagator is not None else None,
            **self.complements
        )
        if frame and frame != self.frame:
            new_obj.frame = frame
        if form and form != self.form:
            new_obj.form = form
        return new_obj

    def __getattr__(self, name):

        name = Form.alt.get(name, name)

        # Verification if the variable is available in the current form
        if name in self.form.param_names:
            i = self.form.param_names.index(name)
            res = self[i]
        elif name in self.complements.keys():
            res = self.complements[name]
        else:
            raise AttributeError("'{}' object has no attribute {!r}".format(self.__class__, name))

        return res

    def __getitem__(self, key):

        if isinstance(key, (int, slice)):
            return super().__getitem__(key)
        else:
            try:
                return self.__getattr__(key)
            except AttributeError as err:
                raise KeyError(str(err))

    def __repr__(self):  # pragma: no cover
        coord_str = '\n'.join(
            ["    %s = %s" % (name, arg) for name, arg in zip(self.form.param_names, self)]
        )

        if self.propagator is None:
            # No propagator defined
            propagator = self.propagator
        elif self.propagator.orbit is None:
            propagator = self.propagator.__class__.__name__
        else:
            propagator = "%s (initialised)" % self.propagator.__class__.__name__

        fmt = """
Orbit =
  date = {date}
  form = {form}
  frame = {frame}
  propag = {propag}
  coord =\n{coord}""".format(
            date=self.date,
            coord=coord_str,
            form=self.form,
            frame=self.frame,
            propag=propagator
        )
        return fmt

    @property
    def maneuvers(self):
        """list of :py:class:`~beyond.orbits.man.Maneuver`: Maneuver descriptions usable by the
        propagator. Not all propagators can handle maneuvers. Check their respective documentations
        for more details.
        """
        mans = self.complements.setdefault('maneuvers', [])

        if isinstance(mans, Maneuver):
            mans = [mans]
            self.complements['maneuvers'] = mans

        return mans

    @maneuvers.setter
    def maneuvers(self, mans):
        if isinstance(mans, Maneuver):
            mans = [mans]

        self.complements['maneuvers'] = mans

    @maneuvers.deleter
    def maneuvers(self):
        del self.complements['maneuvers']

    @property
    def form(self):
        """:py:class:`~beyond.orbits.forms.Form`: Form of the coordinates of the orbit

        If set as a string (e.g. ``"cartesian"``) will be automatically converted to the
        corresponding Form object.

        .. code-block:: python

            orbit.form = "cartesian"
            # is equivalent to
            from beyond.orbits.forms import FormTransform
            orbit.form = FormTransform.CART
        """
        return self._form

    @form.setter
    def form(self, new_form):
        if isinstance(new_form, str):
            new_form = get_form(new_form)
        self.base.setfield(self._form(self, new_form), dtype=float)
        self._form = new_form

    @property
    def frame(self):
        """:py:class:`~beyond.frames.frames.Frame`: Reference frame of the orbit

        if set as a string (e.g. ``"EME2000"``) will be automatically converted to the corresponding
        Frame class.

        .. code-block:: python

            orbit.frame = "EME2000"
            # is equivalent to
            from beyond.frames.frame import EME2000
            orbit.frame = EME2000
        """
        return self._frame

    @frame.setter
    def frame(self, new_frame):
        old_form = self.form

        if isinstance(new_frame, str):
            new_frame = get_frame(new_frame)

        if new_frame != self.frame:
            self.form = 'cartesian'
            try:
                new_coord = self.frame(self.date, self).transform(new_frame.name)
                self.base.setfield(new_coord, dtype=float)
                self._frame = new_frame
            finally:
                self.form = old_form

    @property
    def propagator(self):
        """:py:class:`~beyond.propagators.base.Propagator`: Propagator of the orbit.

        if set as a string (e.g. ``"Sgp4"``) will be automatically converted to the corresponding
        propagator class and instanciated without arguments.
        """
        return self._propagator

    @propagator.setter
    def propagator(self, new_propagator):

        if isinstance(new_propagator, str):
            new_propagator = get_propagator(new_propagator)()

        self._propagator = new_propagator

    @property
    def delay(self):
        """:py:class:`~datetime.timedelta`: Light propagation delay from the point
        in space described by ``self`` to the center of the reference frame
        """
        return timedelta(seconds=self.copy(form='spherical').r / c)

    @property
    def delayed_date(self):
        """:py:class:`~beyond.dates.date.Date`: Date taking into account the
        light propagation delay from the point in space described by ``self``
        to the center of the reference frame
        """
        return self.date + self.delay

    def propagate(self, date):
        """Propagate the orbit to a new date

        Args:
            date (Date)
        Return:
            Orbit
        """

        if self.propagator.orbit is not self:
            self.propagator.orbit = self

        return self.propagator.propagate(date)

    def iter(self, *args, **kwargs):
        """see :py:meth:`Propagator.iter() <beyond.propagators.base.Propagator.iter>`
        """
        if self.propagator.orbit is not self:
            self.propagator.orbit = self

        return self.propagator.iter(*args, **kwargs)

    def ephemeris(self, start, stop, step, **kwargs):
        """Generator giving the propagation of the orbit at different dates

        Args:
            start (Date)
            stop (Date or timedelta)
            step (timedelta)
        Yield:
            Orbit
        """

        for orb in self.iter(start=start, stop=stop, step=step, inclusive=True, **kwargs):
            yield orb

    def ephem(self, start, stop, step, **kwargs):
        """Tabulation of Orbit at a given step and on a given date range

        Args:
            start (Date)
            stop (Date or timedelta)
            step (timedelta)
        Return:
            Ephem:
        """
        return Ephem(self.ephemeris(start, stop, step, **kwargs))

    def as_frame(self, name, **kwargs):  # pragma: no cover
        """Register the orbit as frame.

        see :py:func:`beyond.frames.frames.orbit2frame` for details of the arguments
        """
        return orbit2frame(name, self, **kwargs)
