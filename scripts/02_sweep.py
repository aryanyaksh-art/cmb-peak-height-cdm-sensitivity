"""Stage 2: sweep omega_cdm, plot peak-height ratios and z_eq.

Defaults to the fixed-theta_s mode, which locks peak positions so the figure
shows the amplitude effect alone. Pass --mode fixed_h for the version where
everything moves.

Expect several minutes: each grid point is a full Boltzmann computation, and the
theta_s shooting solver adds a root-find on top.
"""

import argparse
import sys

from cmbpeaks.config import DATA_DIR
from cmbpeaks.plotting import plot_sweep
from cmbpeaks.sweep import default_grid, run_sweep


def _run_one(mode: str, grid) -> None:
    print(f"sweeping omega_cdm over {len(grid)} points, mode={mode}")
    result = run_sweep(grid, mode=mode, keep_spectra=True)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / f"sweep_{mode}.npz"
    result.save(out)
    print(f"\nwrote {out}")

    plot_sweep(result, name=f"02_sweep_ratio_{mode}.png")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["fixed_h", "fixed_theta_s", "both"],
                    default="both")
    ap.add_argument("--n", type=int, default=None,
                    help="grid points (default: config value)")
    args = ap.parse_args()

    grid = default_grid()
    if args.n:
        import numpy as np
        grid = np.linspace(grid[0], grid[-1], args.n)

    modes = ["fixed_h", "fixed_theta_s"] if args.mode == "both" else [args.mode]
    for mode in modes:
        _run_one(mode, grid)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
