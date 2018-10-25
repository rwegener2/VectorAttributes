from shapely.geometry import shape as get_shape
from vectorattributes.geojson_check import GeojsonCheck


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
    # TODO input feature must already be in utm
    """
    This class handles basic loading and formatting of a geojson feature.  It opens the feature, extracts the geometry
    as a shapely object, checks the features for validity (reformatting if needed), extracts feature properties,
    and buffers the object.

    Currently written for housing polygons.  Buffer method perhaps extracted in the future and more general methods
    included.

    This class assumes, but does not test, that the feature input is in WGS84
    """
    DEFAULT_PARAMS = DEFAULT_PARAMS

    def __init__(self, feature):
        if GeojsonCheck(feature).is_geojson is not True:
            raise TypeError('Input is not a geojson feature')
        self.feature = feature
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
            print('invalid geom buffering')
            polygon = polygon.buffer(0)
            self.footprint_errors['geometry']['buffer0'] = True
        if not polygon.is_valid:
            print('invalid geom convex hulling')
            polygon = polygon.convex_hull
            self.footprint_errors['geometry']['convex_hull'] = True
        return polygon

    def get_polygon(self):
        """
        :return: valid utm shapely geometry for feature
        """
        polygon = get_shape(self.feature['geometry'])
        polygon_validated = self.polygon_is_valid(polygon)
        # polygon_utm = convert_4326_to_utm(polygon_validated)
        return polygon_validated

    # TODO not tested -- create subclass
    def buffer_donut(self, buffer_distance):
        """
        Creates the shapely geometries for the buffered area and for the "donut" of the buffered area minus the
        original polygon
        :return: tuple(shapely geometry buffered area, shapely geometry "donut" area)
        """
        if buffer_distance > 0:
            buffered_poly = self.footprint.buffer(buffer_distance)
            donut_poly = buffered_poly.difference(self.footprint)
        elif buffer_distance < 0:
            buffered_poly = self.footprint.buffer(buffer_distance)
            donut_poly = self.footprint.difference(buffered_poly)
        else:
            raise ValueError('buffer distance cannot be equal to zero')
        return buffered_poly, donut_poly
