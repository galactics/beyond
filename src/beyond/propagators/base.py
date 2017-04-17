
from abc import ABCMeta, abstractmethod

from ..utils import Date


class Propagator(metaclass=ABCMeta):

    @abstractmethod
    def _single(self, date):
        pass

    @abstractmethod
    def _generator(self, star, stop, step):
        pass

    def propagate(self, start, stop=None, step=None):

        if stop is None and step is None:
            return self._single(start)
        elif stop is None or step is None:
            raise TypeError("stop and step should be defined")
        else:
            return self._generator(start, stop, step)


class AnalyticalPropagator(Propagator):

    def _generator(self, start, stop, step):
        for date in Date.range(start, stop, step):
            yield self._single(date)


class NumericalPropagator(Propagator):

    def _single(self, date):
        for orb in self._generator(self.orb.date, date, self.step):
            continue
        # Gives only the last iteration
        return orb
