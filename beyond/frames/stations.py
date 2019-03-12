import numpy as np

from .frames import Frame, WGS84, _MetaFrame
from ..constants import Earth
from ..utils.matrix import rot2, rot3


class TopocentricFrame(Frame):
    """Base class for ground station
    """

    _rotation_before_translation = True

    @classmethod
    def visibility(cls, orb, **kwargs):
        """Visibility from a topocentric frame

        see :py:meth:`Propagator.iter() <beyond.propagators.base.Propagator.iter>`
        for description of arguments handling.

        Args:
            orb (Orbit): Orbit to compute visibility from the station with

        Keyword Args:
            start (Date): starting date of the visibility search
            stop (Date or datetime.timedelta) end of the visibility search
            step (datetime.timedelta): step of the computation
            events (bool, Listener or list): If evaluate to True, compute
                AOS, LOS and MAX elevation for each pass on this station.
                If 'events' is a Listener or an iterable of Listeners, they
                will be added to the computation

        Any other keyword arguments are passed to the propagator.

        Yield:
            Orbit: In-visibility point of the orbit. This Orbit is already
                in the frame of the station and in spherical form.
        """

        from ..orbits.listeners import stations_listeners, Listener

        listeners = kwargs.setdefault('listeners', [])
        events = kwargs.pop('events', None)
        event_classes = tuple()

        if events:
            # Handling of the listeners passed in the 'events' kwarg
            # and merging them with the `listeners` kwarg
            if isinstance(events, Listener):
                listeners.append(events)
            elif isinstance(events, (list, tuple)):
                listeners.extend(events)

            sta_list = stations_listeners(cls)
            listeners.extend(sta_list)

            # Only the events present in the `event_classes` list will be yielded
            # outside of visibility. This list was created in order to force
            # the yield of AOS and LOS.

            event_classes = tuple(listener.event for listener in sta_list)

        for point in orb.iter(**kwargs):
            point.frame = cls
            point.form = 'spherical'

            # Not very clean !
            if point.phi < 0 and not isinstance(point.event, event_classes):
                continue

            yield point

    def _to_parent_frame(self, *args, **kwargs):
        """Conversion from Topocentric Frame to parent frame
        """
        lat, lon, _ = self.latlonalt
        m = rot3(-lon) @ rot2(lat - np.pi / 2.) @ rot3(self.heading)
        offset = np.zeros(6)
        offset[:3] = self.coordinates
        return self._convert(m, m), offset

    @classmethod
    def _geodetic_to_cartesian(cls, lat, lon, alt):
        """Conversion from latitude, longitude and altitude coordinates to
        cartesian with respect to an ellipsoid

        Args:
            lat (float): Latitude in radians
            lon (float): Longitude in radians
            alt (float): Altitude to sea level in meters

        Return:
            numpy.array: 3D element (in meters)
        """
        C = Earth.r / np.sqrt(1 - (Earth.e * np.sin(lat)) ** 2)
        S = Earth.r * (1 - Earth.e ** 2) / np.sqrt(1 - (Earth.e * np.sin(lat)) ** 2)
        r_d = (C + alt) * np.cos(lat)
        r_k = (S + alt) * np.sin(lat)

        norm = np.sqrt(r_d ** 2 + r_k ** 2)
        return norm * np.array([
            np.cos(lat) * np.cos(lon),
            np.cos(lat) * np.sin(lon),
            np.sin(lat)
        ])

    @classmethod
    def get_mask(cls, azim):
        """Linear interpolation between two points of the mask
        """

        if cls.mask is None:
            raise ValueError("No mask defined for the station {}".format(cls.name))

        azim %= 2 * np.pi

        if azim in cls.mask[0, :]:
            return cls.mask[1, np.where(azim == cls.mask[0, :])[0][0]]

        for next_i, mask_azim in enumerate(cls.mask[0, :]):
            if mask_azim > azim:
                break
        else:
            next_i = 0

        x0, y0 = cls.mask[:, next_i - 1]
        x1, y1 = cls.mask[:, next_i]

        if next_i - 1 == -1:
            x0 = 0

        return y0 + (y1 - y0) * (azim - x0) / (x1 - x0)


def create_station(name, latlonalt, parent_frame=WGS84, orientation='N', mask=None):
    """Create a ground station instance

    Args:
        name (str): Name of the station

        latlonalt (tuple of float): coordinates of the station, as follow:

            * Latitude in degrees
            * Longitude in degrees
            * Altitude to sea level in meters

        parent_frame (Frame): Planetocentric rotating frame of reference of
            coordinates.
        orientation (str or float): Heading of the station
            Acceptable values are 'N', 'S', 'E', 'W' or any angle in radians
        mask: (2D array of float): First dimension is azimuth counterclockwise strictly increasing.
            Second dimension is elevation. Both in radians

    Return:
        TopocentricFrame
    """

    if isinstance(orientation, str):
        orient = {'N': np.pi, 'S': 0., 'E': np.pi / 2., 'W': 3 * np.pi / 2.}
        heading = orient[orientation]
    else:
        heading = orientation

    latlonalt = list(latlonalt)
    latlonalt[:2] = np.radians(latlonalt[:2])
    coordinates = TopocentricFrame._geodetic_to_cartesian(*latlonalt)

    mtd = '_to_%s' % parent_frame.__name__
    dct = {
        mtd: TopocentricFrame._to_parent_frame,
        'latlonalt': latlonalt,
        'coordinates': coordinates,
        'parent_frame': parent_frame,
        'heading': heading,
        'orientation': orientation,
        'mask': np.array(mask) if mask else None,
    }
    cls = _MetaFrame(name, (TopocentricFrame,), dct)
    cls + parent_frame

    return cls
