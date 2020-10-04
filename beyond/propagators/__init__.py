"""This module defines the propagators availables
"""

from ..errors import UnknownPropagatorError
from .base import Propagator


def get_propagator(name):
    """Retrieve a named propagator

    Args:
        name (str): Name of the desired propagator
    Return:
        Propagator class
    """

    from .j2 import J2
    from .kepler import Kepler
    from .keplernum import KeplerNum
    from .none import NonePropagator
    from .sgp4 import Sgp4
    from .sgp4beta import Sgp4Beta
    from .eh import EcksteinHechler

    scope = {
        "J2": J2,
        "Kepler": Kepler,
        "KeplerNum": KeplerNum,
        "NonePropagator": NonePropagator,
        "Sgp4": Sgp4,
        "Sgp4Beta": Sgp4Beta,
        "EcksteinHechler": EcksteinHechler,
    }

    if name not in scope:
        raise UnknownPropagatorError(name)
    else:
        return scope[name]
