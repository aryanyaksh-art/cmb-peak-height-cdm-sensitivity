"""Stage 8 step 4: baseline EE and TE overlays against Planck 2018.

Eyeball these before trusting anything downstream -- if the baseline overlay
is wrong, every later figure (the retuned peak finder, the EE sweep) is wrong
too. This script does not find peaks; retuning the peak finder for EE is
Stage 8 step 5 and is deliberately not done here.

EE carries Stage 8's analysis; TE is a pipeline check only (it crosses zero,
so peak-height ratios aren't meaningful for it -- see
docs/STAGE8_SPEC.md section 4).
"""

import sys

from cmbpeaks.config import PLANCK_EE_BINNED, PLANCK_TE_BINNED
from cmbpeaks.planck import load_planck_spectrum
from cmbpeaks.plotting import plot_baseline_overlay_ee, plot_baseline_overlay_te
from cmbpeaks.spectra import baseline_params, run_class


def main() -> int:
    print("computing baseline LCDM spectra (TT, EE, TE; lensed)...")
    ell, dl, _ = run_class(baseline_params(), lensed=True, spectra=("tt", "ee", "te"))

    planck_ee = load_planck_spectrum(PLANCK_EE_BINNED, spectrum="EE")
    planck_te = load_planck_spectrum(PLANCK_TE_BINNED, spectrum="TE")

    ee_path = plot_baseline_overlay_ee(ell, dl["ee"], planck_ee)
    te_path = plot_baseline_overlay_te(ell, dl["te"], planck_te)

    print(f"\nwrote {ee_path}")
    print(f"wrote {te_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
