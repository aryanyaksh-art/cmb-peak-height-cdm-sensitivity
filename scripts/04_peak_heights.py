"""Stage 5 Test C: individual peak heights vs omega_cdm.

Ratios (D1/D2, D3/D2) hide which peak actually moves. This replots the raw
peak heights from the cached fixed-theta_s sweep, each normalised to its own
value at the Planck omega_cdm, on one set of axes.

No CLASS runs -- pure replotting of data/sweep_fixed_theta_s.npz.
"""

import sys

from cmbpeaks.config import DATA_DIR
from cmbpeaks.plotting import plot_peak_heights_normalised
from cmbpeaks.sweep import SweepResult


def main() -> int:
    result = SweepResult.load(DATA_DIR / "sweep_fixed_theta_s.npz")
    plot_peak_heights_normalised(result)

    lo, hi = result.param_values[0], result.param_values[-1]
    print(f"\nfractional change across the grid (omega_cdm {lo:.2f} -> {hi:.2f}):")
    for i, label in enumerate(["D1", "D2", "D3"], start=1):
        d = result.peak_dls[:, i - 1]
        frac = d[-1] / d[0] - 1.0
        print(f"  {label}: {frac:+.1%}  ({d[0]:.0f} -> {d[-1]:.0f} uK^2)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
