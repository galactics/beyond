"""This module provides ways to handle the CCSDS formats

It is based on the `CCSDS standard <https://public.ccsds.org/Publications/BlueBooks.aspx>`__.

For XML input/output validation, it is possible to use XSD files provided at
https://sanaregistry.org/r/ndmxml/.
"""

from ...config import config
from . import opm
from . import oem
from . import omm
from . import tdm
from .commons import CcsdsError, detect2load, detect2dump

__all__ = ["load", "loads", "dump", "dumps", "CcsdsError"]


def load(fp):  # pragma: no cover
    """Read CCSDS format from a file descriptor, and provide the beyond class
    corresponding; Orbit or list of Orbit if it's an OPM, Ephem if it's an
    OEM, MeasureSet if it's a TDM.

    Args:
        fp: file descriptor of a CCSDS file
    Return:
        Orbit, Ephem, List[Ephem] or MeasureSet
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
        Orbit, Ephem, List[Ephem] or MeasureSet
    Raise:
        CcsdsError: when the text is not a recognizable CCSDS format
    """

    type, fmt = detect2load(text)

    if type == "oem":
        func = oem.loads
    elif type == "opm":
        func = opm.loads
    elif type == "tdm":
        func = tdm.loads
    elif type == "omm":
        func = omm.loads
    else:  # pragma: no cover
        raise CcsdsError(f"Unknown CCSDS type : {type}")

    return func(text, fmt=fmt)


def dump(data, fp, **kwargs):  # pragma: no cover
    """Write a CCSDS file depending on the type of data, this could be an OPM
    file (Orbit), an OEM file (Ephem or list of Ephem), or a TDM file
    (MeasureSet).

    Args:
        data (Orbit, Ephem, List[Ephem] or MeasureSet)
        fp (file descriptor)
    Keyword Arguments:
        name (str): Name of the object
        cospar_id (str): International designator of the object
        originator (str): Originator of the CCSDS file
        fmt (str): Output format of the file, can be 'xml' or 'kvn'. Default to 'kvn'
        kep (bool): For OPM only, if ``False`` disable the optional osculating keplerian elements.
    Raise:
        TypeError: if the data object class is not handled

    If ``kep = True`` **and** the frame of the StateVector is (pseudo-)inertial (i.e. EME2000, CIRF, TOD, etc.)
    the optional osculating keplerian elements will be added to the OPM.

    It is possible to set the configuration dict to change the default value
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

    type = detect2dump(data)

    if type == "oem":
        content = oem.dumps(data, **kwargs)
    elif type == "opm":
        content = opm.dumps(data, **kwargs)
    elif type == "omm":
        content = omm.dumps(data, **kwargs)
    elif type == "tdm":
        content = tdm.dumps(data, **kwargs)
    else:  # pragma: no cover
        raise CcsdsError(f"Unknown object type for CCSDS : {type}")

    return content
