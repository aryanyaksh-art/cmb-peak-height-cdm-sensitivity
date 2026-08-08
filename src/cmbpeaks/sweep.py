"""Sweep a CLASS parameter (default omega_cdm) and record peak heights.

Two sweep modes, and the difference between them is the methodological point of
the whole project:

``fixed_h``
    Vary the parameter, hold h. The sound horizon at recombination and the
    distance to last scattering both shift, so peak *positions* move along
    with the amplitudes. Everything on the plot slides. Pedagogically honest,
    visually busy.

``fixed_theta_s``
    Vary the parameter, hold the angular acoustic scale 100*theta_s at the
    Planck value and let CLASS solve for h. Peak positions lock to within
    ~2%, so the figure shows mostly the amplitude change -- which is the
    physics the swept parameter actually controls (radiation driving for
    omega_cdm, baryon loading for omega_b).

In both cases Omega_Lambda is left unset so CLASS's closure equation keeps the
universe spatially flat as the parameter changes. ``run_sweep`` defaults to
omega_cdm so every existing caller keeps working unchanged; pass
``param="omega_b"`` (and typically ``fixed={"omega_cdm": OMEGA_CDM_PLANCK}``)
for the baryon-loading companion sweep.
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
    param_values: np.ndarray
    d1_over_d2: np.ndarray
    d3_over_d2: np.ndarray
    peak_ells: np.ndarray  # shape (n_grid, n_peaks)
    peak_dls: np.ndarray  # shape (n_grid, n_peaks)
    z_eq: np.ndarray
    h: np.ndarray
    param: str = "omega_cdm"  # which CLASS parameter this sweep varied
    spectrum: str = "tt"  # which spectrum was tracked (tt, ee, ...)
    spectra: list = field(default_factory=list)  # (ell, Dl) per grid point

    def save(self, path):
        kwargs = dict(
            mode=self.mode,
            param=self.param,
            spectrum=self.spectrum,
            param_values=self.param_values,
            d1_over_d2=self.d1_over_d2,
            d3_over_d2=self.d3_over_d2,
            peak_ells=self.peak_ells,
            peak_dls=self.peak_dls,
            z_eq=self.z_eq,
            h=self.h,
        )
        non_null = [s for s in self.spectra if s is not None]
        if non_null:
            # ell is identical across grid points (same l_max every call), so
            # store it once rather than once per row.
            ell = non_null[0][0]
            n_ell = len(ell)
            dl_grid = np.full((len(self.spectra), n_ell), np.nan)
            for i, s in enumerate(self.spectra):
                if s is not None:
                    dl_grid[i] = s[1]
            kwargs["ell"] = ell
            kwargs["dl_grid"] = dl_grid
        np.savez_compressed(path, **kwargs)

    @classmethod
    def load(cls, path) -> "SweepResult":
        arr = np.load(path)
        spectra: list = []
        if "dl_grid" in arr:
            ell = arr["ell"]
            for row in arr["dl_grid"]:
                if np.all(np.isnan(row)):
                    spectra.append(None)
                else:
                    spectra.append((ell, row))
        # "param_values"/"param" postdate the omega_b sweep (Stage 6); files
        # saved before that only have "omega_cdm", always the swept quantity.
        if "param_values" in arr:
            param = str(arr["param"])
            param_values = arr["param_values"]
        else:
            param = "omega_cdm"
            param_values = arr["omega_cdm"]
        # "spectrum" postdates the EE sweep (Stage 8); every earlier file only
        # ever tracked TT, so that's the default for files that lack the key --
        # same precedent as "param" above.
        spectrum = str(arr["spectrum"]) if "spectrum" in arr else "tt"
        return cls(
            mode=str(arr["mode"]),
            param=param,
            spectrum=spectrum,
            param_values=param_values,
            d1_over_d2=arr["d1_over_d2"],
            d3_over_d2=arr["d3_over_d2"],
            peak_ells=arr["peak_ells"],
            peak_dls=arr["peak_dls"],
            z_eq=arr["z_eq"],
            h=arr["h"],
            spectra=spectra,
        )


def default_grid() -> np.ndarray:
    """omega_cdm grid bracketing the Planck value of 0.1200."""
    return np.linspace(OMEGA_CDM_GRID_MIN, OMEGA_CDM_GRID_MAX, OMEGA_CDM_GRID_N)


def peaks_from_cached_spectra(
    result: SweepResult,
    n_peaks: int,
    prominence: float = 50.0,
    first_peak_bounds: tuple[float, float] = (180.0, 280.0),
    ell_max_search: float = 1500.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Re-run the peak finder on a sweep's cached spectra, no CLASS call.

    For widening how many peaks are read off a sweep already run with
    ``keep_spectra=True`` -- e.g. reading 5 peaks off a sweep whose original
    ``run_sweep`` call only recorded 3 -- without paying for the CLASS time
    again and without touching the sweep's own saved ``peak_ells``/``peak_dls``
    (which stay whatever the original call computed).

    A grid point that doesn't yield ``n_peaks`` (missing cached spectrum, or
    ``find_acoustic_peaks`` raising) comes back as a NaN row plus a warning,
    same failure convention as ``run_sweep`` -- widening the peak count is not
    a reason to paper over an unstable point.
    """
    n = len(result.spectra)
    p_ells = np.full((n, n_peaks), np.nan)
    p_dls = np.full((n, n_peaks), np.nan)
    for i, s in enumerate(result.spectra):
        if s is None:
            warnings.warn(f"grid point {i}: no cached spectrum", stacklevel=2)
            continue
        ell, dl = s
        try:
            peaks = find_acoustic_peaks(
                ell,
                dl,
                n_peaks=n_peaks,
                prominence=prominence,
                first_peak_bounds=first_peak_bounds,
                ell_max_search=ell_max_search,
            )
        except Exception as exc:  # noqa: BLE001 - report, don't retune to hide it
            warnings.warn(f"grid point {i}: {exc}", stacklevel=2)
            continue
        p_ells[i] = [p.ell for p in peaks]
        p_dls[i] = [p.dl for p in peaks]
    return p_ells, p_dls


