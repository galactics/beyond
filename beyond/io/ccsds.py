"""This module provides ways to handle the CCSDS formats

It is based on the `CCSDS standard <https://public.ccsds.org/Publications/BlueBooks.aspx>`__.

For XML input/output validation, it is possible to use XSD files provided at
https://sanaregistry.org/r/ndmxml/.
"""

from collections.abc import Iterable

from ..config import config
from ..orbits import Orbit, Ephem
from ..utils.measures import Measure
from ..propagators.base import AnalyticalPropagator
from ..frames.frames import TEME
from ..orbits.forms import TLE
from ._ccsds.opm import load_opm, dump_opm
from ._ccsds.oem import load_oem, dump_oem
from ._ccsds.omm import load_omm, dump_omm
from ._ccsds.tdm import load_tdm, dump_tdm
from ._ccsds.commons import CcsdsError, detect

__all__ = ["load", "loads", "dump", "dumps", "CcsdsError"]


def load(fp):  # pragma: no cover
    """Read CCSDS format from a file descriptor, and provide the beyond class
    corresponding; Orbit or list of Orbit if it's an OPM, Ephem if it's an
    OEM, MeasureSet if it's a TDM.

    Args:
        fp: file descriptor of a CCSDS file
    Return:
        Orbit or Ephem
    Raise:
        CcsdsError: when the text is not a recognizable CCSDS format
    """
    return loads(fp.read())


def loads(text):
    """Read CCSDS from a string, and provide the beyond class corresponding;
    Orbit or list of Orbit if it's an OPM, Ephem if it's an OEM, MeasureSet
    if it's a TDM.

    Args:
        text (str):
    Return:
        Orbit or Ephem
    Raise:
        CcsdsError: when the text is not a recognizable CCSDS format
    """

    type, fmt = detect(text)

    if type == "OEM":
        func = load_oem
    elif type == "OPM":
        func = load_opm
    elif type == "TDM":
        func = load_tdm
    elif type == "OMM":
        func = load_omm
    else:
        raise CcsdsError("Unknown CCSDS type")

    return func(text, fmt=fmt)


def dump(data, fp, **kwargs):  # pragma: no cover
    """Write a CCSDS file depending on the type of data, this could be an OPM
    file (Orbit or list of Orbit), an OEM file (Ephem), or a TDM file
    (MeasureSet).

    Args:
        data (Orbit, list of Orbit, Ephem, or MeasureSet)
        fp (file descriptor)
    Keyword Arguments:
        name (str): Name of the object
        cospar_id (str): International designator of the object
        originator (str): Originator of the CCSDS file
        fmt (str): Output format of the file, can be 'xml' or 'kvn'. Default to 'kvn'

    It is also possible to set the configuration dict to change the default value
    of 'fmt'.

    .. code-block:: python

        from beyond.config import config
        config["io"] = {"ccsds_default_format": "xml"}
    """
    fp.write(dumps(data, **kwargs))


def dumps(data, **kwargs):
    """Create a string CCSDS representation of the object

    Same arguments and behaviour as :py:func:`dump`
    """

    kwargs.setdefault("fmt", config.get("io", "ccsds_default_format", fallback="kvn"))

    if isinstance(data, Ephem) or (
        isinstance(data, Iterable) and all(isinstance(x, Ephem) for x in data)
    ):
        content = dump_oem(data, **kwargs)
    elif isinstance(data, Orbit):
        if (
            isinstance(data.propagator, AnalyticalPropagator)
            and issubclass(data.frame, TEME)
            and data.form is TLE
        ):
            content = dump_omm(data, **kwargs)
        else:
            content = dump_opm(data, **kwargs)
    elif isinstance(data, Iterable) and all(isinstance(x, Measure) for x in data):
        content = dump_tdm(data, **kwargs)
    else:
        raise TypeError("Unknown object type")

    return content
