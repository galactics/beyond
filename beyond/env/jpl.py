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

In addition to .BSP files, you can provide files in the
`PCK text format <https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/>`__ (generally with a
``.tpc`` extension), which contain informations about masses and dimensions of most of the solar
system bodies.

These files allows to convert to keplerian elements with correct physical constants
(mainly µ).

.. code-block:: python

    config.update({
        "env": {
            "jpl": [
                "/path/to/de430.bsp",
                "/path/to/mar097.bsp",
                "/path/to/jup310.bsp",
                "/path/to/sat360xl.bsp",
                "/path/to/pck00010.tpc",
                "/path/to/gm_de431.tpc"
            ]
        }
    })

Examples of both .bsp and .tcp files are available in the ``tests/data/jpl`` folder.

To display the content of a .bsp file you can use::

    $ python -m beyond.env.jpl <file>...
"""

import numpy as np
from pathlib import Path

from ..config import config
from ..errors import UnknownBodyError, JplConfigError, JplError
from ..orbits import Orbit
from ..utils.node import Node
from ..propagators.base import AnalyticalPropagator
from ..dates import Date
from ..constants import Body, G

from jplephem.spk import SPK, S_PER_DAY
from jplephem.names import target_names

__all__ = ['get_body', 'list_bodies', 'create_frames']


class Target(Node):
    """Class representing the relations between the differents segments
    of .bsp files

    It helps dynamically build the Frames objects
    """

    def __init__(self, name, index):
        super().__init__(name.title().replace(' ', ''))
        self.full_name = name
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

        files = config.get('env', 'jpl', fallback=[])

        if not files:
            raise JplConfigError("No JPL file defined")

        # Extraction of segments from each .bsp file
        for filepath in files:

            filepath = Path(filepath)

            if filepath.suffix.lower() != ".bsp":
                continue

            segments.extend(SPK.open(str(filepath)).segments)

        # list of available segments
        self.segments = dict(((s.center, s.target), s) for s in segments)

        # This variable will contain the Target of reference from which
        # all relations between frames are linked
        targets = {}

        for center_id, target_id in self.segments.keys():

            center_name = target_names.get(center_id, 'Unknown')
            target_name = target_names.get(target_id, 'Unknown')

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
        if len(pos) == 3:
            # The velocity is given in km/days, so we convert to km/s
            # see: https://github.com/brandon-rhodes/python-jplephem/issues/19 for clarifications
            pv = np.concatenate((pos, vel / S_PER_DAY))
        elif len(pos) == 6:
            pv = np.array(pos)
        else:
            raise JplError("Unknown state vector format")

        return sign * pv * 1000


class Pck(dict):
    """Parser of PCK file containing orientation and shape models for solar system bodies
    """

    def __new__(cls, *args, **kwargs):

        # Caching mechanism
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.parse()

        return cls._instance

    @classmethod
    def parse_float(cls, txt):
        if "d" in txt:
            # Exponent
            txt = txt.replace("d", "e")

        return float(txt)

    def parse(self):

        self.clear()

        # Parsing of mutliple files provided in the configuration variable
        for filepath in config['env']['jpl']:

            filepath = Path(filepath)

            if filepath.suffix.lower() != ".tpc":
                continue

            with filepath.open() as fp:
                lines = fp.read().splitlines()

            datablock = False

            # Checking for header
            if lines[0].strip() != "KPL/PCK":
                raise JplError("Unknown file format")

            try:
                for i, line in enumerate(lines):

                    # Seek the begining of a data block
                    if line.strip() == "\\begindata":
                        datablock = True
                        continue

                    # End of a datablock
                    if line.strip() == "\\begintext":
                        datablock = False
                        continue

                    # Variable extraction
                    if datablock and line.strip().lower().startswith('body'):

                        # retrieval of body ID, parameter name and value
                        line = line.strip().lower().lstrip('body')
                        body_id, _, param = line.partition('_')
                        key, _, value = param.partition("=")

                        # If possible, retrieval of the name of the body
                        # if not, use the ID as name
                        name = target_names.get(int(body_id), body_id).title().strip()

                        # If already existing, check out the dictionnary describing the body
                        # caracteristics
                        body_dict = self.setdefault(name, {})

                        # Extraction of interesting data
                        value = value.strip()

                        # List of value scattered on multiple lines
                        if not value.endswith(")"):
                            for next_line in lines[i + 1:]:
                                value += " " + next_line.strip()
                                if next_line.strip().endswith(")"):
                                    break

                        value = [self.parse_float(v) for v in value[1:-2].split()]

                        body_dict[key.upper().strip()] = value
            except Exception as e:
                raise JplError("Parsing error on file '{}'".format(filepath)) from e

    def __getitem__(self, name):
        """Retrieve infos for a given body, if available.

        If not, use default values of 0
        """

        if name == "Solar System Barycenter":
            name = "Sun"

        try:
            obj = super().__getitem__(name)
        except KeyError:
            obj = {}

        # Shape
        if "RADII" in obj:
            radii = obj['RADII'][0] * 1000.
            flattening = 1 - (obj['RADII'][2] / obj['RADII'][0])
        else:
            radii = 0
            flattening = 0

        # mass
        if 'GM' in obj:
            mass = obj['GM'][0] * 1e9 / G
        else:
            mass = 0

        return Body(
            name=name.title(),
            mass=mass,
            equatorial_radius=radii,
            flattening=flattening
        )


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

    if name not in [x.name for x in Bsp().top.list]:
        raise UnknownBodyError(name)

    for a, b in Bsp().top.steps(name):
        if b.name not in _propagator_cache:

            # Creation of the specific propagator class
            propagator = type(
                "%sBspPropagator" % b.name,
                (GenericBspPropagator,),
                {'src': a, 'dst': b}
            )

            # Retrieve informations for the central body. If unavailable, create a virtual body with
            # dummy values
            center = Pck()[b.full_name.title()]

            # Register the Orbit as a frame
            propagator.propagate(date).as_frame(b.name, center=center)
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
    """Create frames availables in the JPL files

    Args:
        until (str): Name of the body you want to create the frame of, and all frames in between.
                     If ``None`` all the frames available in the .bsp files will be created

    Example:

    .. code-block:: python

        # All frames between Earth and Mars are created (Earth, EarthBarycenter,
        # SolarSystemBarycenter, MarsBarycenter and Mars)
        create_frames(until='Mars')

        # All frames between Earth and Phobos are created (Earth, EarthBarycenter,
        # SolarSystemBarycenter, MarsBarycenter and Phobos)
        create_frames(until='Phobos')

        # All frames available in the .bsp files are created
        create_frames()

    """

    now = Date.now()

    if until:
        get_body(until, now)
    else:
        for body in list_bodies():
            get_body(body.name, now)


if __name__ == '__main__':

    import sys

    config.update({
        'eop': {
            'missing_policy': "pass"
        }
    })

    for file in sys.argv[1:]:
        print(file)
        print("*" * len(file))
        for segment in SPK.open(file).segments:

            start = Date(segment.start_jd - Date.JD_MJD)
            end = Date(segment.end_jd - Date.JD_MJD)

            center = target_names[segment.center]
            target = target_names[segment.target]
            print("from {start:{fmt}} to {end:{fmt}} : {center} -> {target}".format(
                start=start, end=end, center=center, target=target,
                fmt="%Y-%m-%d"
            ))
        print()
