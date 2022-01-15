"""This module allow to extract data from .bsp files (provided by JPL)
and integrate them in the frames stack.

See the `NAIF website <https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/>`__
for more informations about the format and content of these files.

For the module to work properly, the .bsp files should be sourced via the `env.jpl.files`
configuration variable.

The following configuration will provide access to the Solar System, Mars, Jupiter, Saturn and
their respective major satellites

.. code-block:: python

    from beyond.config import config

    config.set("env", "jpl", "files", [
        "/path/to/de430.bsp",
        "/path/to/mar097.bsp",
        "/path/to/jup310.bsp",
        "/path/to/sat360xl.bsp"
    ])

This module rely heavily on the jplephem library, which parse the binary .bsp format

In order to use a reference frame of a celestial object, one has to create it first.
For example, to compute the Orbit of the ISS with respect to the reference frame of
Mars (because, why not !)

.. code-block:: python

    from beyond.env.jpl import create_frames

    iss.frame = "Mars"  # would fail
    
    create_frames()
    iss.frame = "Mars"  # would succeed

Alternatively, it is possible to set the ``env.jpl.dynamic_frames`` configuration variable
to ``True`` to force the frame creation when needed. By default this is disabled.

In addition to .bsp files, you can provide files in the
`PCK text format <https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/>`__ (generally with a
``.tpc`` extension), which contain informations about masses and dimensions of most of the solar
system bodies.

These files allows to convert to keplerian elements with correct physical constants
(mainly µ).

.. code-block:: python

    config.set("env", "jpl", "files", [
        "/path/to/de430.bsp",
        "/path/to/mar097.bsp",
        "/path/to/jup310.bsp",
        "/path/to/sat360xl.bsp",
        "/path/to/pck00010.tpc",
        "/path/to/gm_de431.tpc"
    ])

Examples of both .bsp and .tcp files are available in the ``tests/data/jpl`` folder.

To display the content of a .bsp file you can use::

    $ python -m beyond.env.jpl <file>...
"""

import logging
import numpy as np
from pathlib import Path

from ..config import config
from ..errors import UnknownBodyError, JplConfigError, JplError
from ..orbits import Orbit
from ..propagators.base import AnalyticalPropagator
from ..constants import Body, G
from ..frames import center, frames

from jplephem.spk import SPK, S_PER_DAY
from jplephem.names import target_names

__all__ = ["get_orbit", "list_bodies", "create_frames"]
log = logging.getLogger(__name__)


BASE_FRAME = frames.EME2000


class Bsp:
    """Singleton for reading .bsp files from JPL (DE405, DE430, DE431, etc.)

    with caching mechanism
    """

    _instance = None

    def __new__(cls, *args, **kwargs):

        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)

        return cls._instance

    @property
    def spk(self):
        if not hasattr(self, "_spk"):
            self._spk = []

            files = config.get("env", "jpl", "files", fallback=[])

            if not files:
                raise JplConfigError("No JPL file defined")

            # Extraction of segments from each .bsp file
            for filepath in files:

                filepath = Path(filepath)

                if filepath.suffix.lower() != ".bsp":
                    continue

                if not filepath.exists():
                    log.warning(f"File not found : {filepath}")
                    continue

                self._spk.append(SPK.open(str(filepath)))

        return self._spk

    @property
    def segments(self):
        segments = []
        for s in self.spk:
            segments.extend(s.segments)
        return segments

    @property
    def pairs(self):
        pairs = {}
        for s in self.spk:
            pairs.update(s.pairs)
        return pairs


