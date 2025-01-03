from abc import ABCMeta, abstractmethod
from datetime import timedelta

from ..dates import Date
from .listeners import Speaker


class Propagator(metaclass=ABCMeta):
    """Base class for propagators"""

    orbit = None

    @abstractmethod
    def iter(self, **kwargs):
        pass

    @abstractmethod
    def propagate(self, date):
        """Propagate the orbit to a given date

        Args:
            date (Date)
        Return:
            ~beyond.orbits.orbit.Orbit:
        """
        pass

    def copy(self):
        return self.__class__()

    def __repr__(self):
        return f"<Propagator {self.__class__.__name__} at {hex(id(self))}>"


class AnalyticalPropagator(Speaker, Propagator):
    """Base class for analytical propagators (SGP4, Eckstein-Heschler, etc.)"""

    def iter(self, **kwargs):
        """Compute a range of orbits between two dates

        Keyword Arguments:
            dates (list of :py:class:`~beyond.dates.date.Date`): Dates from which iterate over
            start (Date or None): Date of the first point
            stop (Date, timedelta or None): Date of the last point
            step (timedelta or None): Step to use during the computation. Use the same step as
                `self` if `None`
            listeners (list of:py:class:`~beyond.orbits.listeners.Listener`):
        Yield:
            :py:class:`Orbit`:

        There is two ways to use the iter() method.

        If *dates* is defined, it should be an iterable of dates. This could be
        a generator as per :py:meth:`Date.range <beyond.dates.date.Date.range>`, or a list.

        .. code-block:: python

            # Create two successive ranges of dates, with different steps
            dates = list(Date.range(Date(2019, 3, 23), Date(2019, 3, 24), timedelta(minutes=3)))
            dates.extend(
                Date.range(Date(2019, 3, 24),
                Date(2019, 3, 25),
                timedelta(minutes=10),
                inclusive=True)
            )
            propag.iter(dates=dates)

        The alternative, is the use of *start*, *stop* and *step* keyword arguments
        which work exactly as :code:`Date.range(start, stop, step, inclusive=True)`

        If one of *start*, *stop* or *step* arguments is set to ``None`` it will keep
        the same property as the generating ephemeris.

        .. code-block:: python

            propag.iter(stop=stop)  # If the iterator has a default step (e.g. numerical propagator)
            propag.iter(stop=stop, step=step)
            propag.iter(start=start, stop=stop, step=step)
        """

        if "dates" not in kwargs:
            start = kwargs.setdefault("start", self.orbit.date)
            stop = kwargs.get("stop")
            step = kwargs.setdefault("step", getattr(self, "step", None))

            if stop is None:
                raise ValueError("The end of the propagation should be defined")

            start = self.orbit.date if start is None else start
            step = self.step if step is None else step

            kwargs["start"] = start

            if isinstance(kwargs["stop"], timedelta):
                kwargs["stop"] = start + kwargs["stop"]
            if start > kwargs["stop"] and step.total_seconds() > 0:
                kwargs["step"] = -step

        listeners = kwargs.pop("listeners", [])

        self.clear_listeners(listeners)

        for orb in self._iter(**kwargs):
            for listen_orb in self.listen(orb, listeners):
                yield listen_orb
            yield orb

    def _iter(self, **kwargs):
        start = kwargs.get("start")
        stop = kwargs.get("stop")
        step = kwargs.get("step")
        dates = kwargs.get("dates")

        if dates:
            for date in dates:
                yield self.propagate(date)
        else:
            for date in Date.range(start, stop, step, inclusive=True):
                yield self.propagate(date)

    @classmethod
    def fit_statevector(cls, statevector):
        """Find the MeanOrbit that provide the input StateVector

        Args:
            statevector (StateVector)
        Return:
            MeanOrbit: MeanOrbit object which, when propagated at the same date,
                returns the input StateVector
        """
        raise NotImplementedError()


class NumericalPropagator(Propagator):
    """Base class for numerical propagators (e.g. Cowell)"""

    def iter(self, **kwargs):
        if "dates" not in kwargs:
            start = kwargs.setdefault("start", self.orbit.date)
            stop = kwargs.get("stop")
            step = kwargs.setdefault("step", getattr(self, "step", None))

            if stop is None:
                raise ValueError("The end of the propagation should be defined")

            start = self.orbit.date if start is None else start
            step = self.step if step is None else step

            if isinstance(kwargs["stop"], timedelta):
                kwargs["stop"] = start + kwargs["stop"]
            if start > kwargs["stop"] and step.total_seconds() > 0:
                kwargs["step"] = -step

        for orb in self._iter(**kwargs):
            yield orb

    def propagate(self, date):
        if isinstance(date, timedelta):
            date = self.orbit.date + date

        return next(self.iter(start=date, stop=date))
