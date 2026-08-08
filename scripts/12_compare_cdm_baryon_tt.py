"""Characterisation follow-up to the 5-peak TT result in scripts/11_sweep_ee.py.

The omega_cdm sweep's 5-peak TT losses (48.4/45.2/16.5/23.5/6.5% at ell =
220/537/814/1127/1423) alternate from peak 2 onward: odd-numbered peaks
(compression) resist more than the adjacent even-numbered peak (rarefaction).
That could be parity structure -- a compression-vs-rarefaction effect -- or it
could be five numbers with no structure at all. This script does not decide
that; it only asks whether the Stage 6 omega_b sweep's TT peaks show the same
alternation, the opposite, or neither, as one more data point.

Uses only data/sweep_fixed_theta_s.npz and data/sweep_omega_b_fixed_theta_s.npz,
both already on disk with keep_spectra=True -- no CLASS calls here.

Not a mechanism proposal. Stage 5 eliminated four candidates for the
omega_cdm anomaly and it stays open; this script characterises a second
sweep, it does not explain the first one.
"""

import sys

import numpy as np

from cmbpeaks.config import DATA_DIR
from cmbpeaks.plotting import plot_peak_height_change_vs_ell_by_param
from cmbpeaks.sweep import SweepResult, peaks_from_cached_spectra


def _five_peak_result(path):
    base = SweepResult.load(path)
    ells_5, dls_5 = peaks_from_cached_spectra(
        base, n_peaks=5, prominence=50.0,
        first_peak_bounds=(180.0, 280.0), ell_max_search=1500.0,
    )
    n_nan = int(np.sum(np.any(np.isnan(dls_5), axis=1)))
    if n_nan:
        print(f"WARNING: {n_nan}/{len(base.param_values)} grid points "
              f"({path.name}) failed to yield 5 peaks")
    else:
        print(f"5-peak extraction stable at all "
              f"{len(base.param_values)}/{len(base.param_values)} grid points ({path.name})")

    # peaks 1-3 must be untouched by widening to 5.
    assert np.allclose(ells_5[:, :3], base.peak_ells, atol=1e-6)
    assert np.allclose(dls_5[:, :3], base.peak_dls, atol=1e-6)

    return SweepResult(
        mode=base.mode,
        param=base.param,
        spectrum=base.spectrum,
        param_values=base.param_values,
        d1_over_d2=base.d1_over_d2,
        d3_over_d2=base.d3_over_d2,
        peak_ells=ells_5,
        peak_dls=dls_5,
        z_eq=base.z_eq,
        h=base.h,
    )


def _print_table(label, ell_ref, peak_dls):
    frac = peak_dls[-1, :] / peak_dls[0, :] - 1.0
    order = np.argsort(ell_ref)
    ell_sorted = ell_ref[order]
    frac_sorted = frac[order]

    print(f"\n{label} fractional height change (ell at Planck reference):")
    for ell, f in zip(ell_sorted, frac_sorted):
        print(f"  ell={ell:7.1f}: {f:+.1%}")

    print(f"{label} consecutive-point slopes (d(frac)/d(ell), x1e-4):")
    for i in range(len(ell_sorted) - 1):
        slope = (frac_sorted[i + 1] - frac_sorted[i]) / (ell_sorted[i + 1] - ell_sorted[i])
        print(f"  ell {ell_sorted[i]:.0f} -> {ell_sorted[i + 1]:.0f}: {slope * 1e4:+.1f}")

    return frac_sorted


def main() -> int:
    cdm_result = _five_peak_result(DATA_DIR / "sweep_fixed_theta_s.npz")
    b_result = _five_peak_result(DATA_DIR / "sweep_omega_b_fixed_theta_s.npz")

    ref_idx_cdm = int(np.argmin(np.abs(cdm_result.param_values - 0.1200)))
    ref_idx_b = int(np.argmin(np.abs(b_result.param_values - 0.02237)))

    frac_cdm = _print_table("omega_cdm sweep, TT", cdm_result.peak_ells[ref_idx_cdm], cdm_result.peak_dls)
    frac_b = _print_table("omega_b sweep, TT", b_result.peak_ells[ref_idx_b], b_result.peak_dls)

    fig_path = plot_peak_height_change_vs_ell_by_param(cdm_result, b_result)
    print(f"\nwrote {fig_path}")

    # Parity observation only: sign of (odd-peak loss - adjacent even-peak
    # loss) for peaks 2-3, 3-4, 4-5, ordered by ell. Reported, not interpreted.
    print("\nparity check (peak n vs peak n+1 loss, ordered by ell):")
    for label, frac in (("omega_cdm", frac_cdm), ("omega_b", frac_b)):
        signs = []
        for i in range(1, len(frac)):
            d = frac[i] - frac[i - 1]  # loss[i] - loss[i-1]; frac is negative, so
            signs.append("more resistant" if d > 0 else "less resistant")
        print(f"  {label}: " + ", ".join(
            f"peak{i+2} {s} than peak{i+1}" for i, s in enumerate(signs)
        ))

    return 0


if __name__ == "__main__":
    sys.exit(main())
