from vectorattributes.footprint import Footprint
from vectorattributes.dsmcalc import DSMCalc
import numpy as np
from vectorattributes.projection import reproject
from shapely.geometry import mapping as to_json
from shapely.geometry import shape as get_shape


NEW_DEFAULT_PARAMS = {
    "error_thresholds": {
        "low_building": 0.5,
        "min_eave_height": 2.5,
        "max_eave_roof_ratio": 2,
        "max_roof_elevation": 2155,
        "max_roof_height": 999999
    }
}


def error_factory():
    """
    :return: dictionary holding default errors for the calculated properties
    """
    return {
        "roof_height": False,
        "eave_height": False,
        "eave_above_roof": False,
        "reset_eave_normal_roof": False,
        "reset_eave_low_roof": False,
        "min_eave": False,
        "reset_eave_to_min": False,
        "reset_eave_ratio": False,
        "roof_elevation": False,
        "max_roof_height": False,
        "min_roof_height": False,
        "roof_eave_ratio": False
    }


def calculation_factory():
    """
    :return: dictionary holding default values for the calculated properties
    """
    return {
        "area": {
            "ground": np.NaN,
            "eave": np.NaN,
            "roof": np.NaN
        },
        "elevation": {
            "ground": np.NaN,
            "eave": np.NaN,
            "roof": np.NaN
        },
        "roof_pitch": np.NaN,
        "eave_height": np.NaN,
        "roof_height": np.NaN
    }


