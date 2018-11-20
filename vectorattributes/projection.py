import pyproj
from shapely import ops
from functools import partial
import math


# TODO there really should be a check on these functions so they do not accept any shape that does not have EPSG 4326
def get_utm_epsg(lon, lat):
    """
    Determine the UTM zone of the given point from an input lat lon in EPSG:4326 and output the EPSG code of that zone
    :return: EPSG code string in the form EPSG:32xxx
    """
    utm_band = int((math.floor((lon + 180) / 6) % 60) + 1)
    if len(str(utm_band)) == 1:
        utm_band = '0{}'.format(utm_band)
    if lat >= 0:
        epsg_code = 'EPSG:326{}'.format(utm_band)
    else:
        epsg_code = 'EPSG:327{}'.format(utm_band)
    return epsg_code


def reproject(geom, from_proj=None, to_proj=None):
    """
    Recommended function provided by shapely for projection transformations
    :param geom: shapely geometry object
    :param from_proj: both proj should be
    :return: reprojected shapely geometry
    """
    tfm = partial(pyproj.transform, pyproj.Proj(init=from_proj), pyproj.Proj(init=to_proj))
    return ops.transform(tfm, geom)


def convert_4326_to_utm(polygon):
    """
    convert a polygon from EPSG:4326 to the corresponding UTM zone coordinates
    suitable only for objects or areas that fit inside a single utm zone
    :param polygon: shapely object
    :return: reprojected shapely object
    """
    utm_code = get_utm_epsg(polygon.centroid.x, polygon.centroid.y)
    projected_poly = reproject(polygon, from_proj='epsg:4326', to_proj=utm_code)
    return projected_poly
