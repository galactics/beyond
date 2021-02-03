import numpy as np

from .base import AnalyticalPropagator
from ..constants import Earth
from ..dates import timedelta


class Kepler(AnalyticalPropagator):
    """Analytical propagator only taking the evolution of the Mean anomaly"""

    @property
    def orbit(self):
        return self._orbit if hasattr(self, "_orbit") else None

    @orbit.setter
    def orbit(self, orbit):
        self._orbit = orbit.copy(form="keplerian_mean")

    def propagate(self, date):

        if type(date) is timedelta:  # pragma: no cover
            date = self.orbit.date + date

        delta_t = (date - self.orbit.date).total_seconds()

        n = self.orbit.infos.n

        delta = n * delta_t

        new = self.orbit.copy()
        new.date = date
        new[5] = self.orbit[5] + delta

        return new.copy(form="cartesian")
