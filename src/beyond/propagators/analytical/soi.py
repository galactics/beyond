import logging

from .._soi import _SoI
from .kepler import Kepler

__all__ = ["SoIAnalytical"]

log = logging.getLogger(__name__)


class SoIAnalytical(_SoI, Kepler):
    """Kepler (analytical) propagator capable of switching between Sphere of Influence of
    different solar system bodies
    """

    def __init__(self, central, alt, *, frame=None):
        """
        Args:
            central (Body): Central body
            alt (list of Body): Objects to potentially use
            frame (str): Frame of the resulting extrapolation. If ``None``, the
                result will change frame depending on the sphere of influence
                it is in
        """

        self.central = central
        self.alt = alt if isinstance(alt, (list, tuple)) else [alt]
        self.out_frame = frame
        self.frame = frame
        self.active = central.name

    @property
    def orbit(self):
        return self._orbit if hasattr(self, "_orbit") else None

    @orbit.setter
    def orbit(self, orbit):
        soi = self._soi(orbit)
        self._change_soi(soi)
        self._orbit = orbit.copy(form="keplerian_mean", frame=self.frame)

    def copy(self):
        return self.__class__(
            self.central,
            self.alt,
            frame=self.out_frame,
        )
