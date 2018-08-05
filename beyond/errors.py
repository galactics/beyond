
class BeyondError(Exception):
    pass


class _Unknown(BeyondError):

    def __init__(self, name):
        self.name = name

    @property
    def type(self):
        return self.__class__.__name__.lstrip("Unknown").rstrip("Error").lower()

    def __str__(self):
        return "Unknown {} '{}'".format(self.type, self.name)


class UnknownBodyError(_Unknown):
    pass


class UnknownFrameError(_Unknown):
    pass


class UnknownFormError(_Unknown):
    pass


class UnknownPropagatorError(_Unknown):
    pass


class OrbitError(BeyondError):
    pass


class ConfigError(BeyondError):
    pass


class JplError(BeyondError):
    pass


class JplConfigError(JplError, ConfigError):
    pass


class DateError(BeyondError):
    pass


class UnknownScaleError(_Unknown):
    pass


class EopError(BeyondError):
    pass


class EopWarning(Warning):
    pass
