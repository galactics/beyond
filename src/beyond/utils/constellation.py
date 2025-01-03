"""Utilities to compute the parameters of a constellation.

At the moment, only the Walker Star and Walker Delta are available
(see `wikipedia <https://en.wikipedia.org/wiki/Satellite_constellation#Walker_Constellation>`__)
"""

import numpy as np


class WalkerStar:
    """Definition of the WalkerStar constellation

    Example: Iridium is a Walker Star 66/6/2 constellation
    so to generate this, one has to call ``WalkerStar(66, 6, 2)``
    """

    def __init__(self, total, planes, spacing, raan0=0):
        """
        Args:
            total (int) : Total number of satellites
            planes (int) : Number of planes
            spacing (int) : relative spacing between satellites of adjacent planes
            raan0 (float) : RAAN of the first plane (in radians)

        This call order is compliant with Walker notation total/planes/spacing.
        """

        self.total = total
        self.planes = planes
        self.spacing = spacing
        self.raan0 = raan0

    def __repr__(self):  # pragma: cover
        return f"<{self.__class__.__name__} {self.total}/{self.planes}/{self.spacing}>"

    @property
    def per_plane(self):
        """Number of satellites per orbital plane"""
        return self.total // self.planes

    def raan(self, i_plane):
        """
        Args:
            i_plane (int) : index of the plane
        Return:
            float : Right Ascension of Ascending Node in radians
        """
        return np.pi / self.planes * i_plane + self.raan0

    def nu(self, i_plane, i_sat):
        """
        Args:
            i_plane (int) : index of the plane
            i_sat (int) : index of the satellite
        Return:
            float : True anomaly in radians
        """
        return (
            2 * np.pi / self.per_plane * i_sat
            + self.spacing * 2 * (self.raan(i_plane) - self.raan0) / self.per_plane
        )

    def iter_raan(self):
        for i in range(self.planes):
            yield self.raan(i)

    def iter_nu(self, plane):
        for i in range(self.per_plane):
            yield self.nu(plane, i)

    def iter_fleet(self):
        for i, raan in enumerate(self.iter_raan()):
            for nu in self.iter_nu(i):
                yield raan, nu


class WalkerDelta(WalkerStar):
    """Definition of the Walkek Delta constellation

    Example: Galileo is a Walker Delta 24/3/1 constellation
    so to generate this, one has to call ``WalkerDelta(24, 3, 1)``
    """

    def raan(self, i_plane):
        """
        Args:
            i_plane (int) : index of the plane
        Return:
            float : Right Ascension of Ascending Node in radians
        """
        return 2 * np.pi / self.planes * i_plane + self.raan0

    def nu(self, i_plane, i_sat):
        """
        Args:
            i_plane (int) : index of the plane
            i_sat (int) : index of the satellite
        Return:
            float : True anomaly in radians
        """
        return (
            2 * np.pi / self.per_plane * i_sat
            + self.spacing * (self.raan(i_plane) - self.raan0) / self.per_plane
        )
