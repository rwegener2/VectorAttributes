from tests.test_structures import *
from vectorattributes.geojson_check import GeojsonCheck


def test_keys():
    assert GeojsonCheck(valid_geojson_polygon_feature).feature_key_check() is True


def test_keys_missing_one():
    assert GeojsonCheck(no_type_geojson_polygon_feature).feature_key_check() is False


def test_keys_missing_all():
    assert GeojsonCheck(coordinates_only_geojson_polygon_feature).feature_key_check() is False


def test_geom_keys():
    assert GeojsonCheck(valid_geojson_polygon_feature).geometry_key_check() is True


def test_geom_keys_missing_one():
    assert GeojsonCheck(no_coordinates_geojson_polygon_feature).geometry_key_check() is False


def test_geom_keys_missing_all():
    assert GeojsonCheck(empty_geometry_geojson_polygon_feature).geometry_key_check() is False


def test_validate_feature():
    assert GeojsonCheck(valid_geojson_polygon_feature).is_geojson is True


def test_validate_feature_dict_fail():
    assert GeojsonCheck('Guayaquil').is_geojson is False


def test_validate_feature_key_fail():
    assert GeojsonCheck(no_type_geojson_polygon_feature).is_geojson is False


def test_validate_feature_geom_key_fail():
    assert GeojsonCheck(no_coordinates_geojson_polygon_feature).is_geojson is False

