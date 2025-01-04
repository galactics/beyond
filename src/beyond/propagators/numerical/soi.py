import logging

from .._soi import _SoI
from .keplernum import KeplerNum

__all__ = ["SoINumerical"]

log = logging.getLogger(__name__)


class SoINumerical(_SoI, KeplerNum):
    """KeplerNum propagator capable of switching between the Sphere of Influence of
    different solar system bodies
    """

    def __init__(
        self, central_step, alt_step, central, alt, *, method=KeplerNum.RK4, frame=None
    ):
        """
        Args:
            central_step (timedelta): Step to use in computation when only the
                central body is taken into account
            alt_step (timedelta): Step to use in computations under the
                influence of an alternate body
            central (Body): Central body
            alt (list of Body): Objects to potentially use
            method (str): Method of extrapolation (see :py:class:`KeplerNum`)
            frame (str): Frame of the resulting extrapolation. If ``None``, the
                result will change frame depending on the sphere of influence
                it is in
        """

        self.alt_step = alt_step
        self.central_step = central_step
        self.central = central
        self.alt = alt if isinstance(alt, (list, tuple)) else [alt]
        self.method = method
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
        self._orbit = orbit.copy(form="cartesian", frame=self.frame)

    def copy(self):
        return self.__class__(
            self.central_step,
            self.alt_step,
            self.central,
            self.alt,
            method=self.method,
            frame=self.out_frame,
        )

    def _change_soi(self, body):
        """Modify the inner parameters of the KeplerNum propagator in order to place
        the spacecraft in the right Sphere of Influence
        """

        if body == self.central:
            self.step = self.central_step
        else:
            self.step = self.alt_step

        super()._change_soi(body)

    def _iter(self, start=None, stop=None, step=None, **kwargs):
        """This method totaly override the super()._iter() method because
        it is not possible to modify the step on the fly with _SoI implementation.

        Talk about duplication of code...
        """

        orb = self.orbit
        soi = self._soi(orb)

        while orb.date < stop:
            current = soi

            # At each step of the computation, evaluate the need of SOI transition.
            # If needed, stop the iteration, change the parameters of the
            # propagation (frame, step, central body), then start it again from the
            # remaining dates point
            for orb in super(_SoI, self)._iter(
                start=start, stop=stop, step=self.step, **kwargs
            ):
                yield orb.copy(frame=self.out_frame)
                soi = self._soi(orb)
                if soi != current:
                    break

            start = orb.date

            # Here the SoI is changed, see self.orbit setter
            self.orbit = orb

            if start < stop:
                log.debug(f"SOI change {current} => {soi} at {orb.date}")