class Pck(dict):
    """Parser of PCK file containing orientation and shape models for solar system bodies"""

    def __new__(cls, *args, **kwargs):

        # Caching mechanism
        if not hasattr(cls, "_instance"):
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

        files = config.get("env", "jpl", "files", fallback=[])

        if not files:
            raise JplConfigError("No JPL file defined")

        # Parsing of multiple files provided in the configuration variable
        for filepath in files:

            filepath = Path(filepath)

            if filepath.suffix.lower() != ".tpc":
                continue

            if not filepath.exists():
                log.warning(f"File not found : {filepath}")
                continue

            with filepath.open(encoding="ascii") as fp:
                lines = fp.read().splitlines()

            datablock = False

            # Checking for header
            if lines[0].strip() != "KPL/PCK":
                raise JplError("Unknown file format")

            try:
                for i, line in enumerate(lines):

                    # Seek the beginning of a data block
                    if line.strip() == "\\begindata":
                        datablock = True
                        continue

                    # End of a datablock
                    if line.strip() == "\\begintext":
                        datablock = False
                        continue

                    # Variable extraction
                    if datablock and line.strip().lower().startswith("body"):

                        # retrieval of body ID, parameter name and value
                        line = line.strip().lower().lstrip("body")
                        body_id, _, param = line.partition("_")
                        key, _, value = param.partition("=")

                        # If possible, retrieval of the name of the body
                        # if not, use the ID as name
                        name = target_names.get(int(body_id), body_id).title().strip()

                        # If already existing, check out the dictionary describing the body
                        # characteristics
                        body_dict = self.setdefault(name, {})

                        # Extraction of interesting data
                        value = value.strip()

                        # List of value scattered on multiple lines
                        if not value.endswith(")"):
                            for next_line in lines[i + 1 :]:
                                value += " " + next_line.strip()
                                if next_line.strip().endswith(")"):
                                    break

                        value = [self.parse_float(v) for v in value[1:-2].split()]

                        body_dict[key.upper().strip()] = value
            except Exception as e:
                raise JplError(f"Parsing error on file '{filepath}'") from e

    def __getitem__(self, name):
        """Retrieve infos for a given body, if available.

        If not, use default values of 0
        """

        if name == "SOLAR SYSTEM BARYCENTER":
            name = "SUN"

        try:
            obj = super().__getitem__(name.title())
        except KeyError as e:
            if name in target_names.values():
                obj = {}
            else:
                raise UnknownBodyError(name)

        kwargs = {
            "name": name.title(),
            "equatorial_radius": 0,
            "mass": 0,
        }

        # Shape
        if "RADII" in obj:
            kwargs["equatorial_radius"] = obj["RADII"][0] * 1000.0
            kwargs["flattening"] = 1 - (obj["RADII"][2] / obj["RADII"][0])

        # mass
        if "GM" in obj:
            kwargs["mass"] = obj["GM"][0] * 1e9 / G

        return Body(**kwargs)


class JplPropagator(AnalyticalPropagator):
    """Propagator"""

    def __init__(self, obj, frame):
        self.name = obj.name
        self.obj = obj
        self.frame = frame

    def __repr__(self):
        return f"<{self.__class__.__name__} '{self.name}' at {hex(id(self))}>"

    def copy(self):
        return self.__class__(self.obj, self.frame)

    def propagate(self, date):
        """Compute center position

        Args:
            date (Date):
        Return:
            numpy.array: length-6 array position and velocity (in m and m/s) of the
                target, with respect to the center
        """

        date = date.change_scale("TDB")

        if (self.obj.index, self.frame.center.index) in Bsp().pairs.keys():
            segment = Bsp().pairs[self.obj.index, self.frame.center.index]
            sign = -1
        else:
            # When we wish to get a segment that is not available in the files (such as
            # EarthBarycenter with respect to the Moon, for example), we take the segment
            # representing the inverse vector if available and reverse it
            segment = Bsp().pairs[self.frame.center.index, self.obj.index]
            sign = 1

        pos, vel = segment.compute_and_differentiate(date.jd)

        # In some cases, the pos vector contains both position and velocity
        if len(pos) == 3:
            # The velocity is given in km/days, so we convert to km/s
            # see: https://github.com/brandon-rhodes/python-jplephem/issues/19 for clarifications
            pv = np.concatenate((pos, vel / S_PER_DAY))
        elif len(pos) == 6:
            # TODO : Isn't the velocity also in km/days here, as for the previous case ?
            pv = np.array(pos)
        else:
            raise JplError("Unknown state vector format")

        return Orbit(sign * pv * 1000, date, "cartesian", self.frame, self)


