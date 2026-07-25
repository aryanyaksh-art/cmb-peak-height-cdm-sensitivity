"""Stage 1: baseline LCDM spectrum, Planck overlay, benchmark check.

Benchmarks (Planck 2018 I, Table 5): first peak at ell = 220.6 with
D_ell = 5733 microK^2. If the amplitude is off by ~10^12, the T_cmb^2-in-microK^2
factor is missing from the C_ell -> D_ell conversion.
"""

import sys

import numpy as np

from cmbpeaks.config import DATA_DIR
from cmbpeaks.peaks import find_acoustic_peaks, peak_ratios
from cmbpeaks.planck import load_planck_tt
from cmbpeaks.plotting import plot_baseline_overlay, report_benchmarks
from cmbpeaks.spectra import baseline_params, run_class


def main() -> int:
    print("computing baseline LCDM spectrum (lensed)...")
    ell, dl, derived = run_class(baseline_params(), lensed=True)

    print(f"  z_eq       = {derived.get('z_eq', float('nan')):.1f}")
    print(f"  100*theta_s= {derived.get('100*theta_s', float('nan')):.5f}")
    print(f"  Omega_m    = {derived.get('Omega_m', float('nan')):.4f}")

    peaks = find_acoustic_peaks(ell, dl, n_peaks=3)
    ok = report_benchmarks(peaks)

    ratios = peak_ratios(peaks)
    print(f"\n  D1/D2 = {ratios['D1_over_D2']:.3f}")
    print(f"  D3/D2 = {ratios['D3_over_D2']:.3f}")
    print(
        "  (D3/D2 near 1 is the dark-matter signature: baryon loading alone\n"
        "   would leave peak 3 well below peak 2.)"
    )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(DATA_DIR / "baseline_Dl.npz", ell=ell, dl=dl)
    print(f"\nwrote {DATA_DIR / 'baseline_Dl.npz'}")

    planck = load_planck_tt()
    plot_baseline_overlay(ell, dl, planck, peaks=peaks)

    if not ok:
        print("\nBenchmarks outside tolerance -- check units and parameters.")
        return 1
    print("\nBenchmarks pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
