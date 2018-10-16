from vectorattributes.projection import *
from tests.test_structures import *
from shapely.geometry import shape as get_shape


valid_shapely_polygon_feature_wgs = get_shape(valid_geojson_polygon_feature_wgs['geometry'])
valid_shapely_polygon_feature_utm = get_shape(valid_geojson_polygon_feature_utm['geometry'])


def test_single_digit_zone():
    assert get_utm_epsg(-155.575664364, 19.459831494) == 'EPSG:32605'


def test_northern_hemisphere():
    assert get_utm_epsg(-74.0131, 40.7118) == 'EPSG:32618'


def test_southern_hemisphere():
    assert get_utm_epsg(-109.3497, -27.1127) == 'EPSG:32712'


def test_convert_4326_to_utm():
    output = convert_4326_to_utm(valid_shapely_polygon_feature_wgs)
    reprojected = round_shapely_object(output)
    assert reprojected == valid_shapely_polygon_feature_utm
