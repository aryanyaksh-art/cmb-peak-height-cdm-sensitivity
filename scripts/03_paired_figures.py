"""Stage 3: the paired figure — fixed h vs fixed 100*theta_s.

Runs both sweeps keeping the full spectra, then plots them side by side. This is
the figure that shows methodological awareness: the same physical change looks
different depending on what you hold fixed, and only the fixed-theta_s panel
isolates the radiation-driving amplitude effect from geometric shifts.

Slow — two full sweeps. Use a coarse grid while iterating.
"""

import argparse
import sys

import numpy as np

from cmbpeaks.config import DATA_DIR
from cmbpeaks.plotting import plot_paired_sweeps
from cmbpeaks.sweep import SweepResult, default_grid, run_sweep


def _load_or_run(mode: str, grid, force: bool) -> SweepResult:
    path = DATA_DIR / f"sweep_{mode}.npz"
    if not force and path.exists():
        print(f"loading cached {path}")
        result = SweepResult.load(path)
        if any(s is not None for s in result.spectra):
            return result
        print(f"  {path} has no retained spectra, re-running")

    print(f"running sweep: {mode}")
    result = run_sweep(grid, mode=mode, keep_spectra=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    result.save(path)
    print(f"wrote {path}")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8,
                    help="grid points per sweep (fewer = faster, 8 reads well)")
    ap.add_argument("--force", action="store_true",
                    help="recompute both sweeps even if cached npz files exist")
    args = ap.parse_args()

    g = default_grid()
    grid = np.linspace(g[0], g[-1], args.n)

    print("sweep 1/2: fixed h")
    res_h = _load_or_run("fixed_h", grid, args.force)

    print("\nsweep 2/2: fixed 100*theta_s")
    res_t = _load_or_run("fixed_theta_s", grid, args.force)

    plot_paired_sweeps(res_h, res_t)

    span_h = np.nanmax(res_h.peak_ells[:, 0]) - np.nanmin(res_h.peak_ells[:, 0])
    span_t = np.nanmax(res_t.peak_ells[:, 0]) - np.nanmin(res_t.peak_ells[:, 0])
    print("\nfirst-peak position spread across the grid:")
    print(f"  fixed h        : {span_h:6.1f} in ell")
    print(f"  fixed theta_s  : {span_t:6.1f} in ell   (should be much smaller)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
