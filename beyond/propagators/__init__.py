"""This module defines the propagators availables
"""

from ..errors import UnknownPropagatorError


def get_propagator(name):
    """Retrieve a named propagator

    Args:
        name (str): Name of the desired propagator
    Return:
        Propagator class
    """

    from .sgp4 import Sgp4
    from .sgp4beta import Sgp4Beta
    from .kepler import Kepler
    from .none import NonePropagator

    scope = locals().copy()
    scope.update(globals())

    if name is None:
        return NonePropagator
    elif name not in scope:
        raise UnknownPropagatorError(name)
    else:
        return scope[name]
