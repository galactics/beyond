import numpy as np

from .. import constants
from ..utils.node import Node
from ..utils.matrix import expand

from . import orient


class Center:
    """Center of a reference frame.

    This may represent a celestial body center, or the location of a ground station,
    or an arbitraty point in space
    """

    def __init__(self, name, body=None):
        self.name = name
        self.node = Node(name)
        self.body = body

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} '{self.name}' at {hex(id(self))}>"

    def add_link(self, center, orientation, offset):
        """Attach the center to an already defined center.

        For example when creating an earth ground station, the previously defined
        center should be Earth.

        Args:
            center (Center) : Parent center
            orientation (Orientation) : orientation of the offset relative to the parent center
            offset (list or Orbit) : offset relative to the parent center

        If 'offset' has a 'propagate' attribute, it is called to provide a moving
        offset.
        """
        self.node + center.node
        self.offset = offset
        self.orientation = orientation

        setattr(Center, f"{self.name}_to_{center.name}", self._to_parent)

    def convert_to(self, date, new_center, orientation):
        """Compute the offset between to centers, in the given orientation.

        Args:
            date (Date) :
            new_center (Center or str) :
            orientation (Orientation) :
        Return:
            numpy.ndarray : cartesian coordinates of the center relative
                to the new_center.
        """

        if isinstance(new_center, Center):
            new_center = new_center.name

        out = np.zeros(6)

        for a, b in self.node.steps(new_center):
            direct = f"{a}_to_{b}"
            reverse = f"{b}_to_{a}"

            if hasattr(self, direct):
                offset = getattr(self, direct)(date, orientation)
            elif hasattr(self, reverse):
                offset = -getattr(self, reverse)(date, orientation)
            else:
                raise ValueError(f"Unknown transformation {a} <-> {b}")

            out += np.asarray(offset)

        return out

    def _to_parent(self, date, orientation):
        """Provide the offset vector at a given date and in a given reference
        frame orientation.

        This method if here to be renamed when the class is instanciated.
        """

        if hasattr(self.offset, "propagate"):
            res = self.offset.propagate(date)
        else:
            res = self.offset

        return self.orientation.convert_to(date, orientation) @ res


Earth = Center("Earth", body=constants.Earth)


if __name__ == "__main__":  # pragma: no cover

    from ..dates import Date
    from .iau1980 import rate
    from ..env import jpl

    from space.wspace import ws

    ws.load()

    tls = Center(
        "TLS",
        offset=[4509.9270504078, 0, 4509.9270504078, 0, 0, 0],
        orientation=orient.ITRF,
        parent=Earth,
    )

    date = Date.now()

    print(tls.convert_to(date, "Earth", orient.TOD))

    mars = jpl.get_orbit("Mars", date).copy(frame="EME2000")
    mars_center = Center("Mars", offset=mars, orientation=orient.EME2000, parent=Earth)

    print(mars_center.convert_to(date, "Earth", orient.EME2000))
    print(mars_center.convert_to(date, "TLS", orient.ITRF))
