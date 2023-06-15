# -*- coding: utf-8 -*-
"""
Functions for computing the BET areas.
Created on Thu Mar 21 16:24:04 2019

@author: jwmo2, ls604, jrampersad
"""
import os
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib import pyplot as plt
from scipy.interpolate import splev
from scipy.optimize import minimize

from betsi.plotting import create_matrix_plot,regression_diagnostics_plots
from betsi.utils import *
from pprint import pprint
from scipy.interpolate import splrep, pchip_interpolate
matplotlib.use('Qt5Agg')
#matplotlib.use('agg') # do not print plots new Qt windows

##NITROGEN_RADIUS = 1.62E-19
##NITROGEN_MOL_VOL = 44.64117195
AVOGADRO_N = 6.02E+23
## in units of m2
cross_sectional_area = {"N2": 1.62E-19, "Ar": 1.66E-19, "Kr": 2.02E-19, "Xe": 2.32E-19, "CO2": 1.95E-19, "Custom": None}
## in units of mmol/litre or mol/m3
mol_vol = {"N2": 44.64117195, "Ar": 44.642857, "Kr": 44.642857, "Xe": 44.642857, "CO2": 44.642857, "Custom": None}

class BETResult:
    """
    Structure to hold the unfiltered results obtained from running initial BET analysis on
    an isotherm.
    """

    def __init__(self, pressure, q_adsorbed):

        def zero_matrix(dim):
            # Helper function to create a square matrix of dimension dim.
            return np.zeros([dim, dim])

        # Pressure & Q_Adsorbed
        self.pressure = pressure
        self.q_adsorbed = q_adsorbed

        # Apply linearised BET equation
        self.linear_y = (pressure / (q_adsorbed * (1. - pressure)))
        self.rouq_y = q_adsorbed * (1. - pressure)

        # Fit a line to isotherm.
        self.x_range = np.linspace(pressure[0], pressure[len(pressure) -1 ], 10000)
        self.fitted_spline = get_fitted_spline(pressure, q_adsorbed)

        # Number of points in each segment:
        num_points = len(pressure)
        self.point_count = zero_matrix(num_points)

        # Gradients, Intercept and Residual of Linearised BET:
        self.fit_grad = zero_matrix(num_points)
        self.fit_intercept = zero_matrix(num_points)
        self.fit_rsquared = zero_matrix(num_points)

        # 'C' constants and Monolayer loadings:
        self.c = zero_matrix(num_points)
        self.nm = zero_matrix(num_points)

        # Pressure at the Monolayer loading, error and percentage error:
        self.calc_pressure = zero_matrix(num_points)
        self.error = zero_matrix(num_points) + 300
        self.pc_error = zero_matrix(num_points) + 300

        # Identify the Isotherm Knee
        self.knee_index = np.argmax(np.diff(self.rouq_y) < 0)

        # Binary rouquerol `pass` matrices:
        self.rouq1 = zero_matrix(num_points)
        self.rouq2 = zero_matrix(num_points)
        self.rouq3 = zero_matrix(num_points)
        self.rouq4 = zero_matrix(num_points)
        self.rouq5 = zero_matrix(num_points)
        
        #Corresponding pressure matrix
        self.corresponding_pressure = zero_matrix(num_points)
        self.corresponding_pressure_pchip = zero_matrix(num_points)

        # Fill all the matrices
        self._compute_betsi_data(pressure, q_adsorbed)

    def _compute_betsi_data(self, pressure, q_adsorbed):
        """ Computes Monolayer loadings and applies the rouquerel criteria individually to produce a
        dictionary of matrices that can be used in downstream analysis and plotting.

        Args:
            pressure: Array of relative pressure values.
            q_adsorbed: Array of Nitrogen uptake values.

        Returns:
            A Betsi Result Object
        """

        # Fit a line to isotherm.
        fitted_spline = get_fitted_spline(pressure, q_adsorbed)
        fitted_pchip =  get_pchip_interpolation(pressure,q_adsorbed)

        def distance_to_interpolation(_s, _mono):
            # Calculate distance of monolayer loading to fitted spline.
            return (splev(_s, fitted_spline, der=0, ext=0) - _mono) ** 2
        
        def distance_to_pchip(_s,_mono):
        # Create a BET results object:
        
            return (fitted_pchip.__call__(_s,nu=0,extrapolate=None) - _mono) ** 2
        
        
        num_points = len(pressure)

        for i in range(num_points):
            for j in range(i + 1, num_points + 1):

                # Set the number of points
                self.point_count[i, j - 1] = j - i

                # Fit a straight line to points i:j of the linearised equation. Compute C and Nm.
                x = np.concatenate(
                    [np.ones([num_points, 1]), pressure[:, None]], axis=1)
                params, residuals, _, _ = np.linalg.lstsq(
                    x[i:j, :], self.linear_y[i:j], rcond=None)
                if residuals:
                    r2 = 1. - residuals / \
                        (self.linear_y[i:j].size * self.linear_y[i:j].var())
                    self.fit_rsquared[i, j - 1] = r2

                # Set the linearised BET parameters from the fit.
                self.fit_intercept[i, j - 1] = params[0]
                self.fit_grad[i, j - 1] = params[1]
                self.c[i, j - 1] = self.fit_grad[i, j - 1] / \
                    self.fit_intercept[i, j - 1] + 1.
                self.nm[i, j - 1] = 1. / \
                    (self.fit_grad[i, j - 1] + self.fit_intercept[i, j - 1])
        
        for i in range(num_points):
            for j in range(i + 1, num_points):

                # ROUQUEROL CRITERIA 1. vol_adsorbed * (1. - pressure) increases monotonically.
                deltas = np.diff(self.rouq_y[i:(j + 1)])
                if not (deltas < 0).any():
                    self.rouq1[i, j] = 1
                deltas_2 = np.diff(self.linear_y[i:(j+1)])
                if (deltas_2 < 0).any():
                    self.rouq1[i,j]=0

                # ROUQUEROL CRITERIA 2. Resulting C value must be positive.
                if self.c[i, j] <= 0:
                    continue
                self.rouq2[i, j] = 1

                # ROUQUEROL CRITERIA 3. Pressure corresponding to Nm should lie in linear range
                self.calc_pressure[i, j] = 1. / (np.sqrt(self.c[i, j]) + 1)
                opt_res = minimize(fun=distance_to_interpolation,
                                   x0=self.calc_pressure[i, j],
                                   args=(self.nm[i, j]))
                self.corresponding_pressure[i,j] = opt_res.x
                opt_res_pchip = minimize(fun=distance_to_pchip,x0=self.calc_pressure[i, j], args=(self.nm[i, j]))
                self.corresponding_pressure_pchip[i,j] = opt_res_pchip.x
                
                
                if not pressure[i] < self.corresponding_pressure_pchip[i,j] < pressure[j]:
                    continue
                self.rouq3[i, j] = 1

                # ROUQUEROL CRITERIA 4. Relative Pressure should be *close* to P from BET Theory.
                self.error[i, j] = abs(
                    self.corresponding_pressure_pchip[i,j] - self.calc_pressure[i, j])
                self.pc_error[i, j] = (
                    self.error[i, j] / self.corresponding_pressure_pchip[i,j]) * 100.

                # ROUQUEROL CRITERIA 5. Linear region must end at the knee
                if j == self.knee_index:
                    self.rouq5[i, j] = 1

