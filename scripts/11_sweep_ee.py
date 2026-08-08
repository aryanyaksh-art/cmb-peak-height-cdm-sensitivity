"""Stage 8 step 7: the EE omega_cdm sweep, same 16-point grid as Stage 2/5.

Runs the diagnostic docs/STAGE8_SPEC.md section 3 sets up: does one EE peak
resist the omega_cdm-driven height change far more than its neighbours (like
TT peak 3 does), do EE peaks change more uniformly than TT's, or is EE too
noisy to say? No predicted sign goes here -- record which row of the section 3
table the result lands in, the same rule Stage 2 learned the hard way.

Peak numbering is not compared across spectra (docs/STAGE8_SPEC.md section 5,
settled 2026-07-27): TT peak 3 sits at ell~813, between EE's maxima at ell~688
and ell~990. The comparison figure plots fractional height change against
each peak's own position instead.

The comparison originally used TT peaks 1-3 (ell 220-813) against EE peaks
1-5 (ell 395-1608): only two points of each fell in the shared range, so a
claim about TT having a break EE lacks would rest on three TT points -- the
same "too few points to be conclusive" trap Stage 5's k_eq test warned about.
TT peaks 4 and 5 (ell ~1130, ~1430) are both inside the existing TT sweep's
ell_max_search=1500, so they're read off the *already-cached* spectra in
data/sweep_fixed_theta_s.npz via peaks_from_cached_spectra -- no new CLASS
calls, and the original 3-peak sweep_fixed_theta_s.npz (and its published
48.4/45.2/16.5% numbers) is not touched or overwritten.
"""

import sys

import numpy as np

from cmbpeaks.config import (
    DATA_DIR,
    EE_PEAK_ELL_MAX_SEARCH,
    EE_PEAK_FIRST_BOUNDS,
    EE_PEAK_PROMINENCE,
)
from cmbpeaks.plotting import plot_peak_height_change_vs_ell
from cmbpeaks.sweep import SweepResult, default_grid, peaks_from_cached_spectra, run_sweep


def _print_table(label, ell_ref, peak_dls):
    """Fractional height change per peak, plus consecutive-point slopes."""
    frac = peak_dls[-1, :] / peak_dls[0, :] - 1.0
    order = np.argsort(ell_ref)
    ell_sorted = ell_ref[order]
    frac_sorted = frac[order]

    print(f"\n{label} fractional height change (ell at Planck omega_cdm):")
    for ell, f in zip(ell_sorted, frac_sorted):
        print(f"  ell={ell:7.1f}: {f:+.1%}")

    print(f"{label} consecutive-point slopes (d(frac)/d(ell), x1e-4):")
    for i in range(len(ell_sorted) - 1):
        slope = (frac_sorted[i + 1] - frac_sorted[i]) / (ell_sorted[i + 1] - ell_sorted[i])
        print(
            f"  ell {ell_sorted[i]:.0f} -> {ell_sorted[i + 1]:.0f}: "
            f"{slope * 1e4:+.1f}"
        )


def main() -> int:
    grid = default_grid()
    print(
        f"sweeping omega_cdm over {len(grid)} points, mode=fixed_theta_s, "
        "spectrum=EE"
    )

    result = run_sweep(
        grid,
        mode="fixed_theta_s",
        keep_spectra=True,
        spectrum="ee",
        n_peaks=5,
        prominence=EE_PEAK_PROMINENCE,
        first_peak_bounds=EE_PEAK_FIRST_BOUNDS,
        ell_max_search=EE_PEAK_ELL_MAX_SEARCH,
    )

    n_nan = int(sum(1 for v in result.d1_over_d2 if v != v))
    if n_nan:
        print(f"\nWARNING: {n_nan}/{len(grid)} grid points failed (NaN rows)")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "sweep_ee_fixed_theta_s.npz"
    result.save(out)
    print(f"\nwrote {out}")

    # TT: widen from the cached sweep's 3 peaks to 5, reading the already-kept
    # spectra rather than re-running CLASS. Same prominence/bounds/search
    # window the 3-peak sweep used -- only n_peaks changes.
    tt_result = SweepResult.load(DATA_DIR / "sweep_fixed_theta_s.npz")
    tt_ells_5, tt_dls_5 = peaks_from_cached_spectra(
        tt_result, n_peaks=5, prominence=50.0,
        first_peak_bounds=(180.0, 280.0), ell_max_search=1500.0,
    )
    n_tt_nan = int(np.sum(np.any(np.isnan(tt_dls_5), axis=1)))
    if n_tt_nan:
        print(f"\nWARNING: {n_tt_nan}/{len(grid)} TT grid points failed to yield 5 peaks")
    else:
        print(f"\nTT 5-peak extraction: stable at all {len(grid)}/{len(grid)} grid points")

    # Sanity check: peaks 1-3 must be untouched by widening to 5.
    assert np.allclose(tt_ells_5[:, :3], tt_result.peak_ells, atol=1e-6)
    assert np.allclose(tt_dls_5[:, :3], tt_result.peak_dls, atol=1e-6)

    # In-memory 5-peak TT result for the figure only -- not saved, so
    # data/sweep_fixed_theta_s.npz (and its published 3-peak numbers) is
    # untouched.
    tt_result_5 = SweepResult(
        mode=tt_result.mode,
        param=tt_result.param,
        spectrum=tt_result.spectrum,
        param_values=tt_result.param_values,
        d1_over_d2=tt_result.d1_over_d2,
        d3_over_d2=tt_result.d3_over_d2,
        peak_ells=tt_ells_5,
        peak_dls=tt_dls_5,
        z_eq=tt_result.z_eq,
        h=tt_result.h,
    )

    fig_path = plot_peak_height_change_vs_ell(tt_result_5, result)
    print(f"wrote {fig_path}")

    ref_idx = int(np.argmin(np.abs(grid - 0.1200)))  # Planck omega_cdm
    _print_table("EE", result.peak_ells[ref_idx], result.peak_dls)
    _print_table("TT", tt_ells_5[ref_idx], tt_dls_5)

    return 0


if __name__ == "__main__":
    sys.exit(main())
