"""Sweep omega_cdm and record peak heights.

Two sweep modes, and the difference between them is the methodological point of
the whole project:

``fixed_h``
    Vary omega_cdm, hold h. The sound horizon at recombination and the distance
    to last scattering both shift, so peak *positions* move along with the
    amplitudes. Everything on the plot slides. Pedagogically honest, visually
    busy.

``fixed_theta_s``
    Vary omega_cdm, hold the angular acoustic scale 100*theta_s at the Planck
    value and let CLASS solve for h. Peak positions lock in place, so the figure
    shows only the amplitude change -- which is the radiation-driving physics
    dark matter actually controls.

In both cases Omega_Lambda is left unset so CLASS's closure equation keeps the
universe spatially flat as omega_cdm changes.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np

from .config import (
    OMEGA_CDM_GRID_MAX,
    OMEGA_CDM_GRID_MIN,
    OMEGA_CDM_GRID_N,
    THETA_S_100,
)
from .peaks import find_acoustic_peaks, peak_ratios
from .spectra import baseline_params, params_fixed_theta_s, run_class


@dataclass
class SweepResult:
    mode: str
    omega_cdm: np.ndarray
    d1_over_d2: np.ndarray
    d3_over_d2: np.ndarray
    peak_ells: np.ndarray  # shape (n_grid, 3)
    peak_dls: np.ndarray  # shape (n_grid, 3)
    z_eq: np.ndarray
    h: np.ndarray
    spectra: list = field(default_factory=list)  # (ell, Dl) per grid point

    def save(self, path):
        np.savez_compressed(
            path,
            mode=self.mode,
            omega_cdm=self.omega_cdm,
            d1_over_d2=self.d1_over_d2,
            d3_over_d2=self.d3_over_d2,
            peak_ells=self.peak_ells,
            peak_dls=self.peak_dls,
            z_eq=self.z_eq,
            h=self.h,
        )


def default_grid() -> np.ndarray:
    """omega_cdm grid bracketing the Planck value of 0.1200."""
    return np.linspace(OMEGA_CDM_GRID_MIN, OMEGA_CDM_GRID_MAX, OMEGA_CDM_GRID_N)


def run_sweep(
    grid: np.ndarray | None = None,
    mode: str = "fixed_theta_s",
    keep_spectra: bool = False,
    verbose: bool = True,
) -> SweepResult:
    """Run the omega_cdm sweep.

    Failures at individual grid points are recorded as NaN rather than raised.
    The theta_s shooting solver occasionally fails to converge at extreme
    parameter values, and losing one point shouldn't discard a sweep that takes
    several minutes to run.
    """
    if mode not in ("fixed_h", "fixed_theta_s"):
        raise ValueError(f"unknown mode {mode!r}")

    grid = default_grid() if grid is None else np.asarray(grid)
    n = len(grid)

    d1d2 = np.full(n, np.nan)
    d3d2 = np.full(n, np.nan)
    p_ells = np.full((n, 3), np.nan)
    p_dls = np.full((n, 3), np.nan)
    z_eq = np.full(n, np.nan)
    h_out = np.full(n, np.nan)
    spectra = []

    for i, oc in enumerate(grid):
        if mode == "fixed_h":
            params = baseline_params(omega_cdm=float(oc))
        else:
            params = params_fixed_theta_s(float(oc), THETA_S_100)

        try:
            ell, dl, derived = run_class(params)
            peaks = find_acoustic_peaks(ell, dl, n_peaks=3)
            ratios = peak_ratios(peaks)

            d1d2[i] = ratios["D1_over_D2"]
            d3d2[i] = ratios["D3_over_D2"]
            p_ells[i] = [p.ell for p in peaks]
            p_dls[i] = [p.dl for p in peaks]
            z_eq[i] = derived.get("z_eq", np.nan)
            h_out[i] = derived.get("h", params.get("h", np.nan))

            if keep_spectra:
                spectra.append((ell, dl))
            if verbose:
                print(
                    f"  [{i + 1:2d}/{n}] omega_cdm={oc:.4f}  "
                    f"D1/D2={d1d2[i]:.3f}  D3/D2={d3d2[i]:.3f}  "
                    f"z_eq={z_eq[i]:.0f}  h={h_out[i]:.4f}"
                )
        except Exception as exc:  # noqa: BLE001 - one bad point shouldn't kill the run
            warnings.warn(f"omega_cdm={oc:.4f} failed: {exc}", stacklevel=2)
            if keep_spectra:
                spectra.append(None)

    return SweepResult(
        mode=mode,
        omega_cdm=grid,
        d1_over_d2=d1d2,
        d3_over_d2=d3d2,
        peak_ells=p_ells,
        peak_dls=p_dls,
        z_eq=z_eq,
        h=h_out,
        spectra=spectra,
    )
