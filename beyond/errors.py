"""Common errors declarations
"""


class BeyondError(Exception):
    """Generic error"""
    pass


class _Unknown(BeyondError):
    """Generic error for unknown argument
    """

    def __init__(self, name):
        self.name = name

    @property
    def type(self):
        return self.__class__.__name__.lstrip("Unknown").rstrip("Error").lower()

    def __str__(self):
        return "Unknown {} '{}'".format(self.type, self.name)


class UnknownBodyError(_Unknown):
    """Unknown Body (Earth, Moon, Sun, etc.)
    """
    pass


class UnknownFrameError(_Unknown):
    """Unknown frame (ITRF, EME2000, etc.)
    """
    pass


class UnknownFormError(_Unknown):
    """Unknown form (keplerian, cartesian)
    """
    pass


class UnknownPropagatorError(_Unknown):
    """Unknown propagator (sgp4, kepler)
    """
    pass


class OrbitError(BeyondError):
    pass


class ConfigError(BeyondError):
    pass


class JplError(BeyondError):
    """Generic error for JPL data handling

    allows to fallback to other data
    """
    pass


class JplConfigError(JplError, ConfigError):
    pass


class DateError(BeyondError):
    pass


class UnknownScaleError(_Unknown):
    """Unknown scale (UTC, TAI, UT1, GPS, etc.)
    """
    pass


class EopError(BeyondError):
    """Eart Orientation Parameters error (lack of data)
    """
    pass


class EopWarning(Warning):
    pass
