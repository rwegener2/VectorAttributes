"""
Create:
test structures (geojson and shapely) for all geometry types
investigate invalid polygons and create geojson example of each
Notes:
    sometimes properties dicts are OrderedDicts (NC Municipalities)
"""
from collections import OrderedDict
import numpy as np
from shapely.geometry import mapping, shape as get_shape


def round_shapely_object(shapely_obj):
    raw = mapping(shapely_obj)
    rounded_coordinates = []
    for float_point in np.round(np.array(raw['coordinates'][0]), 0):
        rounded_coordinates.append(tuple([int(float_zero) for float_zero in float_point]))
    raw['coordinates'] = (tuple(rounded_coordinates),)
    rounded = get_shape(raw)
    return rounded


# not used so far
valid_geojson_point_feature = {
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [125.6, 10.1]
  },
  "properties": {
    "name": "Dinagat Islands"
  }
}

valid_geojson_polygon_feature = {
    'properties': OrderedDict([("name", "Dahlia")]),
    'type': 'Feature',
    'id': '0',
    'geometry': {
        'coordinates': [[(-122.4103173469268, 37.78337247419125), (-122.4104206420338, 37.7833590750075),
                         (-122.4104664105675, 37.78360478527359), (-122.4104739356278, 37.78364477503958),
                         (-122.4103759761863, 37.78365638609612), (-122.4103173469268, 37.78337247419125)]],
        'crs': {'init': 'epsg:4326'},
        'type': 'Polygon'}
}

valid_geojson_polygon_feature_wgs = {
    'properties': OrderedDict([("name", "Yerba Buena Gardens")]),
    'type': 'Feature',
    'geometry': {
        'coordinates': [[(-122.40161, 37.78465), (-122.40239, 37.78397), (-122.40340, 37.78504), (-122.40269, 37.78559),
                        (-122.40161, 37.78465)]],
        'crs': {'init': 'epsg:4326'},
        'type': 'Polygon'}
}

valid_geojson_polygon_feature_utm = {
    'properties': OrderedDict([("name", "Yerba Buena Gardens")]),
    'type': 'Feature',
    'geometry': {
        'coordinates': [[(552691, 4182091), (552622, 4182015), (552533, 4182133), (552595, 4182194),
                          (552691, 4182091)]],
        'crs': {'init': 'epsg:32610'},
        'type': 'Polygon'}
}

valid_geojson_polygon_feature_ocean = {
    'properties': OrderedDict([("name", "Titanic")]),
    'type': 'Feature',
    'id': '0',
    'geometry': {
        'coordinates': [[(-49.948253, 41.726931), (-49.948250, 41.726931),
                         (-49.948250, 41.726929), (-49.948253, 41.726929),
                         (-49.948253, 41.726931)]],
        'crs': {'init': 'epsg:4326'},
        'type': 'Polygon'}
}

no_type_geojson_polygon_feature = {
    'properties': OrderedDict([("name", "Dahlia")]),
    'geometry': {
        'coordinates': [[(-122.4103173469268, 37.78337247419125), (-122.41042064203376, 37.7833590750075),
                         (-122.41046641056752, 37.78360478527359), (-122.41047393562782, 37.783644775039576),
                         (-122.4103759761863, 37.78365638609612), (-122.4103173469268, 37.78337247419125)]],
        'type': 'Polygon'}
}

coordinates_only_geojson_polygon_feature = {
    'coordinates': [[(-122.4103173469268, 37.78337247419125), (-122.41042064203376, 37.7833590750075),
                     (-122.41046641056752, 37.78360478527359), (-122.41047393562782, 37.783644775039576),
                     (-122.4103759761863, 37.78365638609612), (-122.4103173469268, 37.78337247419125)]]
}

no_coordinates_geojson_polygon_feature = {
    'properties': OrderedDict([("name", "Dahlia")]),
    'geometry': {
        'type': 'Polygon'}
}

empty_geometry_geojson_polygon_feature = {
    'properties': OrderedDict([("name", "Dahlia")]),
    'geometry': {
    }
}

invalid_geojson_overlap_polygon = {
    'properties': OrderedDict([("name", "Figure Eight"), ("notes", "fixed with buffer zero")]),
    'type': 'Feature',
    'geometry': {
        'coordinates': [[(-122.000, 37.00), (-122.500, 37.00),
                         (-122.000, 36.50), (-122.500, 36.50)]],
        'crs': {'init': 'epsg:4326'},
        'type': 'Polygon'}
}
