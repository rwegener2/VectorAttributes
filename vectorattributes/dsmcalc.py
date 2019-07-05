import shapely.geometry
from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry
from affine import Affine
import rasterio.features
import rasterio.transform
import numpy as np
from collections import Counter
import math


DEFAULT_PARAMS = {
    "dsm_calc": {
        "dsm_nodata": -9999,
        "min_elevation": -415,
        "max_comparison_factor": 6
    }
}


def factory():
    return {
        "all": {
            "dsm_null": False,
            "negative_elevation": False,
            "comparison_factor_exceeded": False
        },
        "find_nulls_only": {
            "dsm_null": False,
            "negative_elevation": False
        }
    }


class DSMCalc(object):
    """
    This class is designed to run the statistical analysis on the input DSM in the area of the vector object.  It takes
    DSM data, masks it to the feature area, removes any abnormally how or high elevations, looks at standard deviation
    of pixels, and runs about a dozen standard statistical operations such as max, min, mean, etc.  Additionally, it
    checks many of these calculated values for errors and flag atypical results in self.errors.

    Optionally, the code can exit early if the 'find_nulls_only' flag is raised.  In this case the process masks the DSM
    data in the area of the provided feature and determines the percent of feature area that is null.  It does not
    continue more analysis after that.

    If null_values_only values should output with: {}
    If all methods are run values should output with: height_max, pixel_count, comparison_factor, min, max, mean, sum,
    std, med, range, mode, minor
    """
    DEFAULT_PARAMS = DEFAULT_PARAMS

    def __init__(self, dsm, footprint, find_nulls_only=False, height_max=np.NaN):
        """
        :param dsm:
        :param footprint: shapely polygon
        """
        self.errors = self.set_default_errors(find_nulls_only)
        self.values = {"tree_masked_dsm": False, "pixel_count": np.NaN, "height_max": height_max}
        if not isinstance(footprint, (BaseGeometry, BaseMultipartGeometry)):
            raise TypeError('DSMCalc input geometry is not a shapely geometry based object')
        self.footprint = self.check_vector_validity(footprint)
        self.dsm = self.check_raster_coverage(dsm, footprint)
        self.dsm_data = self.read_dsm()
        self.masked_dsm = self.mask_dsm()
        self.null_data_error()

    @staticmethod
    def set_default_errors(find_nulls_only):
        default_errors = factory()
        if find_nulls_only is True:
            return default_errors['find_nulls_only']
        else:
            return default_errors['all']

    @staticmethod
    def check_vector_validity(footprint):
        """
        :return: footprint
        """
        if footprint.is_valid is False:
            raise ValueError('Input vector is not valid')
        return footprint

    @staticmethod
    def check_raster_coverage(raster, footprint):
        """
        Ensure that the bbox for the dsm contains the full feature
        """
        dsm_bbox = shapely.geometry.box(*raster.bounds)
        if dsm_bbox.contains(footprint):
            return raster
        else:
            raise ValueError('Footprint not contained in dsm area')

    def get_upper_left_lower_right(self):
        """
        Get pixel coordinates of the geometry's bounding box in relation to the raster
        """
        ul = self.dsm.index(*self.footprint.bounds[0:2])
        lr = self.dsm.index(*self.footprint.bounds[2:4])
        return ul, lr

    def get_window_from_bounds(self):
        """
        Get pixel coordinates of the bounding box and output in bounding box format
        """
        ul, lr = self.get_upper_left_lower_right()
        window = ((lr[0], ul[0] + 1), (ul[1], lr[1] + 1))
        return window

    def read_dsm(self):
        """
        Read in dsm data from the bounding box of footprint
        """
        window = self.get_window_from_bounds()
        elev_data = self.dsm.read(1, window=window)
        return elev_data

    def mask_dsm(self):
        """
        Create a mask of the dsm pixels touching the footprint by rasterizing the footprint values and masking the part
        of the raster data that overlaps with the feature
        """
        ul, lr = self.get_upper_left_lower_right()
        t = self.dsm.transform
        shifted_affine = Affine(t.a, t.b, t.c + ul[1] * t.a, t.d, t.e, t.f + lr[0] * t.e)

        mask = rasterio.features.rasterize(
            [(self.footprint, 0)],
            out_shape=self.dsm_data.shape,
            transform=shifted_affine,
            fill=1,
            all_touched=True,
            dtype=np.uint8)

        masked_dsm = np.ma.array(data=self.dsm_data, mask=mask.astype(bool))
        return masked_dsm

    def null_data_error(self):
        """
        Check if there are more than 5% null values
        """
        dsm_nodata = self.DEFAULT_PARAMS['dsm_calc']['dsm_nodata']
        count_nodata = np.ma.equal(self.masked_dsm, dsm_nodata).sum()
        self.set_pixel_count()
        if self.values['pixel_count'] > 0 and float(count_nodata)/self.values['pixel_count'] >= 0.05:
            self.errors['dsm_null'] = True
        if self.values['pixel_count'] < 1:
            raise ValueError('Footprint area was found to be fully masked')

    def mask_low_elevations(self):
        """
        Mask all elevations below the default 'min_elevation' parameter and set error, if negative elevations exist
        """
        if len(self.masked_dsm[self.masked_dsm <= 0]) > 0:
            self.errors['negative_elevation'] = True
            self.masked_dsm[self.masked_dsm < self.DEFAULT_PARAMS['dsm_calc']['min_elevation']] = np.ma.masked
        self.set_pixel_count()

    def set_pixel_count(self):
        """
        Count number of unmasked pixels
        """
        pixel_count = int(self.masked_dsm.count())
        self.values['pixel_count'] = pixel_count

    def remove_anomalous_roof(self, p_100, p_75):
        # if self.values['pixel_count'] > 1:
        co_array = self.masked_dsm[(self.masked_dsm <= p_100) & (self.masked_dsm >= p_75)]
        height_max = np.median(co_array.compressed())
        self.values['height_max'] = round(float(height_max), 5)

    def comparison_factor_maximum(self, p_100, p_75):
        """
        If the q4r to iqr ratio is higher than the maximum, remove anomalous roof heights
        """
        max_comparison_factor = self.DEFAULT_PARAMS['dsm_calc']['max_comparison_factor']
        if self.values['comparison_factor'] >= max_comparison_factor:
            self.errors['comparison_factor_exceeded'] = True
            self.remove_anomalous_roof(p_100, p_75)

    def comparison_factor(self):
        """
        Calculate the 25th, 75th, and 100th percentile values for the data.  Determine comparison factor between the
        quartile ranges (q4r, iqr).  If calculated comparison factor is greater than a set threshold, this indicates an
        atypical feature on the roof, whose values we then remove.
        """
        if not self.masked_dsm.compressed().size <= 1:
            p_100 = np.percentile(self.masked_dsm.compressed(), 100)
            p_75 = np.percentile(self.masked_dsm.compressed(), 75)
            p_25 = np.percentile(self.masked_dsm.compressed(), 25)

            q4r = p_100 - p_75
            iqr = p_75 - p_25

            # calculate comparison ratio
            self.values['comparison_factor'] = np.NaN
            if q4r > 0 and iqr > 0:
                comparison_factor = round(float((q4r / iqr)), 5)
                if not math.isinf(comparison_factor) or math.isnan(comparison_factor):
                    self.values['comparison_factor'] = comparison_factor
            self.comparison_factor_maximum(p_100, p_75)

    def clip_max_heights(self):
        if not math.isnan(self.values['height_max']):
            self.masked_dsm[self.masked_dsm > self.values['height_max']] = np.ma.masked

    def get_pixel_area(self):
        """
        :return: number of pixels per m^2
        """
        pixel_size_x, pixel_size_y = self.dsm.res
        return 1 / (pixel_size_x * pixel_size_y)

    def calculate_stats(self):
        if self.masked_dsm.compressed().size > 1:
            self.set_pixel_count()
            self.values['min'] = round(float(self.masked_dsm.min()), 5)
            self.values['max'] = round(float(self.masked_dsm.max()), 5)
            self.values['mean'] = round(float(self.masked_dsm.mean()), 5)
            self.values['sum'] = round(float(self.masked_dsm.sum()), 5)
            self.values['std'] = round(float(self.masked_dsm.std()), 5)
            self.values['median'] = round(float(np.median(self.masked_dsm.compressed())), 5)

            self.values['10th_perc'] = np.percentile(self.masked_dsm, 10)
            self.values['25th_perc'] = np.percentile(self.masked_dsm, 25)
            self.values['75th_perc'] = np.percentile(self.masked_dsm, 75)
            self.values['90th_perc'] = np.percentile(self.masked_dsm, 90)

        elif self.masked_dsm.compressed().size == 1:
            self.values['min'] = round(float(self.masked_dsm.compressed()[0]), 5)
            self.values['max'] = round(float(self.masked_dsm.compressed()[0]), 5)
            self.values['mean'] = round(float(self.masked_dsm.compressed()[0]), 5)
            self.values['sum'] = round(float(self.masked_dsm.compressed()[0]), 5)
            self.values['std'] = 0
            self.values['pixel_count'] = 1
            self.values['median'] = round(float(self.masked_dsm.compressed()[0]), 5)
            self.values.update({'10th_perc': np.NaN, '25th_perc': np.NaN, '75th_perc': np.NaN, '90th_perc': np.NaN})

        elif self.masked_dsm.compressed().size == 0:
            self.values['pixel_count'] = 0
            self.values.update({'min': np.NaN, 'max': np.NaN, 'mean': np.NaN, 'sum': np.NaN, 'median': np.NaN,
                                '10th_perc': np.NaN, '25th_perc': np.NaN, '75th_perc': np.NaN, '90th_perc': np.NaN,
                                'std': np.NaN})

        self.values['area'] = round(float(self.footprint.area), 5)
        self.values['coverage'] = round(float(self.values['pixel_count'] / self.values['area'] /
                                              self.get_pixel_area()), 5)
