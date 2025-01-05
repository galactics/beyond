"""This module defines the propagators availables
"""

from ..errors import UnknownPropagatorError
from .base import Propagator as Propagator


def get_propagator(name):
    """Retrieve a named propagator

    Args:
        name (str): Name of the desired propagator
    Return:
        Propagator class
    """
    from .analytical import J2, Kepler, NonePropagator, Sgp4, Sgp4Beta, EcksteinHechler
    from .numerical import KeplerNum
    from .rpo import ClohessyWiltshire, YamanakaAnkersen

    scope = {
        "J2": J2,
        "Kepler": Kepler,
        "KeplerNum": KeplerNum,
        "NonePropagator": NonePropagator,
        "Sgp4": Sgp4,
        "Sgp4Beta": Sgp4Beta,
        "EcksteinHechler": EcksteinHechler,
        "ClohessyWiltshire": ClohessyWiltshire,
        "YamanakaAnkersen": YamanakaAnkersen,
    }

    if name not in scope:
        raise UnknownPropagatorError(name)
    else:
        return scope[name]
