"""Module dedicated to parsing Horizon ephemeris format
retrievable from NASA's https://ssd.jpl.nasa.gov/horizons.cgi
"""

import numpy as np

from ..orbits import Orbit, Ephem
from ..dates import Date
from ..utils import units, matrix
from ..frames.iau1980 import _nutation
from ..errors import ParseError


class HorizonParseError(ParseError):
    pass


def load(fp):
    """Read Horizon format ephemeris from a file

    Args:
        fp: file descriptor of a Horizon file
    Return:
        Ephem
    Raises:
        HorizonParseError: The file is not a recognizable Horizon format
    """

    return loads(fp.read())


def loads(text):
    """Read Horizon format ephemeris from a text

    Args:
        text (str): text in Horizon format
    Return:
        Ephem
    Raises:
        HorizonParseError: The text is not a recognizable Horizon format
    """

    frames = {"ICRF/J2000.0": "EME2000", "FK4/B1950.0": "G50", "ICRF": "EME2000"}

    formats = {
        "1 (position only)": ("date", "pos"),
        "2 (position and velocity)": ("date", "pos", "vel"),
        "3 (position, velocity, LT, range, range-rate)": (
            "date",
            "pos",
            "vel",
            "dummy",
        ),
        "4 (position, LT, range, and range-rate)": ("date", "pos", "dummy"),
        "5 (velocity only)": ("date", "vel"),
    }

    lines = text.splitlines()

    if "$$SOE" not in lines or "$$EOE" not in lines:
        # No data for this body, this could be due to an absence of data for the
        # requested timespan. The next few lines try to extract the error message
        # inside the Horizon format in order to provide it to the user
        for line in lines:
            if line.startswith("No ephemeris for target"):
                break
        raise HorizonParseError(line)

    ephem_start = lines.index("$$SOE") + 1
    ephem_stop = lines.index("$$EOE")

    comments, header = "", {}

    # Header parsing
    for line in lines[:ephem_start]:
        if not line or line.startswith("******"):
            continue
        elif len(line) > 16 and line[16] == ":":
            k, _, v = line.partition(":")
            header[k.strip()] = v.strip()
        else:
            comments += f"\n{line}"

    # Header conversion
    name = header["Target body name"].partition("{")[0].strip()
    center = header["Center body name"].partition("{")[0].strip()
    center_site = header["Center-site name"]

    unit = header["Output units"]
    if unit.startswith("KM"):
        pos_unit = vel_unit = units.km
    else:
        pos_unit = vel_unit = units.AU
    if unit.endswith("D"):
        vel_unit /= units.day

    _type = header["Output type"]
    if _type != "GEOMETRIC cartesian states":
        raise HorizonParseError("Unknown output type")

    _format = header["Output format"]
    if _format not in formats:
        raise HorizonParseError(f"Unknown format : '{_format}'")

    frame = header["Reference frame"]
    if frame not in frames:
        raise HorizonParseError(f"Unknown frame : {frame}")
    frame = frames[frame.strip()]

    if frame == "EME2000":
        # If the central body is an other solar system celestial body
        # we have to change the reference frame to match the ones defined in beyond
        if center != "Earth (399)":
            frame = center.partition("(")[0].strip()

    coord = header.get(
        "Coordinate systm", "Earth Mean Equator and Equinox of Reference Epoch"
    )
    if coord == "Earth Mean Equator and Equinox of Reference Epoch":
        coord = "equatorial"
    elif coord == "Ecliptic and Mean Equinox of Reference Epoch":
        coord = "ecliptic"
    else:
        # Should handle the equator of each body
        raise HorizonParseError("Unknown coordinate system")

    line_desc = formats[_format]

    # Data parsing
    orbs = []
    for i in range(ephem_start, ephem_stop, len(line_desc)):
        date, *data = lines[i : i + len(line_desc)]

        *date, scale = date.split()[3:]
        date = Date.strptime(" ".join(date), "%Y-%b-%d %H:%M:%S.%f", scale=scale)

        if coord == "equatorial":
            rotation = np.identity(3)
        else:
            # rotation of the vector in order to convert it from ecliptic
            # plane to equatorial plane, which is the only reference plane in
            # the beyond library at the moment
            epsilon_bar, _, delta_epsilon = np.deg2rad(_nutation(date))
            epsilon = epsilon_bar + delta_epsilon
            rotation = matrix.rot1(-epsilon)

        vector = [0] * 6
        for desc, line in zip(line_desc[1:], data):
            if "=" in line:
                # removing labels before casting to float
                line = " ".join(line.split("=")[1:]).split()[::2]
            else:
                line = line.split()

            if desc == "pos":
                vector[:3] = rotation @ [float(x) * pos_unit for x in line]
            elif desc == "vel":
                vector[3:] = rotation @ [float(x) * vel_unit for x in line]

        orbs.append(Orbit(vector, date, "cartesian", frame, None))

    ephem = Ephem(orbs)
    ephem.name = name

    return ephem
