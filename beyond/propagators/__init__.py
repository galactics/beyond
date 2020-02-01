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

    from .keplernum import KeplerNum
    from .none import NonePropagator
    from .sgp4 import Sgp4
    from .sgp4beta import Sgp4Beta

    scope = {
        "KeplerNum": KeplerNum,
        "NonePropagator": NonePropagator,
        "Sgp4": Sgp4,
        "Sgp4Beta": Sgp4Beta,
    }

    if name not in scope:
        raise UnknownPropagatorError(name)
    else:
        return scope[name]
