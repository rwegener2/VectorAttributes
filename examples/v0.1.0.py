from vectorattributes.dsmfootprint import DSMFootprint
import rasterio
import fiona
import json


dsm_filepath = '/Users/rachelwegener/repos/test_data/SoMADSMFootprints/SoMa_DSM.tif'
footprint_filepath = '/Users/rachelwegener/repos/test_data/SoMADSMFootprints/SoMA_building_central/SoMA_building_central.shp'

shapefile_1 = '17JUL24003152_056860049110_17JUL24003153_056864883110'
shapefile_2 = '18FEB15003345_057618369050_18FEB15003346_057618370050'
shapefile_3 = '17FEB12002749_056283380180_17FEB12002748_056283382180'
shapefile_4 = '16APR06014236_055878310190_16APR06014237_055894731030'
working_directory = '/Users/rachelwegener/repos/test_data/s3_tests/'

shapefile = shapefile_1

footprint_filepath = working_directory + 'buildings/' + shapefile + '.shp'
dsm_filepath = working_directory + 'dsm/' + shapefile + '.tif'

output_feature = {
    'type': 'FeatureCollection',
    'features': []
}

with fiona.open(footprint_filepath, 'r') as bldg_footprints, \
        rasterio.open(dsm_filepath, 'r') as dsm:
    for feature in bldg_footprints:
        processed_data = DSMFootprint(feature, bldg_footprints.crs, dsm, dsm.crs.to_dict())
        geojson = processed_data.output_geojson()
        output_feature['features'].append(geojson)

output_name = 'height_attributed_feature.json'
output_file = '/Users/rachelwegener/repos/test_data/AustrailaDSMFootprints/' + output_name

with open(output_file, 'w') as out_file:
    json.dump(output_feature, out_file, indent=4)