class JplCenter(center.Center):
    """Class representing the relations between the different segments
    of .bsp files
    """

    def __init__(self, name, index, body=None):
        short_name = name.title().replace(" ", "")
        super().__init__(short_name, body=body)
        self.full_name = name
        self.index = index

    def add_link(self, linked, propagator):
        super().add_link(linked, BASE_FRAME.orientation, propagator)
        self.link = linked


class JplFrame(frames.Frame):
    """Class for Frames from .bsp files"""

    def __init__(self, center):
        super().__init__(center.name, BASE_FRAME.orientation, center)


# Cache containing all the propagators used
_frame_cache = {}
_propagator_cache = {}


def create_frames():
    """Create all frames available from the .bsp files"""

    # This variable will contain the Target of reference from which
    # all relations between frames are linked
    centers = {}

    for center_id, target_id in Bsp().pairs:

        center_name = target_names.get(center_id, "Unknown")
        target_name = target_names.get(target_id, "Unknown")

        if center_id not in centers:
            center_body = Pck()[center_name]
            center = centers[center_id] = JplCenter(
                center_name, center_id, body=center_body
            )
        else:
            center = centers[center_id]

        if target_id not in centers:
            target_body = Pck()[target_name]
            target = centers[target_id] = JplCenter(
                target_name, target_id, body=target_body
            )
        else:
            target = centers[target_id]

        if center.name not in _frame_cache:
            _frame_cache[center.name] = JplFrame(center)
        if target.name not in _frame_cache:
            _frame_cache[target.name] = JplFrame(target)

        if target.name not in _propagator_cache:
            _propagator_cache[target.name] = JplPropagator(
                target, _frame_cache[center.name]
            )

        # Link between the JplCenter objects (see beyond.frames.center)
        target.add_link(center, _propagator_cache[target.name])

    # We take the Earth JplCenter and attach it to the existing Earth center
    # (defined in beyond.frames.center)
    first_frame = _frame_cache["Earth"]
    BASE_FRAME.center.add_link(first_frame.center, BASE_FRAME.orientation, np.zeros(6))


def get_body(name):
    """Retrieve a body instance for a given object"""
    body = Pck()[name]
    body.propagator = get_propagator(name)
    return body


def get_propagator(name):
    """Retrieve a propagator object by its name"""
    if name not in _propagator_cache.keys():
        raise UnknownBodyError(name)

    return _propagator_cache[name]


def get_orbit(name, date):
    """Get an Orbit object of a celestial body at a given date"""
    return get_propagator(name).propagate(date)


def get_frame(name):
    """Get the frame attached to a celestial body"""
    frame = _frame_cache[name]
    # As the frame cache was populated at the same time as the propagator
    # cache, we have to attache the correct propagator to its body
    frame.center.body.propagator = get_propagator(name)
    return frame


def list_frames():
    """List frames available through .bsp files"""
    return list(_frame_cache.values())


def list_bodies():
    """List bodies available through .tpc files"""
    return [Pck()[k] for k in Pck().keys()]


if __name__ == "__main__":  # pragma: no cover

    import sys
    from beyond.dates import Date

    config.update({"eop": {"missing_policy": "pass"}})

    for file in sys.argv[1:]:
        print(file)
        print("*" * len(file))
        for segment in SPK.open(file).segments:

            start = Date(segment.start_jd - Date.JD_MJD)
            end = Date(segment.end_jd - Date.JD_MJD)

            center = target_names.get(segment.center, "Unknown")
            target = target_names.get(segment.target, "Unknown")
            fmt = "%Y-%m-%d"
            print(f"from {start:{fmt}} to {end:{fmt}} : {center} -> {target}")
        print()
