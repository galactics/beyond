import numpy as np

from ...orbits.cov import Cov


def read_cov(orb, data):

    frame = data.get("COV_REF_FRAME", orb.cov.PARENT_FRAME)
    if frame in ("RSW", "RTN"):
        frame = "QSW"

    values = [
        [
            data["CX_X"],
            data["CY_X"],
            data["CZ_X"],
            data["CX_DOT_X"],
            data["CY_DOT_X"],
            data["CZ_DOT_X"],
        ],
        [
            data["CY_X"],
            data["CY_Y"],
            data["CZ_Y"],
            data["CX_DOT_Y"],
            data["CY_DOT_Y"],
            data["CZ_DOT_Y"],
        ],
        [
            data["CZ_X"],
            data["CZ_Y"],
            data["CZ_Z"],
            data["CX_DOT_Z"],
            data["CY_DOT_Z"],
            data["CZ_DOT_Z"],
        ],
        [
            data["CX_DOT_X"],
            data["CX_DOT_Y"],
            data["CX_DOT_Z"],
            data["CX_DOT_X_DOT"],
            data["CY_DOT_X_DOT"],
            data["CZ_DOT_X_DOT"],
        ],
        [
            data["CY_DOT_X"],
            data["CY_DOT_Y"],
            data["CY_DOT_Z"],
            data["CY_DOT_X_DOT"],
            data["CY_DOT_Y_DOT"],
            data["CZ_DOT_Y_DOT"],
        ],
        [
            data["CZ_DOT_X"],
            data["CZ_DOT_Y"],
            data["CZ_DOT_Z"],
            data["CZ_DOT_X_DOT"],
            data["CZ_DOT_Y_DOT"],
            data["CZ_DOT_Z_DOT"],
        ],
    ]

    cov = Cov(orb, np.array(values).astype(np.float) * 1e6)
    cov._frame = frame

    return cov


def dump_cov(cov):
    text = "\n"
    if cov.frame != cov.PARENT_FRAME:
        frame = cov.frame
        if frame == "QSW":
            frame = "RSW"
        text += "COV_REF_FRAME        = {frame}\n".format(frame=frame)

    elems = ["X", "Y", "Z", "X_DOT", "Y_DOT", "Z_DOT"]
    for i, a in enumerate(elems):
        for j, b in enumerate(elems[: i + 1]):
            txt = "{a}_{b}".format(a=a, b=b)

            text += "C{txt:<19} = {v: 0.16e}\n".format(txt=txt, v=cov[i, j] / 1e6)

    return text
