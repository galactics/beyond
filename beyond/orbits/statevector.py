#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Orbit description
"""

import numpy as np
from textwrap import indent

from ..constants import c
from ..dates import timedelta
from ..errors import OrbitError
from .forms import get_form, Form
from ..frames.frames import get_frame, orbit2frame
from .man import Man
from .cov import Cov


class StateVector(np.ndarray):
    """Coordinate representation
    """

    def __new__(cls, coord, date, form, frame, **kwargs):
        """
        Args:
            coord (list): 6-length state vector
            date (Date): Date associated with the state vector
            form (str or Form): Name of the form of the state vector
            frame (str or Frame): Name of the frame of reference of the state vector
        """

        if len(coord) != 6:
            raise OrbitError("Should be 6 in length")

        if isinstance(form, str):
            form = get_form(form)

        if isinstance(frame, str):
            frame = get_frame(frame)

        obj = np.ndarray.__new__(
            cls, (6,), buffer=np.array([float(x) for x in coord]), dtype=float
        )
        obj._data = kwargs

        obj._data["date"] = date
        obj._data["form"] = form
        obj._data["frame"] = frame

        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return

        self._data = obj._data.copy()

    def __reduce__(self):
        """For pickling

        see http://stackoverflow.com/questions/26598109
        """
        reconstruct, clsinfo, state = super().__reduce__()

        new_state = {
            "basestate": state,
            "data": self._data,
        }

        return reconstruct, clsinfo, new_state

    def __setstate__(self, state):
        """For pickling

        see http://stackoverflow.com/questions/26598109
        """
        super().__setstate__(state["basestate"])
        self._data = state["data"]

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

        new_compl = {}
        for k, v in self._data.items():
            new_compl[k] = v.copy() if hasattr(v, "copy") else v

        new_obj = self.__class__(self.base, **new_compl)

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
        elif name in self._data.keys():
            res = self._data[name]
        else:
            raise AttributeError(
                "'{}' object has no attribute {!r}".format(self.__class__, name)
            )

        return res

    def __getitem__(self, key):

        if isinstance(key, (int, slice)):
            return super().__getitem__(key)
        else:
            try:
                return self.__getattr__(key)
            except AttributeError as err:
                raise KeyError(str(err))

    def __str__(self):  # pragma: no cover
        return str(self.base)

    def __repr__(self):  # pragma: no cover
        coord_str = "\n".join(
            [
                "    %s = %s" % (name, arg)
                for name, arg in zip(self.form.param_names, self)
            ]
        )

        fmt = """
