from vectorattributes.dsmfootprint import DSMFootprint
import rasterio
import fiona
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import shape as get_shape
import tqdm
import time


start = time.time()

# TODO life together with this testing script
shapefile_1 = '17JUL24003152_056860049110_17JUL24003153_056864883110'  # 155 features - change in DSM?  Minor error only
shapefile_2 = '18FEB15003345_057618369050_18FEB15003346_057618370050'  # 269 features - 1 shape ev_elev incorrect
# feature id properties  ur_08_55_20170217_181143 - Warning: converting masked element to nan [min, max, mean, sum, std]
shapefile_3 = '17FEB12002749_056283380180_17FEB12002748_056283382180'  # 11,553 features
shapefile_4 = '16APR06014236_055878310190_16APR06014237_055894731030'  # 44 features  # GOOD TO GO @ 1%

shapefile = shapefile_4
working_directory = '/Users/rachelwegener/repos/test_data/s3_tests/'
footprint_filepath = working_directory + 'buildings/' + shapefile + '.shp'
dsm_filepath = working_directory + 'dsm/' + shapefile + '.tif'
tree_dsm_filepath = working_directory + 'tree_masked_dsm/' + shapefile + '.tif'
dtm_filepath = working_directory + 'dtm/' + shapefile + '.tif'

output_feature = {
    'type': 'FeatureCollection',
    'features': []
}

with fiona.open(footprint_filepath, 'r') as bldg_footprints, \
        rasterio.open(dsm_filepath, 'r') as dsm, \
        rasterio.open(dtm_filepath, 'r') as dtm, \
        rasterio.open(tree_dsm_filepath, 'r') as tree_dsm:
    for feature in tqdm.tqdm(bldg_footprints):
    # for feature in bldg_footprints:
        processed_data = DSMFootprint(feature, bldg_footprints.crs, dsm, dsm.crs.to_dict(), tree_dsm=tree_dsm,
                                      tree_dsm_crs=tree_dsm.crs.to_dict(), dem=dtm, dem_crs=dtm.crs.to_dict(), )
        geojson = processed_data.output_geojson()
        output_feature['features'].append(geojson)

# START VALIDATION
control_filepath = working_directory + 'height_attributed_buildings/' + shapefile + '.shp'

# create index for refactored geojson outputs
output_ids = []
for obj in output_feature['features']:
    output_ids.append(obj['properties']['original_properties']['u_id'])

# set up column name mapping
# problem children: roof shape 'rf_shp': ['roof', 'pitch']
testing_attributes = {'rf_max': ['roof', 'max'], 'rf_min': ['roof', 'min'],
                      'rf_med': ['roof', 'median'], 'rf_std': ['roof', 'std'], 'rf_height': ['roof', 'height'],
                      'ev_max': ['eave', 'max'], 'ev_min': ['eave', 'min'], 'ev_med': ['eave', 'median'],
                      'ev_std': ['eave', 'std'], 'ev_height': ['eave', 'height'], 'gnd_max': ['ground', 'max'],
                      'gnd_min': ['ground', 'min'], 'gnd_med': ['ground', 'median'], 'gnd_std': ['ground', 'std'],
                      'rf_count': ['roof', 'pixel_count'], 'rf_minor': ['roof', 'minor'], 'rf_sum': ['roof', 'sum'],
                      'rf_range': ['roof', 'range'], 'rf_mean': ['roof', 'mean'],
                      'rf_area': ['roof', 'area'], 'rf_cov': ['roof', 'coverage'], 'ev_count': ['eave', 'pixel_count'],
                      'ev_minor': ['eave', 'minor'], 'ev_sum': ['eave', 'sum'],
                      'ev_range': ['eave', 'range'], 'ev_mean': ['eave', 'mean'], 'ev_area': ['eave', 'area'],
                      'ev_cov': ['eave', 'coverage'], 'gnd_count': ['ground', 'pixel_count'], 'gnd_minor': ['ground', 'minor'],
                      'gnd_sum': ['ground', 'sum'], 'gnd_range': ['ground', 'range'],
                      'gnd_mean': ['ground', 'mean'], 'gnd_area': ['ground', 'area'], 'gnd_cov': ['ground', 'coverage'],
                      'gnd_elev': ['ground', 'elevation'], 'ev_elev': ['eave', 'elevation'], 'rf_elev': ['roof', 'elevation'],
                      'rf_mod': ['roof', 'mode'], 'gnd_mod': ['ground', 'mode'], 'ev_mod': ['eave', 'mode']}

# for error checking
# couldn't find roof_eave_ratio
testing_errors = {'min_ev_er': ['calculated_properties', 'min_eave'],
                  'min_rf_er': ['calculated_properties', 'min_roof_height'],
                  'ev_gtr_er': ['calculated_properties', 'eave_above_roof'],
                  'e_to_p_er': ['calculated_properties', 'roof_eave_ratio'],
                  'elt_z_er': ['footprint', 'negative_elevation'],
                  'gd_gtr_er': ['calculated_properties', 'roof_height'],
                  'gd_gte_er': ['calculated_properties', 'eave_height'],
                  'evtolrf_er': ['calculated_properties', 'reset_eave_low_roof'],
                  'evtorf_er': ['calculated_properties', 'reset_eave_normal_roof'],
                  'evtomn_er': ['calculated_properties', 'reset_eave_to_min'],
                  'rf_elev_er': ['calculated_properties', 'roof_elevation'],
                  'rf_hgt_er': ['calculated_properties', 'max_roof_height'],
                  'q4_rng_er': ['footprint', 'comparison_factor_exceeded'], 'dsm_null': ['footprint', 'dsm_null']}