class BETFilterAppliedResults:
    """
    Structure obtained from applying a set of custom filters to a BETResult.

    After initialisation with an initialised BETResult object and set of desired features, the
    BETFilterAppliedResults object contains all data required to produce any plot.
    """

    def __init__(self, bet_result, **kwargs):

        # Transfer all the properties from the original BET calculation
        self.__dict__.update(bet_result.__dict__)
        self.filter_params = kwargs

        # Apply the selected filters in turn
        filter_mask = np.ones_like(bet_result.c)

        if kwargs.get('use_rouq1', True):
            filter_mask = filter_mask * bet_result.rouq1

        if kwargs.get('use_rouq2', True):
            filter_mask = filter_mask * bet_result.rouq2

        if kwargs.get('use_rouq3', True):
            filter_mask = filter_mask * bet_result.rouq3

        if kwargs.get('use_rouq4', True):
            max_perc_error = kwargs.get('max_perc_error', 20)
            filter_mask = filter_mask * (bet_result.pc_error < max_perc_error)

        if kwargs.get('use_rouq5', False):
            filter_mask = filter_mask * bet_result.rouq5
        
        adsorbate = kwargs.get('adsorbate', "N2")
        
        if adsorbate == "Custom":
            cross_sectional_area[adsorbate] = 1.0E-18 * kwargs.get('cross_sectional_area')
            mol_vol[adsorbate] = kwargs.get('molar_volume')

        # Filter results that have less than the minimum points
        min_points = kwargs.get('min_num_pts', 10)
        filter_mask = filter_mask * (bet_result.point_count > min_points)

        # Block out results that have less than the minimum R2
        min_r2 = kwargs.get('min_r2', 0.9)
        filter_mask = filter_mask * (bet_result.fit_rsquared > min_r2)

        ## assert np.sum(filter_mask) != 0, "NO valid areas found"
        self.has_valid_areas = False
        self.original_pressure_data = bet_result.original_pressure_data
        self.original_q_adsorbed_data = bet_result.original_q_adsorbed_data
        self.comments_to_data =  bet_result.comments_to_data
        self.adsorbate = adsorbate
        
        if np.sum(filter_mask) != 0:
            self.has_valid_areas = True
                
            # Compute valid BET areas
            ##self.bet_areas = NITROGEN_RADIUS * AVOGADRO_N * \
            ##    NITROGEN_MOL_VOL * bet_result.nm * 0.000001
            self.bet_areas = cross_sectional_area[adsorbate] * AVOGADRO_N * \
                mol_vol[adsorbate] * bet_result.nm * 0.000001
            self.bet_areas_filtered = self.bet_areas * filter_mask
            self.valid_indices = np.where(self.bet_areas_filtered > 0)
    
            # Define isotherm knee as ending on highest P
            self.list = np.where(self.valid_indices[1] == np.amax(self.valid_indices[1]))
            self.lower = (self.valid_indices[0])[self.list]
            self.upper = (self.valid_indices[1])[self.list]
            self.valid_knee_indices = (self.lower, self.upper)
            self.knee_only_bet_areas_filtered = self.bet_areas * bet_result.rouq5
    
    
            # Define the valid cases
            self.num_valid = len(self.valid_indices[0])
            self.valid_bet_areas = self.bet_areas[self.valid_indices]
            self.valid_pc_errors = bet_result.pc_error[self.valid_indices]
            self.valid_knee_bet_areas = self.bet_areas[self.valid_knee_indices]
            self.valid_knee_pc_errors = bet_result.pc_error[self.valid_knee_indices]
            self.valid_calc_pressures = bet_result.calc_pressure[self.valid_indices]
            self.valid_nm = bet_result.nm[self.valid_indices]
    
            ## New lines added
            ## was needed in the plotting.py file
            self.pc_errors = bet_result.pc_error
    
            # Find min error and corresponding indices
            knee_only_filter = np.zeros([len(bet_result.pressure),len(bet_result.pressure)])
            knee_only_filter[self.valid_knee_indices] = 1
            knee_filter = filter_mask * knee_only_filter
            filtered_pcerrors = bet_result.pc_error + 1000.0 * (1 - filter_mask)
            knee_filtered_pcerrors = bet_result.pc_error + \
                1000.0 * (1 - knee_filter)
            min_i, min_j = np.unravel_index(
                np.argmin(knee_filtered_pcerrors), filtered_pcerrors.shape)
            self.min_i = min_i
            self.min_j = min_j
    
            self.compute_BET_curve()
    
            self.std_area = np.std(self.bet_areas[self.valid_indices])

    def compute_BET_curve(self):
        """Function for computing BET curve. This is separated to a different function to allow custom min_i min_j"""

        # Compute BET curve at min point
        numerator = (self.nm[self.min_i, self.min_j] *
                     self.c[self.min_i, self.min_j] * self.x_range)
        denominator = (1. - self.x_range) + (1. - self.x_range)\
            * (self.c[self.min_i, self.min_j] - 1.) * self.x_range

        with np.errstate(divide='ignore'):
            self.bet_curve = numerator / denominator

        self.min_area = self.bet_areas[self.min_i, self.min_j]

    def find_nearest_idx(self, coords):
        """Finds min_i and min_j for the given monlayer error coordinates
        """
        # find the index bet areas
        betarea_idx = np.abs(self.valid_bet_areas - coords[0]).argmin()
        pcerror_idx = np.abs(self.valid_pc_errors - coords[1]).argmin()

        # get the indices
        min_i = self.valid_indices[0][betarea_idx] #+ 1
        min_j = self.valid_indices[1][pcerror_idx] #+ 1

        self.min_i = min_i
        self.min_j = min_j

        self.compute_BET_curve()

    def export(self, filepath):
        """ Write all relevant information to the directory at filepath.

        """
        filepath = Path(filepath)

        # Write out the filter settings used to get these results.
        with (filepath / 'filter_summary.json').open('w') as fp:
            pprint(self.filter_params, fp)

        # Write out the key results.
        with (filepath / 'results.txt').open('w') as fp:
            print(f"Best area has: ", file=fp)
            print(f"Area: {self.min_area} ", file=fp)
            print(
                f"Total points: {self.point_count[self.min_i, self.min_j]} ", file=fp)
            print(
                f"R-Squared: {self.fit_rsquared[self.min_i, self.min_j]} ", file=fp)
            print(
                f"Linear Gradient: {self.fit_grad[self.min_i, self.min_j]} ", file=fp)
            print(
                f"Intercept: {self.fit_intercept[self.min_i, self.min_j]} ", file=fp)
            print(
                f"C: {self.c[self.min_i, self.min_j]} ", file=fp)
            print(
                f"Monolayer Loading: {self.nm[self.min_i, self.min_j]} ", file=fp)
            print(
                f"Calculated Pressure: {self.calc_pressure[self.min_i, self.min_j]} ", file=fp)
            print(
                f"Read pressure: {self.corresponding_pressure_pchip[self.min_i,self.min_j]} ", file =fp)
            print(
                f"Error: {self.error[self.min_i, self.min_j]} ", file=fp)

        # Write out a set of csv files
        matrices_f = filepath / 'matrices'
        matrices_f.mkdir(exist_ok=True)
        np.savetxt(str(matrices_f / 'point_counts.csv'),
                   self.point_count, delimiter=',', fmt='%i')
        np.savetxt(str(matrices_f / 'rouq1.csv'),
                   self.rouq1, delimiter=',', fmt='%i')
        np.savetxt(str(matrices_f / 'rouq2.csv'),
                   self.rouq2, delimiter=',', fmt='%i')
        np.savetxt(str(matrices_f / 'rouq3.csv'),
                   self.rouq3, delimiter=',', fmt='%i')
        np.savetxt(str(matrices_f / 'rouq4.csv'),
                   self.rouq4, delimiter=',', fmt='%i')
        np.savetxt(str(matrices_f / 'rouq5.csv'),
                   self.rouq5, delimiter=',', fmt='%i')
        np.savetxt(str(matrices_f / 'bet_areas_filtered.csv'),
                   self.bet_areas_filtered, delimiter=',', fmt='%1.3f')
        np.savetxt(str(matrices_f / 'bet_areas.csv'),
                   self.bet_areas, delimiter=',', fmt='%1.3f')
        np.savetxt(str(matrices_f / 'fit_rsquared.csv'),
                   self.fit_rsquared, delimiter=',', fmt='%1.3f')
        np.savetxt(str(matrices_f / 'fit_grad.csv'),
                   self.fit_grad, delimiter=',', fmt='%1.3f')
        np.savetxt(str(matrices_f / 'fit_intercept.csv'),
                   self.fit_intercept, delimiter=',', fmt='%1.3f')
        np.savetxt(str(matrices_f / 'c_value.csv'),
                   self.c, delimiter=',', fmt='%1.3f')
        np.savetxt(str(matrices_f / 'nm.csv'),
                   self.nm, delimiter=',', fmt='%1.3f')
        np.savetxt(str(matrices_f / 'calc_pressure.csv'),
                   self.calc_pressure, delimiter=',', fmt='%1.3f')
        np.savetxt(str(matrices_f / 'error.csv'),
                   self.error, delimiter=',', fmt='%1.3f')
        np.savetxt(str(matrices_f / 'pc_error.csv'),
                   self.pc_error, delimiter=',', fmt='%1.3f')


