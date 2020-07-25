import numpy as np

from ...orbits.cov import Cov


def load_cov(orb, data):

    if "COV_REF_FRAME" in data:
        frame = data["COV_REF_FRAME"].text
    else:
        frame = orb.frame

    if frame in ("RSW", "RTN"):
        frame = "QSW"

    values = [
        [
            data["CX_X"].text,
            data["CY_X"].text,
            data["CZ_X"].text,
            data["CX_DOT_X"].text,
            data["CY_DOT_X"].text,
            data["CZ_DOT_X"].text,
        ],
        [
            data["CY_X"].text,
            data["CY_Y"].text,
            data["CZ_Y"].text,
            data["CX_DOT_Y"].text,
            data["CY_DOT_Y"].text,
            data["CZ_DOT_Y"].text,
        ],
        [
            data["CZ_X"].text,
            data["CZ_Y"].text,
            data["CZ_Z"].text,
            data["CX_DOT_Z"].text,
            data["CY_DOT_Z"].text,
            data["CZ_DOT_Z"].text,
        ],
        [
            data["CX_DOT_X"].text,
            data["CX_DOT_Y"].text,
            data["CX_DOT_Z"].text,
            data["CX_DOT_X_DOT"].text,
            data["CY_DOT_X_DOT"].text,
            data["CZ_DOT_X_DOT"].text,
        ],
        [
            data["CY_DOT_X"].text,
            data["CY_DOT_Y"].text,
            data["CY_DOT_Z"].text,
            data["CY_DOT_X_DOT"].text,
            data["CY_DOT_Y_DOT"].text,
            data["CZ_DOT_Y_DOT"].text,
        ],
        [
            data["CZ_DOT_X"].text,
            data["CZ_DOT_Y"].text,
            data["CZ_DOT_Z"].text,
            data["CZ_DOT_X_DOT"].text,
            data["CZ_DOT_Y_DOT"].text,
            data["CZ_DOT_Z_DOT"].text,
        ],
    ]

    cov = Cov(orb, np.array(values).astype(np.float) * 1e6, frame)

    return cov


def dump_cov(cov):
    text = "\n"
    if cov.frame != cov.orb.frame:
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