# roof pitch
pitch = {2: 'steep or high complexity', 1: 'moderate', 0: 'flat'}

# loop through Dan's output and check that the corresponding output exists in refactored geojson
dans_features = gpd.read_file(control_filepath)
tracking_errors = pd.DataFrame()
for index, row in tqdm.tqdm(dans_features.iterrows()):
# for index, row in dans_features.iterrows():
    u_id = row['u_id']
    refactored_feature = output_feature['features'][output_ids.index(u_id)]

    # test calculated values
    for attr, ref_attr in testing_attributes.items():
        refactored_attribute = refactored_feature['properties']['calculated_properties'][ref_attr[0]][ref_attr[1]]
        if np.isnan(refactored_attribute):
            if row[attr] != -9999.0:
                print(u_id, '<<<<< ----- >>>>>')
                print('found falsehood', attr)
                print('    Dan: ', row[attr])
                print('    New: ', refactored_attribute)
                tracking_errors = tracking_errors.append({ref_attr[0]+'-'+ref_attr[1]: 1}, ignore_index=True)
        elif not np.isclose(row[attr], refactored_attribute, rtol=0.03):
            if attr in ['ev_std', 'rf_std', 'gnd_std']:
                if not np.isclose(row[attr], refactored_attribute, rtol=0.15):
                    print('found standard dev falsehood')
                    tracking_errors = tracking_errors.append({ref_attr[0] + '-' + ref_attr[1]: 1}, ignore_index=True)
            else:
                print(u_id, '<<<<< --??-??-- >>>>>')
                print('found falsehood', attr)
                print('    Dan: ', row[attr])
                # print('  eave height/roof height ', row['ev_height'], row['rf_height'])
                # print('    Dan eave count: ', row['ev_count'])
                # print('    Dan roof count: ', row['rf_count'])
                print('    New: ', refactored_attribute)
                # print('  eave height/roof height ', refactored_feature['properties']['calculated_properties']['eave']['height'],
                #       refactored_feature['properties']['calculated_properties']['roof']['height'])
                # print('    New count: ', refactored_feature['properties']['calculated_properties']['eave'])
                # print('    New count: ', refactored_feature['properties']['calculated_properties']['roof'])
                tracking_errors = tracking_errors.append({ref_attr[0]+'-'+ref_attr[1]: 1}, ignore_index=True)

    # test geometry
    # if not row['geometry'] == get_shape(refactored_feature['geometry']):
    #     print('geometry falsehood')
    #     tracking_errors = tracking_errors.append({'geometry': 1}, ignore_index=True)

    # test errors
    for err, ref_err in testing_errors.items():
        refactored_error = refactored_feature['properties']['errors'][ref_err[0]][ref_err[1]]
        if not row[err] == refactored_error:
            print(u_id, '<<<<< ----- >>>>>')
            print('found error falsehood', err)
            print('    Dan: ', row[err])
            print('    New: ', refactored_error)
            tracking_errors = tracking_errors.append({ref_err[1]: 1}, ignore_index=True)

    # test roof pitch
    if pitch[row['rf_shp']] != refactored_feature['properties']['calculated_properties']['roof']['pitch']:
        print(u_id, '<<<<<<< ---- >>>>>>>')
        print('found pitch error')
        print('    Dan: ', row['rf_shp'])
        print('    New: ', refactored_feature['properties']['calculated_properties']['roof']['pitch'])

    # check clip_val
    if np.isnan(refactored_feature['properties']['calculated_properties']['height_max']):
        if not row['clip_val'] == -9999.0:
            print('clip_val error')
            print('Dan : ', row['clip_val'])
            print('New: ', refactored_feature['properties']['calculated_properties']['height_max'])
    elif not np.isclose(refactored_feature['properties']['calculated_properties']['height_max'], row['clip_val'],
                        rtol=0.05):
        print('clip_val error')
        print('Dan : ', row['clip_val'])
        print('New: ', refactored_feature['properties']['calculated_properties']['height_max'])

# view all
final_error_overview = pd.DataFrame(tracking_errors.sum(axis=0, skipna=True), columns=['counts'])
final_error_overview['percentages'] = tracking_errors.sum(axis=0, skipna=True) / len(dans_features) * 100
print(final_error_overview)
print('Script ran for {} minutes'.format((time.time()-start)/60))

# Creating the full dataframe
# all_shape_deviations = pd.DataFrame()
# all_shape_deviations = all_shape_deviations.append(tracking_errors.sum(axis=0, skipna=True), ignore_index=True)
# all_shape_deviations = all_shape_deviations.append(tracking_errors.sum(axis=0, skipna=True) / len(dans_features), ignore_index=True)
