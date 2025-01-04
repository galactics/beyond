import logging
from collections import namedtuple

log = logging.getLogger(__name__)

SOI = namedtuple("SOI", "radius frame")


class _SoI:
    SOIS = {
        "Mercury": SOI(112408000, "Mercury"),
        "Venus": SOI(616270000, "Venus"),
        "Earth": SOI(924642000, "EME2000"),
        "Moon": SOI(66168000, "Moon"),
        "Mars": SOI(577223000, "Mars"),
        "Jupiter": SOI(48219667000, "Jupiter"),
        "Saturn": SOI(54800713000, "Saturn"),
        "Uranus": SOI(51839589000, "Uranus"),
        "Neptune": SOI(84758736000, "Neptune"),
    }

    def _soi(self, orb):
        """Evaluate the need for SOI transition, by comparing the radial distance
        between the considered body and the spacecraft

        If therer is no body in sight, default to central body.
        """

        for body in self.alt:
            soi = self.SOIS[body.name]
            sph = orb.copy(frame=soi.frame, form="spherical")
            if sph.r < soi.radius:
                active = body
                break
        else:
            active = self.central

        return active

    def _change_soi(self, body):
        """Modify the inner parameters of the KeplerNum propagator in order to place
        the spacecraft in the right Sphere of Influence
        """

        if body == self.central:
            self.bodies = [self.central]
            self.active = self.central.name
            self.frame = self.central.name
        else:
            soi = self.SOIS[body.name]
            self.bodies = [body]
            self.active = body.name
            self.frame = soi.frame

    def _iter(self, start=None, stop=None, step=None, **kwargs):
        orb = self.orbit
        soi = self._soi(orb)

        while orb.date < stop:
            current = soi

            # At each step of the computation, evaluate the need of SOI transition.
            # If needed, stop the iteration, change the parameters of the
            # propagation (frame, step, central body), then start it again from the
            # remaining dates point
            for orb in super()._iter(start=start, stop=stop, step=step, **kwargs):
                yield orb.copy(frame=self.out_frame)
                soi = self._soi(orb)
                if soi != current:
                    break

            start = orb.date

            # Here the SoI is changed, see self.orbit setter
            self.orbit = orb

            if start < stop:
                log.debug(f"SOI change {current} => {soi} at {orb.date}")
