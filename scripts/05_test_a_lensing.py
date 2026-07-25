"""Stage 5 Test A: is the D1/D2 sign flip a lensing artifact?

Gravitational lensing smooths the acoustic peaks and suppresses higher ones
more than lower ones -- a low-ell-favouring effect too, so it has to be ruled
out before crediting the D1/D2 trend to anything else (early ISW, the
radiation-driving envelope, etc).

Runs the fixed-theta_s sweep with lensed=False and compares its D1/D2, D3/D2
trends against the already-cached lensed sweep. ~16 Boltzmann runs.
"""

import sys

from cmbpeaks.config import DATA_DIR
from cmbpeaks.sweep import SweepResult, default_grid, run_sweep


def main() -> int:
    grid = default_grid()

    lensed = SweepResult.load(DATA_DIR / "sweep_fixed_theta_s.npz")

    print("running fixed_theta_s sweep, lensed=False ...")
    unlensed = run_sweep(grid, mode="fixed_theta_s", keep_spectra=True, lensed=False)
    out = DATA_DIR / "sweep_fixed_theta_s_unlensed.npz"
    unlensed.save(out)
    print(f"wrote {out}")

    print("\n=== D1/D2, D3/D2: lensed vs unlensed ===")
    print(f"{'omega_cdm':>10}  {'D1/D2 (lensed)':>15}  {'D1/D2 (unlensed)':>17}  "
          f"{'D3/D2 (lensed)':>15}  {'D3/D2 (unlensed)':>17}")
    for oc, d1l, d1u, d3l, d3u in zip(
        grid, lensed.d1_over_d2, unlensed.d1_over_d2,
        lensed.d3_over_d2, unlensed.d3_over_d2,
    ):
        print(f"{oc:10.4f}  {d1l:15.3f}  {d1u:17.3f}  {d3l:15.3f}  {d3u:17.3f}")

    print("\nD1/D2 range, lensed:   "
          f"{lensed.d1_over_d2[0]:.3f} -> {lensed.d1_over_d2[-1]:.3f}")
    print("D1/D2 range, unlensed: "
          f"{unlensed.d1_over_d2[0]:.3f} -> {unlensed.d1_over_d2[-1]:.3f}")
    print("D3/D2 range, lensed:   "
          f"{lensed.d3_over_d2[0]:.3f} -> {lensed.d3_over_d2[-1]:.3f}")
    print("D3/D2 range, unlensed: "
          f"{unlensed.d3_over_d2[0]:.3f} -> {unlensed.d3_over_d2[-1]:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
