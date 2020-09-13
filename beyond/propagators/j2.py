import numpy as np

from .base import AnalyticalPropagator
from ..constants import Earth
from ..dates import timedelta


class J2(AnalyticalPropagator):
    """Analytical propagator taking only the Earth-J2 effect into account"""

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

        mu = Earth.mu
        r = self.orbit.infos.r
        re = Earth.r
        n = self.orbit.infos.n
        a, e, i = self.orbit[:3]

        com = n * re ** 2 * Earth.J2 / (a ** 2 * (1 - e ** 2) ** 2)

        dΩ = -3 / 2 * com * np.cos(i)
        dω = 3 / 4 * com * (4 - 5 * np.sin(i) ** 2)
        dM = 3 / 4 * com * np.sqrt(1 - e ** 2) * (2 - 3 * np.sin(i) ** 2)

        delta = np.array([0.0, 0.0, 0.0, dΩ, dω, dM + n]) * delta_t

        new = self.orbit[:] + delta

        new[3:] = new[3:] % (2 * np.pi)
        new.date = date

        return new.copy(form="cartesian")
