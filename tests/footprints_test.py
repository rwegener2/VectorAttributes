import pytest
from vectorattributes.footprint import Footprint
from tests.test_structures import *
from shapely.geometry import shape as get_shape

valid_shapely_polygon_feature = get_shape(valid_geojson_polygon_feature['geometry'])
invalid_shapely_overlap_polygon = get_shape(invalid_geojson_overlap_polygon['geometry'])
valid_shapely_polygon_feature_wgs = get_shape(valid_geojson_polygon_feature_wgs['geometry'])
valid_shapely_polygon_feature_utm = get_shape(valid_geojson_polygon_feature_utm['geometry'])


@pytest.fixture
def rounded_utm_footprint():
    """ Returns a Footprint containing a WGS polygon which was converted to UTM by default and rounded"""
    default_output = Footprint(valid_geojson_polygon_feature_wgs)
    rounded_output = round_shapely_object(default_output.footprint)
    default_output.footprint = rounded_output
    return default_output


def test_input_geojson():
    with pytest.raises(TypeError):
        Footprint(no_type_geojson_polygon_feature)


def test_get_polygon_utm_conversion():
    footprint_obj = rounded_utm_footprint()
    assert footprint_obj.footprint == valid_shapely_polygon_feature_utm

# TODO would need to create a utm output to test against
# def test_invalid_get_polygon_buffer():
#     assert Footprint(invalid_geojson_overlap_polygon).get_polygon() == invalid_shapely_overlap_polygon.buffer(0)


def test_invalid_get_polygon_buffer_error():
    assert Footprint(invalid_geojson_overlap_polygon).errors['geometry']['buffer0'] is True


# TODO need a shape that would require a convex hull
# def test_invalid_get_polygon_convex_hull():
#     raise NotImplementedError
