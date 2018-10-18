from vectorattributes.footprint import Footprint
from vectorattributes.dsmcalc import DSMCalc
import numpy as np


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

    Inputs assume that the feature is inside the DSM area and that the feature.

    :param dsm:
    :param feature: A single geojson feature (not a full shapefile)
    """
    NEW_DEFAULT_PARAMS = NEW_DEFAULT_PARAMS

    def __init__(self, dsm, feature, tree_dsm=None):
        self.dsm = dsm
        tree_flag = False
        if tree_dsm:
            self.tree_dsm = tree_dsm
            tree_flag = True
        super().__init__(feature)
        self.DEFAULT_PARAMS.update(NEW_DEFAULT_PARAMS)
        if self.properties['u_id'] in ['ur_02_56_20160908_77545', 'ur_02_56_20160908_77575', 'ur_02_56_20160908_77578',
                                       'ur_02_56_20160908_77570', 'ur_02_56_20160908_77571', 'ur_02_56_20160908_77576',
                                       'ur_02_56_20160908_77577', 'ur_02_56_20160908_77574']:
            print('-------------EXAMPLE FEATURE -------------------------->>>>>>>>>>>>>>>')
            print('inherited footprint errors ', self.footprint_errors)
        self.footprint_errors['dsm_null'] = self.determine_is_null()
        print('after determine is null ', self.footprint_errors)
        self.calculation_errors = error_factory()
        self.footprint_calcs = self.footprint_calculations(tree_flag=tree_flag)
        print('after footprint calcs ', self.footprint_errors)
        self.ground_calcs = self.ground_calculations()
        self.eave_calcs = self.eave_calculations(tree_flag=tree_flag)
        self.roof_calcs = self.roof_calculations(tree_flag=tree_flag)

        # Calculating results
        self.calculations = calculation_factory()
        self.get_elevations()
        self.calculate_pitch()
        self.set_eave_height()
        self.set_roof_height()

        # Validation / Fixing wanky results
        self.check_for_errors()

    def determine_is_null(self):
        footprint = DSMCalc(self.dsm, self.footprint)
        return footprint.errors['dsm_null']

    @staticmethod
    def full_dsm_operations(dsm_calc_obj, test_dist):
        dsm_calc_obj.mask_low_elevations()
        if test_dist is True:
            dsm_calc_obj.comparison_factor()
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

    def ground_calculations(self):
        ground = DSMCalc(self.dsm, self.footprint_ground, height_max=self.footprint_calcs['height_max'])
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
            self.calculations['roof_pitch'] = "steep or high complexity"
        elif self.roof_calcs['std'] > 0.5:
            self.calculations['roof_pitch'] = "moderate"
        else:
            self.calculations['roof_pitch'] = "flat"

    def set_eave_height(self):
        """
        As long as both eave and ground are valid values and eave is not lower than ground, calculate eave height.  If
        any previous conditions are true, set error values and flags.
        """
        eave_elev = self.eave_calcs['elevation']
        ground_elev = self.ground_calcs['elevation']
        if np.isnan(eave_elev) or np.isnan(ground_elev) or eave_elev < ground_elev:
            self.eave_calcs['height'] = np.NaN
            self.calculation_errors['eave_height'] = True
        else:
            self.eave_calcs['height'] = eave_elev - ground_elev

    def set_roof_height(self):
        """
        As long as both roof and ground are valid values and roof is not lower than ground, calculate roof height.  If
        any previous conditions are true, set error values and flags.
        """
        roof_elev = self.roof_calcs['elevation']
        ground_elev = self.ground_calcs['elevation']
        if np.isnan(roof_elev) or np.isnan(ground_elev) or roof_elev < ground_elev:
            self.roof_calcs['height'] = np.NaN
            self.calculation_errors['roof_height'] = True
        else:
            self.roof_calcs['height'] = roof_elev - ground_elev

    def reset_eave_low_roof_error(self, roof_height):
        """
        If eave is above the roof or is nan, reset the eave value depending on if the roof value is below threshold
        (lower than habitable height)
        """
        low_building_threshold = self.DEFAULT_PARAMS['error_thresholds']['low_building']
        if roof_height > low_building_threshold:
            self.eave_calcs['height'] = roof_height - low_building_threshold
            self.calculation_errors['reset_eave_normal_roof'] = True
        else:
            self.eave_calcs['height'] = self.calculations['roof_height']
            self.calculation_errors['reset_eave_low_roof'] = True

    def roof_below_eave_error(self):
        """
        If the eave is below the roof, set the error flag to True
        If eave is an error, reset the eave height based on the height of the roof
        """
        roof_height = self.roof_calcs['height']
        eave_height = self.eave_calcs['height']
        if not roof_height > eave_height:
            self.calculation_errors['eave_above_roof'] = True
            if np.isnan(eave_height):
                self.reset_eave_low_roof_error(roof_height)

    def min_eave_height_error(self):
        min_eave_height = self.DEFAULT_PARAMS['error_thresholds']['min_eave_height']
        low_building_threshold = self.DEFAULT_PARAMS['error_thresholds']['low_building']
        print('eave height: ', self.eave_calcs['height'])
        print('eave_min err before loops ', self.calculation_errors['min_eave'], self.calculation_errors['reset_eave_to_min'])
        if self.eave_calcs['height'] < min_eave_height:
            print('found eave height false; entered loop')
            self.calculation_errors['min_eave'] = True
            if self.roof_calcs['height'] >= (min_eave_height + low_building_threshold):
                self.eave_calcs['height'] = min_eave_height
                self.calculation_errors['reset_eave_to_min'] = True
        print('eave_min ', self.calculation_errors['min_eave'])
        print('reset_eave_to_min ', self.calculation_errors['reset_eave_to_min'])

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

    def check_for_errors(self):
        self.roof_below_eave_error()
        self.min_eave_height_error()
        self.roof_eave_ratio_error()
        self.tallest_building_error()
        self.max_roof_height_error()
        self.min_roof_height_error()

    def output_geojson(self):
        output = {
            'type': 'feature',
            'geometry': self.feature['geometry'],
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
        return output
