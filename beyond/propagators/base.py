
from abc import ABCMeta, abstractmethod
from datetime import timedelta
from collections.abc import Iterable

from ..dates import Date
from ..orbits.listeners import Speaker


class Propagator(Speaker, metaclass=ABCMeta):
    """Base class for propagators
    """

    orbit = None

    @abstractmethod
    def _iter(self, **kwargs):
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

    def iter(self, **kwargs):
        """Compute a range of orbits between two dates

        Keyword Arguments:
            start (Date)
            stop (Date or timedelta)
            step (timedelta)
        Yield:
            :py:class:`~beyond.orbits.orbit.Orbit`:

        Examples:

        .. code-block:: python

            propag.iter(stop=stop)
            propag.iter(stop=stop, step=step)
            propag.iter(start=start, stop=stop, step=step)
        """

        start = kwargs.setdefault('start', self.orbit.date)
        stop = kwargs.get('stop')
        step = kwargs.setdefault('step', getattr(self, 'step', None))

        if 'stop' is None:
            raise ValueError("The end of the propagation should be defined")

        start = self.orbit.date if start is None else start
        step = self.step if step is None else step

        if isinstance(kwargs['stop'], timedelta):
            kwargs['stop'] = start + kwargs['stop']
        if start > kwargs['stop'] and step.total_seconds() > 0:
            kwargs['step'] = -step

        listeners = kwargs.pop('listeners', [])

        for orb in self._iter(**kwargs):
            for listen_orb in self.listen(orb, listeners):
                yield listen_orb
            yield orb


class AnalyticalPropagator(Propagator):
    """Base class for analytical propagators (SGP4, Eckstein-Heschler, etc.)
    """

    def _iter(self, **kwargs):

        start = kwargs.get('start')
        stop = kwargs.get('stop')
        step = kwargs.get('step')

        for date in Date.range(start, stop, step, inclusive=True):
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
