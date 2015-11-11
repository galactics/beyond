#!/usr/bin/env python
# -*- coding: utf-8 -*-


def linear(x, x_list, y_list):
    """Linear interpolation

    Args:
        x (float): Coordinate of the interpolated value
        x_list (tuple): x-coordinates of data
        y_list (tuple): y-coordinates of data
    Return:
        float

    Example:
        >>> x_list = [1, 2]
        >>> y_list = [12, 4]
        >>> linear(1.75, x_list, y_list)
        6.0

    """
    x0, x1 = x_list
    y0, y1 = y_list
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
