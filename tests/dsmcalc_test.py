from vectorattributes.dsmcalc import DSMCalc
import pytest
from tests.test_structures import *
import rasterio
import os
from vectorattributes.projection import *
from vectorattributes.footprint import Footprint

valid_shapely_polygon_feature = get_shape(valid_geojson_polygon_feature['geometry'])
valid_shapely_polygon_feature_wgs = get_shape(valid_geojson_polygon_feature_wgs['geometry'])
valid_shapely_polygon_feature_utm = convert_4326_to_utm(valid_shapely_polygon_feature)
valid_shapely_polygon_feature_ocean = get_shape(valid_geojson_polygon_feature_ocean['geometry'])
invalid_shapely_overlap_polygon = get_shape(invalid_geojson_overlap_polygon['geometry'])

repo_location = os.path.dirname(__file__)
dsm = rasterio.open(repo_location + '/test_data/SoMa_DSM.tif')
masked_dsm = np.load(repo_location + '/test_data/masked_dsm_SoMa')

# TODO cannot test -- rasterio Affine has broken pytest


@pytest.fixture
def rounded_utm():
    """ Returns a Footprint containing a WGS polygon which was converted to UTM by default and rounded"""
    calculations = DSMCalc(dsm, valid_shapely_polygon_feature_wgs)
    calculations.footprint = calculations.check_vector_validity(calculations.footprint)
    rounded_output = round_shapely_object(calculations.footprint)
    calculations.footprint = rounded_output
    return calculations


@pytest.fixture
def footprint():
    obj = Footprint(valid_geojson_polygon_feature)
    return obj.footprint


def test_improper_footprint_input_type():
    with pytest.raises(TypeError):
        DSMCalc(dsm, valid_geojson_polygon_feature)


def test_invalid_polygon_input():
    with pytest.raises(ValueError):
        DSMCalc(dsm, invalid_shapely_overlap_polygon)


# def test_valid_utm_input():
#     """
#     check_vector_validity
#     """
#     calculations = DSMCalc(dsm, valid_shapely_polygon_feature_utm)
#     assert calculations.footprint == valid_shapely_polygon_feature_utm
#
#
# def test_dsm_complete_footprint_coverage():
#     """
#     check_raster_coverage
#     """
#     calculations = DSMCalc(dsm, valid_shapely_polygon_feature_utm)
#     assert calculations.check_raster_coverage(dsm) == dsm
#
#
# def test_dsm_incomplete_footprint_coverage():
#     """
#     check_raster_coverage
#     """
#     with pytest.raises(ValueError):
#         assert DSMCalc(dsm, valid_shapely_polygon_feature_ocean)
#
#
# def test_pixel_bounding_box():
#     """
#     get_upper_left_lower_right
#     """
#     calculations = DSMCalc(dsm, valid_shapely_polygon_feature)
#     assert calculations.get_upper_left_lower_right() == ((5392, 3004), (5326, 3032))
#
#
# def test_window():
#     """
#     get_window_from_bounds
#     """
#     calculations = DSMCalc(dsm, valid_shapely_polygon_feature, is_utm=False)
#     assert calculations.get_window_from_bounds() == ((5326, 5393), (3004, 3033))
#
#
# def test_read_dsm():
#     calculations = DSMCalc(dsm, valid_shapely_polygon_feature, is_utm=False)
#     elev_data = dsm.read(1, window=((5326, 5393), (3004, 3033)))
#     assert np.array_equal(calculations.read_dsm(), elev_data) is True
# # TODO not a good test -- same code as function
#
#
# # def test_mask_dsm():
# #     calculations = DSMCalc(dsm, valid_shapely_polygon_feature, is_utm=False)
# #     assert calculations.masked_dsm == masked_dsm
# #
# def test_null_error():
#     dsm = rasterio.open('/Users/rachelwegener/repos/height-attributes/test_data/SoMa_DSM.tif')
#     fprint_obj = Footprint(valid_geojson_polygon_feature)
#     dsm_calc = DSMCalc(dsm, fprint_obj.footprint)
#     dsm_calc.null_data_error()
#     assert dsm_calc.errors['dsm_null'] is False
#
# def test_neg_elev():
#     dsm = rasterio.open('/Users/rachelwegener/repos/height-attributes/test_data/SoMa_DSM.tif')
#     fprint_obj = Footprint(valid_geojson_polygon_feature)
#     dsm_calc = DSMCalc(dsm, fprint_obj.footprint)
#     dsm_calc.mask_low_elevations()
#     assert dsm_calc.errors['negative_elevation'] is False
#
# def test_neg_elev():
#     dsm = rasterio.open('/Users/rachelwegener/repos/height-attributes/test_data/SoMa_DSM.tif')
#     fprint_obj = Footprint(valid_geojson_polygon_feature)
#     dsm_calc = DSMCalc(dsm, fprint_obj.footprint)
#     dsm_calc.pixel_count()
#     assert dsm_calc.values['pixel_count'] is False
#
#
# def test_neg_elev():
#     dsm = rasterio.open('/Users/rachelwegener/repos/height-attributes/test_data/SoMa_DSM.tif')
#     fprint_obj = Footprint(valid_geojson_polygon_feature)
#     dsm_calc = DSMCalc(dsm, fprint_obj.footprint)
#     dsm_calc.comparison_factor()
#     assert dsm_calc.values['comparison_factor'] == 2.53
#     assert dsm_calc.errors['comparison_factor_exceeded'] == False

