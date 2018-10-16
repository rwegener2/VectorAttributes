class GeojsonCheck(object):
    """
    Class to determine if an input object is a geojson or not and determine object type.  Currently only supports
    geojson features.  Does not validate geometry coordinates
    """
    def __init__(self, input_object):
        self.input = input_object
        self.type = self.determine_feature_type()
        self.is_geojson = self.validate_object()

    def is_dict(self):
        return isinstance(self.input, dict)

    # TODO testing for this method
    def determine_feature_type(self):
        if not self.is_dict():
            return False
        elif 'type' not in self.input.keys():
            return False
        elif self.input['type'] in ['FeatureCollection', 'Feature', 'GeometryCollection', 'Point', 'MultiPoint',
                                    'LineString', 'MultiLineString', 'Polygon', 'Multipolygon']:
            return self.input['type']
        else:
            return False

    # TODO testing for this method
    def validate_object(self):
        if self.type is False:
            return False
        elif self.type is 'FeatureCollection':
            print('FeatureCollection objects not yet supported')
            return False
        elif self.type is 'Feature':
            return self.validate_feature()
        else:
            print('Purely geometry objects not yet supported')
            return False

    def feature_key_check(self):
        required_keys = ['properties', 'geometry', 'type']
        return all(i in self.input.keys() for i in required_keys)

    def geometry_key_check(self):
        required_keys = ['type', 'coordinates']
        return all(i in self.input['geometry'].keys() for i in required_keys)

    def validate_feature(self):
        if not self.feature_key_check():
            return False
        if not self.geometry_key_check():
            return False
        else:
            return True
