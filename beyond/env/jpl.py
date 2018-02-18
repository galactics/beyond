"""This module allow to extract data from .BSP files (provided by JPL)
and integrate them in the frames stack.

See the `NAIF website <https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/>`__
for more informations about the format and content of these files.

For the module to work properly, the .bsp files should be sourced via the `env.jpl.bsp`
configuration variable.

The following configuration will provide access to the Solar System, Mars, Jupiter, Saturn and
their respective major satellites

.. code-block:: python

    from beyond.config import config

    config.update({
        "env": {
            "jpl": [
                "/path/to/de430.bsp",
                "/path/to/mar097.bsp",
                "/path/to/jup310.bsp",
                "/path/to/sat360xl.bsp"
            ]
        }
    })

This module rely heavily on the jplephem library, which parse the binary .BSP format
"""

import numpy as np

from ..config import config
from ..orbits import Orbit
from ..utils.node import Node
from ..propagators.base import AnalyticalPropagator
from ..dates import Date

from jplephem.spk import SPK
from jplephem.names import target_names

__all__ = ['get_body', 'list_bodies']


class Target(Node):
    """Class representing the relations between the differents segments
    of .bsp files

    It helps dynamically build the Frames objects
    """

    def __init__(self, name, index):
        super().__init__(name)
        self.index = index


class GenericBspPropagator(AnalyticalPropagator):
    """Generic propagator
    """

    BASE_FRAME = "EME2000"

    @classmethod
    def propagate(cls, date):

        frame_name = cls.src.name
        if frame_name == 'Earth':
            frame_name = cls.BASE_FRAME

        date = date.change_scale("TDB")

        return Orbit(
            date,
            Bsp().get(cls.src, cls.dst, date),
            form="cartesian",
            frame=frame_name,
            propagator=cls()
        )


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
        for filepath in config['env']['jpl']:
            segments.extend(SPK.open(str(filepath)).segments)

        # list of available segments
        self.segments = dict(((s.center, s.target), s) for s in segments)

        # This variable will contain the Target of reference from which
        # all relations between frames are linked
        targets = {}

        for center_id, target_id in self.segments.keys():

            center_name = target_names.get(center_id, 'Unknown').title().replace(' ', '')
            target_name = target_names.get(target_id, 'Unknown').title().replace(' ', '')

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

    def get(self, center, target, date):
        """Retrieve the position and velocity of a target with respect to a center

        Args:
            center (Target):
            target (Target):
            date (Date):
        Return:
            numpy.array: lenght-6 array position and velocity (in m and m/s) of the
                target, with respect to the center
        """

        if (center.index, target.index) in self.segments:
            pos, vel = self.segments[center.index, target.index].compute_and_differentiate(date.jd)
            sign = 1
        else:
            # When we wish to get a segment that is not available in the files (such as
            # EarthBarycenter with respect to the Moon, for example), we take the segment
            # representing the inverse vector if available and reverse it
            pos, vel = self.segments[target.index, center.index].compute_and_differentiate(date.jd)
            sign = -1

        # In some cases, the pos vector contains both position and velocity
        pv = np.array(pos) if len(pos) == 6 else np.concatenate((pos, -vel))

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
            propagator.propagate(date).as_frame(b.name)
            _propagator_cache[b.name] = propagator

    return _propagator_cache[name].propagate(date)


def list_bodies():
    """List bodies provided by the .bsp files

    Yield:
        Target
    """
    for x in Bsp().top.list[:-1]:
        yield x


def create_frames(until=None):
    """Create all frames availables in the JPL files
    """

    now = Date.now()

    if until:
        get_body(until, now)
    else:
        for body in list_bodies():
            get_body(body.name, now)
