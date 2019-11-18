import numpy as np

from ...dates import Date
from ...utils import units
from ...orbits import Orbit, Ephem

from .commons import parse_date, CcsdsParseError, _dump_header, _dump_meta_odm


def read_oem(string):
    """
    Args:
        string (str): String containing the OEM
    Return:
        Ephem:
    """

    ephems = []
    required = ("REF_FRAME", "CENTER_NAME", "TIME_SYSTEM", "OBJECT_ID", "OBJECT_NAME")

    mode = None
    for line in string.splitlines():

        if not line or line.startswith("COMMENT"):  # pragma: no cover
            continue
        elif line.startswith("META_START"):
            mode = "meta"
            ephem = {"orbits": []}
            ephems.append(ephem)
        elif line.startswith("META_STOP"):
            mode = "data"

            # Check for required fields
            for k in required:
                if k not in ephem:
                    raise CcsdsParseError("Missing field '{}'".format(k))

            # Conversion to be compliant with beyond.env.jpl dynamic reference
            # frames naming convention.
            if ephem["CENTER_NAME"].lower() != "earth":
                ephem["REF_FRAME"] = ephem["CENTER_NAME"].title().replace(" ", "")
        elif mode == "meta":
            key, _, value = line.partition("=")
            ephem[key.strip()] = value.strip()
        elif mode == "data":
            date, *state_vector = line.split()
            date = parse_date(date, ephem["TIME_SYSTEM"])

            # Conversion from km to m, from km/s to m/s
            # and discard acceleration if present
            state_vector = np.array([float(x) for x in state_vector[:6]]) * units.km

            ephem["orbits"].append(
                Orbit(date, state_vector, "cartesian", ephem["REF_FRAME"], None)
            )

    for i, ephem_dict in enumerate(ephems):
        if not ephem_dict["orbits"]:
            raise CcsdsParseError("Empty ephemeris")

        # In case there is no recommendation for interpolation
        # default to a Lagrange 8th order
        method = ephem_dict.get("INTERPOLATION", "Lagrange").lower()
        order = int(ephem_dict.get("INTERPOLATION_DEGREE", 7)) + 1
        ephem = Ephem(ephem_dict["orbits"], method=method, order=order)

        ephem.name = ephem_dict["OBJECT_NAME"]
        ephem.cospar_id = ephem_dict["OBJECT_ID"]
        ephems[i] = ephem

    if len(ephems) == 1:
        return ephems[0]

    return ephems


def dump_oem(data, **kwargs):

    if isinstance(data, Ephem):
        data = [data]

    header = _dump_header(data, "OEM", version="2.0", **kwargs)

    content = []
    for i, data in enumerate(data):

        data.form = "cartesian"

        interp = data.method.upper()
        if data.method != data.LINEAR:
            interp += "\nINTERPOLATION_DEGREE = {}".format(data.order - 1)

        meta = _dump_meta_odm(data, **kwargs)
        meta += """TIME_SYSTEM          = {orb.start.scale.name}
START_TIME           = {orb.start:%Y-%m-%dT%H:%M:%S.%f}
STOP_TIME            = {orb.stop:%Y-%m-%dT%H:%M:%S.%f}
INTERPOLATION        = {interp}
META_STOP

""".format(
            creation_date=Date.now(),
            originator=kwargs.get("originator", "N/A"),
            name=kwargs.get("name", "N/A"),
            cospar_id=kwargs.get("cospar_id", "N/A"),
            orb=data,
            interp=interp,
        )

        text = []
        for orb in data:
            text.append(
                "{date:%Y-%m-%dT%H:%M:%S.%f} {orb[0]:{fmt}} {orb[1]:{fmt}} {orb[2]:{fmt}} {orb[3]:{fmt}} {orb[4]:{fmt}} {orb[5]:{fmt}}".format(
                    date=orb.date, orb=orb.base / units.km, fmt=" 10f"
                )
            )

        content.append(meta + "\n".join(text))

    return header + "\n" + "\n\n\n".join(content)
