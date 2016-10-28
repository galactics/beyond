"""This module defines the propagators availables
"""

from .sgp4 import Sgp4


def get_propagator(name):
    """Retrieve a named propagator

    Args:
        name (str): Name of the desired propagator
    Return:
        Propagator class
    """
    scope = locals().copy()
    scope.update(globals())
    try:
        return scope[name]
    except KeyError:
        raise TypeError("Unknown propagator '%s'" % name)
