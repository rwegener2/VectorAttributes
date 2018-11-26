from shapely.geometry import shape as get_shape
from vectorattributes.geojson_check import GeojsonCheck
from .projection import *


DEFAULT_PARAMS = {
    "spatial_calcs": {
        "ground_buffer_inner": 6,
        "ground_buffer_outer": 0.2,
        "eave_buffer": -0.1}
}


def error_factory():
    return {
        "geometry": {
            "buffer0": False,
            "convex_hull": False},
        "dsm_null": False
    }


class Footprint(object):
    """
    This class handles basic loading and formatting of a geojson feature.  It opens the feature, extracts the geometry
    as a shapely object, checks the features for validity (reformatting if needed), extracts feature properties,
    and buffers the object.

    Currently written for housing polygons.  Buffer method perhaps extracted in the future and more general methods
    included.
    """
    DEFAULT_PARAMS = DEFAULT_PARAMS

    def __init__(self, feature, crs):
        """
        :param feature: geojson feature
        :param crs: crs predefined by EPSG and input as a dict version of the proj4 string Ex. {'init': 'epsg:4326'}
        """
        if GeojsonCheck(feature).is_geojson is not True:
            raise TypeError('Input is not a geojson feature')
        self.feature = feature
        self.fprint_crs = self.crs_isvalid(crs)
        self.footprint_errors = error_factory()
        self.footprint = self.get_polygon()
        self.properties = self.feature['properties']
        self.footprint_ground_full, self.footprint_ground = self.buffer_donut(DEFAULT_PARAMS['spatial_calcs']
                                                                              ['ground_buffer_inner'] +
                                                                              DEFAULT_PARAMS['spatial_calcs']
                                                                              ['ground_buffer_outer'])
        self.footprint_roof, self.footprint_eave = self.buffer_donut(DEFAULT_PARAMS['spatial_calcs']['eave_buffer'])

    def polygon_is_valid(self, polygon):
        """
        check the polygon for validity and fix with either a buffer of 0 or, if need be, return a convex hull of the
        polygon for analysis
        :return: original or corrected geometry
        """
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
            self.footprint_errors['geometry']['buffer0'] = True
        if not polygon.is_valid:
            polygon = polygon.convex_hull
            self.footprint_errors['geometry']['convex_hull'] = True
        return polygon

    @staticmethod
    def crs_isvalid(crs):
        if crs is None:
            return None
        if len(crs.keys()) > 1 or 'init' not in crs.keys() or crs['init'][:4] != 'epsg':
            raise RuntimeError(
                'Improper crs input, crs must be predefined using EPSG codes an cannot be raw parameters')
        elif crs['init'][5:7] != '32' and crs['init'] != 'epsg:4326':
            raise RuntimeError('Cannot handle epsg codes that are not WGS84 or UTM zones')
        return crs['init']

    def get_polygon(self):
        """
        :return: valid shapely geometry for feature
        """
        polygon = get_shape(self.feature['geometry'])
        polygon_validated = self.polygon_is_valid(polygon)
        return polygon_validated

    # TODO not tested -- create subclass
    def buffer_donut(self, buffer_distance):
        """
        Creates the shapely geometries for the buffered area and for the "donut" of the buffered area minus the
        original polygon.  Output polygons are given in crs of shape input into Footprint feature
        :return: tuple(shapely geometry buffered area, shapely geometry "donut" area)
        """
        utm_code = None
        if self.fprint_crs == 'epsg:4326':
            utm_polygon = convert_4326_to_utm(self.footprint)
            utm_code = get_utm_epsg(self.footprint.centroid.x, self.footprint.centroid.y)
        else:
            utm_polygon = self.footprint
        if buffer_distance > 0:
            buffered_poly = utm_polygon.buffer(buffer_distance)
            donut_poly = buffered_poly.difference(utm_polygon)
        elif buffer_distance < 0:
            buffered_poly = utm_polygon.buffer(buffer_distance)
            donut_poly = utm_polygon.difference(buffered_poly)
        else:
            raise ValueError('buffer distance cannot be equal to zero')
        if utm_code:
            buffered_poly = reproject(buffered_poly, from_proj=utm_code, to_proj=self.fprint_crs)
            donut_poly = reproject(donut_poly, from_proj=utm_code, to_proj=self.fprint_crs)
        return buffered_poly, donut_poly