class DSMFootprint(Footprint):
    """
    This class runs the DSMCalc class on the footprints created in the Footprint class and them compares the outputs
    to flag oddities in the data or fix inconsistent values

    :param feature: A single geojson feature (not a full shapefile)
    :param feature_crs:
    :param dsm:
    :param dsm_crs:
    :param tree_dsm:
    :param tree_dsm_crs:
    :param dem:
    :param dem_crs:
    """
    NEW_DEFAULT_PARAMS = NEW_DEFAULT_PARAMS

    def __init__(self, feature, feature_crs, dsm, dsm_crs, tree_dsm=None, tree_dsm_crs=None, dem=None, dem_crs=None):
        # Setting all the initial variables
        self.dsm = dsm
        self.dsm_crs = self.crs_isvalid(dsm_crs)
        self.input_feature_crs = self.crs_isvalid(feature_crs)
        # TODO these logic statements probably shouldn't be here
        # TODO Jon - how do you feel about a class that has some attributes only under certain circumstances
        tree_flag = False
        if tree_dsm:
            self.tree_dsm = tree_dsm
            self.tree_dsm_crs = self.crs_isvalid(tree_dsm_crs)
            tree_flag = True
            if self.tree_dsm_crs != self.dsm_crs:
                raise ValueError('Tree masked dsm crs must match not-masked dsm crs')
        # set the dem
        self.dem = dem
        self.dem_crs = self.crs_isvalid(dem_crs)
        if self.dem_crs is not None and self.dem_crs != self.dsm_crs:
            raise ValueError('dem crs must match not-masked dsm crs')
        # set feature crs
        if self.input_feature_crs != self.dsm_crs:
            feature = self.reproject_footprint(feature, self.input_feature_crs, self.dsm_crs)
        super().__init__(feature, dsm_crs)
        self.DEFAULT_PARAMS.update(NEW_DEFAULT_PARAMS)

        # Calculations round 1
        self.footprint_errors['dsm_null'] = self.determine_is_null()
        self.calculation_errors = error_factory()
        self.footprint_calcs = self.footprint_calculations(tree_flag=tree_flag)
        self.ground_calcs = self.ground_calculations()
        self.eave_calcs = self.eave_calculations(tree_flag=tree_flag)
        self.roof_calcs = self.roof_calculations(tree_flag=tree_flag)

        # Calculations round 2
        self.calculations = calculation_factory()
        self.get_elevations()
        self.calculate_pitch()
        self.set_eave_height()
        self.set_roof_height()

        # Validation / Fixing wanky results
        self.check_for_errors()

    # I took out crs_isvalid here because I think it should inherit, if something goes wanky perhaps repaste it here

    @staticmethod
    def reproject_footprint(feature, feature_crs, dsm_crs):
        footprint_reproj = reproject(get_shape(feature['geometry']), from_proj=feature_crs, to_proj=dsm_crs)
        feature['geometry'] = to_json(footprint_reproj)
        return feature

    def determine_is_null(self):
        footprint = DSMCalc(self.dsm, self.footprint)
        return footprint.errors['dsm_null']

    @staticmethod
    def full_dsm_operations(dsm_calc_obj, test_dist):
        dsm_calc_obj.mask_low_elevations()
        if test_dist is True:
            dsm_calc_obj.comparison_factor()
        dsm_calc_obj.clip_max_heights()
        dsm_calc_obj.calculate_stats()
        return dsm_calc_obj

    def footprint_calculations(self, tree_flag):
        if tree_flag is True:
            footprint = DSMCalc(self.tree_dsm, self.footprint)
            footprint.values["tree_masked_dsm"] = True
        else:
            footprint = DSMCalc(self.dsm, self.footprint)
        self.full_dsm_operations(footprint, test_dist=True)
        self.footprint_errors.update({'negative_elevation': footprint.errors['negative_elevation'],
                                      'comparison_factor_exceeded': footprint.errors['comparison_factor_exceeded']})
        return footprint.values

    def set_height_model(self):
        # TODO add flag for use of dem
        if self.dem:
            return self.dem
        return self.dsm

    def ground_calculations(self):
        height_model = self.set_height_model()
        ground = DSMCalc(height_model, self.footprint_ground, height_max=self.footprint_calcs['height_max'])
        self.full_dsm_operations(ground, test_dist=False)
        return ground.values

    def roof_calculations(self, tree_flag):
        if tree_flag:
            roof = DSMCalc(self.tree_dsm, self.footprint_roof, height_max=self.footprint_calcs['height_max'])
            roof.values["tree_masked_dsm"] = True
        else:
            roof = DSMCalc(self.dsm, self.footprint_roof, height_max=self.footprint_calcs['height_max'])
        self.full_dsm_operations(roof, test_dist=False)
        return roof.values

    def eave_calculations(self, tree_flag):
        if tree_flag:
            eave = DSMCalc(self.tree_dsm, self.footprint_eave, height_max=self.footprint_calcs['height_max'])
            eave.values["tree_masked_dsm"] = True
        else:
            eave = DSMCalc(self.dsm, self.footprint_eave, height_max=self.footprint_calcs['height_max'])
        self.full_dsm_operations(eave, test_dist=False)
        return eave.values

    def get_elevations(self):
        self.ground_calcs.update({'elevation': self.ground_calcs['min']})
        self.roof_calcs.update({'elevation': self.roof_calcs['max']})
        self.eave_calcs.update({'elevation': self.eave_calcs['median']})

    def calculate_pitch(self):
        if self.roof_calcs['std'] > 1.5:
            self.roof_calcs.update({"pitch": "steep or high complexity"})
        elif self.roof_calcs['std'] > 0.5:
            self.roof_calcs.update({"pitch": "moderate"})
        else:
            self.roof_calcs.update({"pitch": "flat"})

    def set_eave_height(self):
        """
        As long as both eave and ground are valid values and eave is not lower than ground, calculate eave height.  If
        any previous conditions are true, set error values and flags.
        """
        # if not np.isnan(self.roof_calcs['elevation'])
        eave_elev = self.eave_calcs['elevation']
        ground_elev = self.ground_calcs['elevation']
        # TODO is this the logic we want to be using?  It matches Dans right now
        if not np.isnan(self.roof_calcs['elevation']):
            if not eave_elev >= ground_elev:
                self.eave_calcs['height'] = np.NaN
                self.calculation_errors['eave_height'] = True
            else:
                self.eave_calcs['height'] = eave_elev - ground_elev
        else:
            self.eave_calcs['height'] = np.NaN

    def set_roof_height(self):
        """
        As long as both roof and ground are valid values and roof is not lower than ground, calculate roof height.  If
        any previous conditions are true, set error values and flags.
        """
        roof_elev = self.roof_calcs['elevation']
        ground_elev = self.ground_calcs['elevation']
        # TODO is this the logic we want to be using?  It matches Dans right now
        if not np.isnan(roof_elev) and not np.isnan(ground_elev):
            if roof_elev < ground_elev:
                self.roof_calcs['height'] = np.NaN
                self.calculation_errors['roof_height'] = True
            else:
                self.roof_calcs['height'] = roof_elev - ground_elev
        else:
            self.roof_calcs['height'] = np.NaN

    def roof_below_eave_error(self):
        """
        Fixing the roof height, only if there is a problem with it (eave elev is nan or roof is below eave)
        If the eave is below the roof, set the error flag to True
        If eave is an error, reset the eave height based on the height of the roof
        """
        # TODO is this the logic we want to be using?  It matches Dans right now
        if not np.isnan(self.roof_calcs['elevation']) and not np.isnan(self.ground_calcs['elevation']):
            roof_height = self.roof_calcs['height']
            eave_height = self.eave_calcs['height']
            if roof_height < eave_height:
                self.calculation_errors['eave_above_roof'] = True
            if roof_height < eave_height or np.isnan(self.eave_calcs['elevation']):
                self.reset_eave_low_roof_error(roof_height)

    def reset_eave_low_roof_error(self, roof_height):
        """
        If eave is above the roof or is nan, reset the eave value depending on if the roof value is below threshold
        (lower than habitable height)
        """
        low_building_threshold = self.DEFAULT_PARAMS['error_thresholds']['low_building']
        if roof_height > low_building_threshold:
            self.eave_calcs['height'] = roof_height - low_building_threshold
            self.calculation_errors['reset_eave_low_roof'] = True
        else:
            self.eave_calcs['height'] = self.roof_calcs['height']
            self.calculation_errors['reset_eave_normal_roof'] = True

    def min_eave_height_error(self):
        min_eave_height = self.DEFAULT_PARAMS['error_thresholds']['min_eave_height']
        low_building_threshold = self.DEFAULT_PARAMS['error_thresholds']['low_building']
        if not self.eave_calcs['height'] >= min_eave_height:
            self.calculation_errors['min_eave'] = True
            if self.roof_calcs['height'] >= (min_eave_height + low_building_threshold):
                self.eave_calcs['height'] = min_eave_height
                self.calculation_errors['reset_eave_to_min'] = True

    def roof_eave_ratio_error(self):
        max_eave_roof_ratio = self.DEFAULT_PARAMS['error_thresholds']['max_eave_roof_ratio']
        if (self.roof_calcs['height'] / self.eave_calcs['height']) > max_eave_roof_ratio:
            self.calculation_errors['roof_eave_ratio'] = True

    def tallest_building_error(self):
        if self.roof_calcs['elevation'] > self.DEFAULT_PARAMS['error_thresholds']['max_roof_elevation']:
            self.calculation_errors['roof_elevation'] = True

    def max_roof_height_error(self):
        if self.roof_calcs['height'] > self.DEFAULT_PARAMS['error_thresholds']['max_roof_height']:
            self.calculation_errors['max_roof_height'] = True

    def min_roof_height_error(self):
        if self.roof_calcs['height'] < (self.DEFAULT_PARAMS['error_thresholds']['min_eave_height'] +
                                        self.DEFAULT_PARAMS['error_thresholds']['low_building']):
            self.calculation_errors['min_roof_height'] = True
        elif np.isnan(self.roof_calcs['height']):
            self.calculation_errors['min_roof_height'] = True

    def check_for_errors(self):
        self.roof_below_eave_error()
        self.min_eave_height_error()
        self.roof_eave_ratio_error()
        self.tallest_building_error()
        self.max_roof_height_error()
        self.min_roof_height_error()

    def output_geojson(self):
        feature4326 = self.feature
        if self.fprint_crs != 'epsg:4326':
            footprint_reproj = reproject(self.footprint, from_proj=self.fprint_crs, to_proj='epsg:4326')
            feature4326['geometry'] = to_json(footprint_reproj)
        return {
            'type': 'feature',
            'geometry': feature4326['geometry'],
            'properties': {
                'original_properties': self.properties,
                'calculated_properties': {
                    'ground': self.ground_calcs,
                    'eave': self.eave_calcs,
                    'roof': self.roof_calcs,
                    'height_max': self.footprint_calcs['height_max']
                },
                'errors': {
                    'footprint': self.footprint_errors,
                    'calculated_properties': self.calculation_errors
                }
            }}
