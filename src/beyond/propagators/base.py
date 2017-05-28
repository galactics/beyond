
from abc import ABCMeta, abstractmethod
from datetime import timedelta

from ..utils import Date
from ..orbits.listeners import Speaker


class Propagator(Speaker, metaclass=ABCMeta):
    """Base class for propagators
    """

    orbit = None

    @abstractmethod
    def _iter(self, star, stop, step, **kwargs):
        pass

    @abstractmethod
    def propagate(self, start):
        pass

    def iter(self, *, start=None, stop=None, step=None, **kwargs):
        """
        Examples:
            propag.iter(stop)
            propag.iter(stop, step)
            propag.iter(start, stop, step)
        """

        if stop is None:
            raise ValueError("The end of the propagation should be defined")

        start = self.orbit.date if start is None else start
        step = self.step if step is None else step

        if isinstance(stop, timedelta):
            stop = start + stop
        if start > stop and step > 0:
            step = -step

        listeners = kwargs.pop('listeners', [])

        for orb in self._iter(start, stop, step, **kwargs):
            for listen_orb in self.listen(orb, listeners):
                yield listen_orb
            yield orb


class AnalyticalPropagator(Propagator):
    """Base class for analytical propagators (RGP4, Eckstein-Heschler, etc.)
    """

    def _iter(self, start, stop, step, **kwargs):
        for date in Date.range(start, stop, step, kwargs.get('inclusive')):
            yield self.propagate(date)


class NumericalPropagator(Propagator):
    """Base class for numerical propagators (i.e. Cowell)
    """

    def propagate(self, date):

        for orb in self.iter(stop=date, inclusive=True):
            continue
        else:
            # Gives only the last iteration
            return orb
