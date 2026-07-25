"""Reproducing the CMB acoustic peak-height dependence on the CDM density."""

__version__ = "0.1.0"

from .peaks import Peak, find_acoustic_peaks, peak_ratios
from .planck import PlanckTT, load_planck_tt
from .spectra import baseline_params, cl_to_dl, params_fixed_theta_s, run_class
from .sweep import SweepResult, default_grid, run_sweep

__all__ = [
    "Peak",
    "PlanckTT",
    "SweepResult",
    "baseline_params",
    "cl_to_dl",
    "default_grid",
    "find_acoustic_peaks",
    "load_planck_tt",
    "params_fixed_theta_s",
    "peak_ratios",
    "run_class",
    "run_sweep",
]
