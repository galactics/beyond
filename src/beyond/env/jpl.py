"""This module allow to extract data from .BSP files (provided by JPL)
and integrate them in the frames stack.

See the `NAIF website <https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/>`__
for more informations about the format and content of these files.

For the module to work properly, the .bsp files should be placed in the "env" folder
(the one already containing the 'finals'), and the `env.planest_source` configuration variable
should list the files to use, in a coma-separated string

The following configuration will provide access to the Solar System, Mars, Jupiter, Saturn and
their respective major satellites

.. code-block:: text

    [env]
    planets_source = de430.bsp, mar097.bsp, jup310.bsp, sat360xl.bsp

This module rely heavily on the jplephem library, which parse the binary .BSP format
"""

import numpy as np

from ..config import config
from ..orbits import Orbit
from ..utils.node import Node2
from ..propagators.base import AnalyticalPropagator

from jplephem.spk import SPK
from jplephem.names import target_names

__all__ = ['get_body', 'list_bodies']


class Target(Node2):
    """Class representing the relations between the differents segments
    of .bsp files

    It helps dynamically build the Frames objects
    """

    def __init__(self, name, index):
        super().__init__(name)
        self.index = index

    def __contains__(self, value):
        return value in [x.index for x in self.list]


class EarthPropagator(AnalyticalPropagator):

    FRAME = "EME2000"
    ORIGIN = [0] * 6

    @classmethod
    def vector(cls, date):
        orb = Orbit(
            date,
            cls.ORIGIN,
            form='cartesian',
            frame=cls.FRAME,
            propagator=cls()
        )
        return orb

    def propagate(self, date):
        return self.vector(date)


class GenericBspPropagator(AnalyticalPropagator):
    """Generic propagator
    """

    @classmethod
    def vector(cls, date):

        frame_name = cls.src.name
        if frame_name == 'Earth':
            frame_name = EarthPropagator.FRAME

        return Orbit(
            date,
            Bsp().get(cls.src.index, cls.dst.index, date),
            form="cartesian",
            frame=frame_name,
            propagator=cls()
        )

    def propagate(self, date):
        return self.vector(date)


class Bsp:
    """Singleton for reading .bsp files from JPL (DE405, DE430, DE431, etc.)

    with caching mechanism
    """

    _instance = None

    def __new__(cls, *args, **kwargs):

        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.open()

        return cls._instance

    def open(self):
        """Open the files
        """
        segments = []

        # Extraction of segments from each .bsp file
        for filename in config['env']['planets_source'].split(','):
            filepath = config['folder'] / 'env' / filename.strip()
            segments.extend(SPK.open(filepath).segments)

        # list of available segments
        self.segments = dict(((s.center, s.target), s) for s in segments)

        # This variable will contain the Target of reference from which
        # all relations between frames are linked
        targets = {}

        for center_id, target_id in self.segments.keys():
            try:
                center_name = target_names[center_id].title().replace(" ", "")
                target_name = target_names[target_id].title().replace(" ", "")
            except KeyError:
                # In case of an Unknown Object, from a jplephem library standpoint,
                # we discard it.
                continue

            # Retrieval of the Target object representing the center if it exists
            # or creation of said object if it doesn't.
            center = targets.setdefault(center_id, Target(center_name, center_id))
            target = targets.setdefault(target_id, Target(target_name, target_id))

            # Link between the Target objects (see Node2)
            center + target

        # We take the Earth target and make it the top of the structure.
        # That way, it is easy to link it to the already declared earth-centered reference frames
        # from the `frames.frame` module.
        self.top = targets[399]

    def get(self, center_id, target_id, date):
        """Retrieve the position and velocity of a target with respect to a center

        Args:
            center_id (int):
            target_id (int):
            date (Date):
        Return:
            numpy.array: lenght-6 array position and velocity (in m and m/s) of the
                target, with respect to the center
        """

        try:
            pos, vel = self.segments[center_id, target_id].compute_and_differentiate(date.jd)
            sign = 1
        except KeyError:
            # Some times we want to get the reversed vector of what is available
            pos, vel = self.segments[target_id, center_id].compute_and_differentiate(date.jd)
            sign = -1

        # In some cases, the pos vector contains both position and velocity
        pv = np.array(pos) if len(pos) == 6 else np.concatenate((pos, vel))

        return sign * pv * 1000


# Cache containing all the propagators used
_propagator_cache = {}


def get_body(name, date):
    """Retriev the orbit of a solar system object

    Args:
        name (str): The name of the body desired. For exact nomenclature, see
            :py:func:`available_planets`
        date (Date): Date at which the state vector will be extracted
    Return:
        Orbit: Orbit of the desired object, in the reference frame in which it is declared in
            the .bsp file
    """

    # Special case for earth
    if name == 'Earth':
        return Orbit(
            date,
            EarthPropagator.ORIGIN,
            form="cartesian",
            frame=EarthPropagator.FRAME,
            propagator=EarthPropagator()
        )

    # On-demand Propagator and Frame generation
    for a, b in Bsp().top.steps(name):
        if b.name not in _propagator_cache:

            # Creation of the specific propagator class
            propagator = type(
                "%sBspPropagator" % b.name,
                (GenericBspPropagator,),
                {'src': a, 'dst': b}
            )

            # Register the Orbit as a frame
            propagator.vector(date).register_as_frame(b.name)
            _propagator_cache[b.name] = propagator

    return _propagator_cache[name].vector(date)


def list_bodies():
    """List bodies provided by the .bsp files

    Yield:
        Target
    """
    for x in Bsp().top.list[:-1]:
        yield x
