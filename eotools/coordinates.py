#!/usr/bin/env python

from __future__ import absolute_import
import collections

import gdal


def convert_coordinates(geotransform, xy, to_map=True, centre=False):
    """
    Given a tuple containing an (x, y) co-ordinate pair, convert
    the co-ordinate pair to either image/array co-ordinates or
    real world (map) co-ordinates.

    :param geotransform:
        A list or tuple of length 6 containing a valid GDAL style
        GeoTransform.

    :param xy:
        A tuple containing an (x, y) co-ordinate pair. The pair
        can be either image/array co-ordinates or map co-ordinates.
        If xy is a list of tuple co-ordinate pairs, then each (x, y)
        pair will be converted, eg [(x, y), (x, y), (x, y)].
        If image co-ordinates are input, then set to_map=True. If map
        co-ordinates are input, then set to_map=False.

    :param to_map:
        A boolean indicating if the conversion should be image to
        map or map to image. Default is True (image to map).

    :param centre:
        A boolean indicating if the returned co-ordinate pair
        should be offset by 0.5 indicating the centre of a pixel.
        Default is False.

    :return:
        A tuple containing an (x, y) co-ordinate pair.
        The returned type will be int if to_map=False and float
        if to_map=True (Default). If xy is a list of tuple
        co-ordinate pairs, then a list of (x, y) co-ordinate pairs
        will be returned, eg [(x, y), (x, y), (x, y)].
    """
    # If we have a list of tuples otherwise we'll get an int
    if isinstance(xy[0], collections.Sequence):
        points = []
        if to_map:
            if centre:
                xy = [(x + 0.5, y + 0.5) for x, y in xy]
            for point in xy:
                x = point[0] * geotransform[1] + geotransform[0]
                y = geotransform[3] - point[1] * abs(geotransform[5])
                points.append((x, y))
        else:
            invgt = gdal.InvGeoTransform(geotransform)[1]
            for point in xy:
                x = int(point[0] * invgt[1] + invgt[0])
                y = int(invgt[3] - point[1] * abs(invgt[5]))
                points.append((x, y))
        return points
    else:
        if to_map:
            if centre:
                xy = tuple(v + 0.5 for v in xy)
            x = xy[0] * geotransform[1] + geotransform[0]
            y = geotransform[3] - xy[1] * abs(geotransform[5])
        else:
            invgt = gdal.InvGeoTransform(geotransform)[1]
            x = int(xy[0] * invgt[1] + invgt[0])
            y = int(invgt[3] - xy[1] * abs(invgt[5]))
        return x, y