def analyse_file(input_file, output_dir=None, **kwargs):
    """ Entry point for performing BET analysis on a single named csv file.
    If the output directory does not exist, one is created automatically."""

    if output_dir is None:
        output_dir = Path(os.getcwd() + '/bet_output')

    if isinstance(input_file, str):
        input_file = Path(input_file)

    if isinstance(output_dir, str):
        output_dir = Path(output_dir)

    output_subdir = output_dir / input_file.name
    output_subdir.mkdir(exist_ok=True, parents=True)

    # Compute unfiltered results
    pressure, q_adsorbed, comments_to_data = get_data(input_file=input_file)
    betsi_unfiltered = BETResult(pressure, q_adsorbed)
    betsi_unfiltered.original_pressure_data = pressure
    betsi_unfiltered.original_q_adsorbed_data = q_adsorbed
    betsi_unfiltered.comments_to_data = comments_to_data
    # Apply custom filters:
    betsi_filtered = BETFilterAppliedResults(betsi_unfiltered, **kwargs)

    # Export the results
    betsi_filtered.export(output_subdir)
    
    # Create and save a PDF plot
    # Do not display plots in multiple Qt windows
    with matplotlib.rc_context({'interactive': False}):
        fig = create_matrix_plot(betsi_filtered,kwargs['use_rouq3'],kwargs['use_rouq4'],name=input_file.stem,)
        #fig.tight_layout(pad=0.3, rect=[0, 0, 1, 0.95])
        fig.savefig(
            str(output_subdir / f'{input_file.stem}_combined_plot.pdf'), bbox_inches='tight')
        #plt.tight_layout()
        #plt.show()

        # Create and show Diagnostics plot
        fig_2 = regression_diagnostics_plots(betsi_filtered,name=input_file.stem)
        fig_2.tight_layout(pad=.3, rect=[0,0,1,.95])
        fig_2.savefig(str(output_subdir / f'{input_file.stem}_RD_plots.pdf'))
        #plt.show()

if __name__ == "__main__":
    analyse_file(
        Path(r"/Users/johannesosterrieth/Desktop/q_nu1105.csv"))