StateVector =
  date = {date}
  form = {form}
  frame = {frame}
  coord =\n{coord}\n""".format(
            date=self.date, coord=coord_str, form=self.form, frame=self.frame,
        )

        # Add covariance to the repr
        if self.cov is not None:
            fmt += indent(repr(self.cov), " " * 2)

        return fmt

    @property
    def date(self):
        return self._data["date"]

    @date.setter
    def date(self, value):
        self._data["date"] = value

    @property
    def event(self):
        return self._data.get("event")

    @event.setter
    def event(self, value):
        self._data["event"] = value

    @property
    def cov(self):
        """:py:class:`~beyond.orbits.cov.Cov`: 6x6 Covariance matrix

        If a statevector and its covariance are expressed in the same frame,
        changing the frame of the statevector will trigger the change of its
        covariance frame.
        """
        if "cov" not in self._data.keys():
            self._data["cov"] = None

        return self._data["cov"]

    @cov.setter
    def cov(self, value):

        if not isinstance(value, Cov):
            raise TypeError("Unknwon covariance type : ".format(type(value)))

        self._data["cov"] = value
        self._data["cov"].orb = self

    @cov.deleter
    def cov(self):
        self._data["cov"] = None

    @property
    def maneuvers(self):
        """list of :py:class:`~beyond.orbits.man.Man`: Maneuver descriptions usable by the
        propagator. Not all propagators can handle maneuvers. Check their respective documentations
        for more details.
        """
        mans = self._data.setdefault("maneuvers", [])

        if isinstance(mans, Man):
            mans = [mans]
            self._data["maneuvers"] = mans

        return mans

    @maneuvers.setter
    def maneuvers(self, mans):
        if isinstance(mans, Man):
            mans = [mans]

        self._data["maneuvers"] = mans

    @maneuvers.deleter
    def maneuvers(self):
        del self._data["maneuvers"]

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
        return self._data["form"]

    @form.setter
    def form(self, new_form):
        if isinstance(new_form, str):
            new_form = get_form(new_form)
        self.base.setfield(self._data["form"](self, new_form), dtype=float)
        self._data["form"] = new_form

    @property
    def frame(self):
        """:py:class:`~beyond.frames.frames.Frame`: Reference frame of the orbit
        If set as a string (e.g. ``"EME2000"``) will be automatically converted to the
        corresponding Frame object.

        .. code-block:: python

            orbit.frame = "EME2000"
            # is equivalent to
            from beyond.frames.frames import EME2000
            orbit.frame = EME2000
        """
        return self._data["frame"]

    @frame.setter
    def frame(self, new_frame):
        old_form = self.form
        old_frame = self.frame

        if isinstance(new_frame, str):
            new_frame = get_frame(new_frame)

        if new_frame != self.frame:
            self.form = "cartesian"
            try:
                new_coord = self.frame.transform(self, new_frame)
                self.base.setfield(new_coord, dtype=float)
                self._data["frame"] = new_frame
            finally:
                self.form = old_form

        if self.cov is not None and self.cov.frame == old_frame:
            self.cov.frame = new_frame

    def as_frame(self, name, **kwargs):  # pragma: no cover
        """Register the orbit as frame.

        see :py:func:`beyond.frames.frames.orbit2frame` for details of the arguments
        """
        return orbit2frame(name, self, **kwargs)

    def as_orbit(self, propagator):
        from .orbit import Orbit

        new_dict = self._data.copy()
        new_dict["propagator"] = propagator
        return Orbit(self.base, **new_dict)

    @property
    def infos(self):
        """:py:class:`Infos` object of ``self``
        """
        if not hasattr(self, "_infos"):
            self._data["infos"] = Infos(self)
        return self._data["infos"]


class Infos:
    """Compute additional informations on an orbit
    """

    def __init__(self, orb):
        self.orb = orb

    @property
    def kep(self):
        if not hasattr(self, "_kep"):
            self._kep = self.orb.copy(form="keplerian")
        return self._kep

    @property
    def sphe(self):
        if not hasattr(self, "_sphe"):
            self._sphe = self.orb.copy(form="spherical")
        return self._sphe

    @property
    def mu(self):
        return self.orb.frame.center.body.mu

    @property
    def type(self):
        for t in "elliptic hyperbolic parabolic".split():
            if getattr(self, t):
                return t

    @property
    def elliptic(self):
        """True if the orbit it elliptic
        """
        return self.kep.e < 1

    @property
    def parabolic(self):
        """True if the orbit it parabolic
        """
        return self.kep.e == 1

    @property
    def hyperbolic(self):
        """True if the orbit it hyperbolic
        """
        return self.kep.e > 1

    @property
    def energy(self):
        """Mechanical energy of the orbit
        """
        return -self.mu / (2 * self.kep.a)

    @property
    def n(self):
        """Mean motion
        """
        return np.sqrt(self.mu / abs(self.kep.a) ** 3)

    @property
    def period(self):
        """Period of the orbit as a timedelta
        """
        if not self.elliptic:
            raise ValueError("period undefined : orbit is hyperbolic")

        return timedelta(seconds=2 * np.pi * np.sqrt(self.kep.a ** 3 / self.mu))

    @property
    def apocenter(self):
        """Radius of the apocenter
        """
        if not self.elliptic:
            raise ValueError("apocenter undefined : orbit is hyperbolic")

        return self.kep.a * (1 + self.kep.e)

    @property
    def pericenter(self):
        """Radius of the pericenter
        """
        return self.kep.a * (1 - self.kep.e)

    @property
    def r(self):
        """Instantaneous radius
        """
        return self.sphe.r

    @property
    def ra(self):
        """Radius of the apocenter
        """
        return self.apocenter

    @property
    def rp(self):
        """Radius of the pericenter
        """
        return self.pericenter

    @property
    def v(self):
        """Instantaneous velocity
        """
        return np.sqrt(self.mu * (2 / self.r - 1 / self.kep.a))

    @property
    def va(self):
        """Velocity at apocenter
        """
        if not self.elliptic:
            raise ValueError("va undefined : orbit not elliptic")

        return np.sqrt(self.mu * (2 / (self.ra) - 1 / self.kep.a))

    @property
    def vp(self):
        """Velocity at pericenter
        """
        return np.sqrt(self.mu * (2 / (self.rp) - 1 / self.kep.a))

    @property
    def vinf(self):
        """Hyperbolic excess velocity
        """
        if not self.hyperbolic:
            raise ValueError("vinf undefined : orbit not hyperbolic")
        return np.sqrt(self.mu / abs(self.kep.a))

    @property
    def dinf(self):
        """Distance between the focus and the asymptote
        """
        if not self.hyperbolic:
            raise ValueError("dinf undefined : orbit not hyperbolic")

        return abs(self.kep.a * self.kep.e) * np.sqrt(1 - (1 / self.kep.e) ** 2)

    @property
    def cos_fpa(self):
        return (
            np.sqrt(self.mu / (self.kep.a * (1 - self.kep.e ** 2)))
            * (1 + self.kep.e * np.cos(self.kep.nu))
            / self.kep.nu
        )

    @property
    def sin_fpa(self):
        return (
            np.sqrt(self.mu / (self.kep.a * (1 - self.kep.e ** 2)))
            * self.kep.e
            * np.sin(self.kep.nu)
            / self.kep.nu
        )

    @property
    def fpa(self):
        """Flight path angle
        """
        return np.arctan2(self.sin_fpa, self.cos_fpa)

    @property
    def delay(self):
        """:py:class:`~datetime.timedelta`: Light propagation delay from the point
        in space described by ``self`` to the center of the reference frame
        """
        return timedelta(seconds=self.sphe.r / c)
