from .base import AnalyticalPropagator


class NonePropagator(AnalyticalPropagator):
    """The NonePropagator returns the same orbit at every step

    This is useful when dealing with the object at the center
    of a reference frame.
    """

    def propagate(self, date):
        orb = self.orbit.copy()
        orb.date = date
        return orb