def run_sweep(
    grid: np.ndarray | None = None,
    mode: str = "fixed_theta_s",
    keep_spectra: bool = False,
    verbose: bool = True,
    lensed: bool = True,
    param: str = "omega_cdm",
    fixed: dict | None = None,
    spectrum: str = "tt",
    n_peaks: int = 3,
    prominence: float = 50.0,
    first_peak_bounds: tuple[float, float] | None = None,
    ell_max_search: float = 1500.0,
) -> SweepResult:
    """Run a sweep of ``param`` (default omega_cdm) over ``grid``.

    Failures at individual grid points are recorded as NaN rather than raised.
    The theta_s shooting solver occasionally fails to converge at extreme
    parameter values, and losing one point shouldn't discard a sweep that takes
    several minutes to run.

    ``lensed=False`` switches to CLASS's raw (unlensed) C_ell, for isolating
    how much of a trend is lensing smoothing rather than the underlying
    physics -- lensing suppresses higher peaks more than lower ones, which is
    a low-ell-favouring effect too and has to be ruled out before crediting
    anything else.

    ``fixed`` overrides any other baseline parameter (e.g. ``{"omega_cdm":
    0.1200}`` when sweeping omega_b, to be explicit that CDM is pinned at the
    Planck value even though that's already the baseline default).

    ``spectrum``, ``n_peaks``, ``prominence`` and ``ell_max_search`` select
    which spectrum ``run_class`` returns and how ``find_acoustic_peaks`` reads
    it -- defaults reproduce the original TT-only, 3-peak behaviour exactly,
    so every existing TT caller is unaffected. ``first_peak_bounds`` defaults
    to ``None``, which keeps TT's mode-dependent window (120-280 fixed_h,
    180-280 fixed_theta_s); pass an explicit window (e.g. config.py's
    ``EE_PEAK_FIRST_BOUNDS``) for a non-TT spectrum, since TT's window is
    tuned to TT peak positions.
    """
    if mode not in ("fixed_h", "fixed_theta_s"):
        raise ValueError(f"unknown mode {mode!r}")

    grid = default_grid() if grid is None else np.asarray(grid)
    fixed = fixed or {}
    n = len(grid)

    d1d2 = np.full(n, np.nan)
    d3d2 = np.full(n, np.nan)
    p_ells = np.full((n, n_peaks), np.nan)
    p_dls = np.full((n, n_peaks), np.nan)
    z_eq = np.full(n, np.nan)
    h_out = np.full(n, np.nan)
    spectra = []

    for i, val in enumerate(grid):
        overrides = {**fixed, param: float(val)}
        if mode == "fixed_h":
            params = baseline_params(**overrides)
        else:
            params = params_fixed_theta_s(THETA_S_100, **overrides)

        if first_peak_bounds is not None:
            bounds = first_peak_bounds
        elif mode == "fixed_h":
            # fixed_h lets the sound horizon grow faster than the distance to
            # last scattering as omega_cdm drops, so ell_1 can undershoot
            # Planck's [180, 280] window well before it stops being an
            # acoustic peak.
            bounds = (120.0, 280.0)
        else:
            bounds = (180.0, 280.0)

        try:
            ell, dl, derived = run_class(params, lensed=lensed, spectra=(spectrum,))
            peaks = find_acoustic_peaks(
                ell,
                dl,
                n_peaks=n_peaks,
                prominence=prominence,
                first_peak_bounds=bounds,
                ell_max_search=ell_max_search,
            )
            ratios = peak_ratios(peaks)

            d1d2[i] = ratios["D1_over_D2"]
            d3d2[i] = ratios.get("D3_over_D2", np.nan)
            p_ells[i] = [p.ell for p in peaks]
            p_dls[i] = [p.dl for p in peaks]
            z_eq[i] = derived.get("z_eq", np.nan)
            h_out[i] = derived.get("h", params.get("h", np.nan))

            if keep_spectra:
                spectra.append((ell, dl))
            if verbose:
                print(
                    f"  [{i + 1:2d}/{n}] {param}={val:.4f}  "
                    f"D1/D2={d1d2[i]:.3f}  D3/D2={d3d2[i]:.3f}  "
                    f"z_eq={z_eq[i]:.0f}  h={h_out[i]:.4f}"
                )
        except Exception as exc:  # noqa: BLE001 - one bad point shouldn't kill the run
            warnings.warn(f"{param}={val:.4f} failed: {exc}", stacklevel=2)
            if keep_spectra:
                spectra.append(None)

    return SweepResult(
        mode=mode,
        param=param,
        spectrum=spectrum,
        param_values=grid,
        d1_over_d2=d1d2,
        d3_over_d2=d3d2,
        peak_ells=p_ells,
        peak_dls=p_dls,
        z_eq=z_eq,
        h=h_out,
        spectra=spectra,
    )
