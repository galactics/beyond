
from abc import ABCMeta, abstractmethod
from datetime import timedelta

from ..utils import Date


class Propagator(metaclass=ABCMeta):

    orbit = None

    @abstractmethod
    def _iter(self, star, stop, step, **kwargs):
        pass

    # @abstractmethod
    # def _bisect(self, start, stop):
    #     pass

    @abstractmethod
    def propagate(self, start):
        pass

    def iter(self, *args, **kwargs):
        """
        Examples:

            propag.iter(stop)
            propag.iter(stop, step)
            propag.iter(start, stop, step)
        """

        if not 1 <= len(args) <= 3:
            raise ValueError
        elif len(args) == 1:
            start = self.orbit.date
            stop, = args
            step = self.step
        elif len(args) == 2:
            start = self.orbit.date
            stop, step = args
        else:
            start, stop, step = args

        if isinstance(stop, timedelta):
            stop = start + stop
        if start > stop and step > 0:
            step = -step

        return self._iter(start, stop, step, **kwargs)


class AnalyticalPropagator(Propagator):

    def _iter(self, start, stop, step, **kwargs):
        for date in Date.range(start, stop, step, kwargs.get('inclusive')):
            yield self.propagate(date)


class NumericalPropagator(Propagator):

    def propagate(self, date):
        for orb in self.iter(self.orbit.date, date, self.step, inclusive=True):
            continue
        else:
            # Gives only the last iteration
            return orb
