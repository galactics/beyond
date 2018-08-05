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

    scope = locals().copy()
    scope.update(globals())

    if name not in scope:
        raise UnknownPropagatorError(name)

    return scope[name]
