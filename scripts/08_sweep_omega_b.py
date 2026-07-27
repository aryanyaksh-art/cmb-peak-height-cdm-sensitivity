"""Stage 6: sweep omega_b instead of omega_cdm -- the baryometer companion figure.

Dark matter and baryons move the acoustic peaks through different physics.
The omega_cdm sweep (Stage 2/5) isolates radiation driving, the mechanism a
CDM-dominated matter budget controls. This sweep isolates baryon loading:
baryons add inertia to the photon-baryon fluid without adding pressure, which
shifts the oscillation's zero-point and enhances compression peaks (1st, 3rd)
over the rarefaction peak (2nd). Because R = 3*rho_b / 4*rho_gamma depends
only on omega_b (and redshift), not on omega_cdm, both D1/D2 and D3/D2 are
expected to rise with omega_b -- the textbook prediction, unlike the omega_cdm
sign flips this project already ran into. Recorded either way; a prediction
being right is not a reason to skip stating it as a prediction.

Fixed-theta_s mode only, so peak positions stay locked and the figure isolates
the amplitude effect, same as the omega_cdm sweep's headline panel. omega_cdm
is held at the Planck value explicitly via ``fixed=`` even though that's
already the baseline default, so the sweep call states the held parameter
rather than relying on an implicit default.
"""

import sys

import numpy as np

from cmbpeaks.config import (
    DATA_DIR,
    OMEGA_B_GRID_MAX,
    OMEGA_B_GRID_MIN,
    OMEGA_B_GRID_N,
    OMEGA_CDM_PLANCK,
)
from cmbpeaks.plotting import plot_sweep
from cmbpeaks.sweep import run_sweep


def main() -> int:
    grid = np.linspace(OMEGA_B_GRID_MIN, OMEGA_B_GRID_MAX, OMEGA_B_GRID_N)
    print(f"sweeping omega_b over {len(grid)} points, mode=fixed_theta_s, "
          f"omega_cdm held at {OMEGA_CDM_PLANCK}")

    result = run_sweep(
        grid,
        mode="fixed_theta_s",
        keep_spectra=True,
        param="omega_b",
        fixed={"omega_cdm": OMEGA_CDM_PLANCK},
    )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "sweep_omega_b_fixed_theta_s.npz"
    result.save(out)
    print(f"\nwrote {out}")

    plot_sweep(result, name="08_sweep_ratio_omega_b_fixed_theta_s.png")

    print("\nD1/D2 range:", f"{result.d1_over_d2[0]:.3f} -> {result.d1_over_d2[-1]:.3f}")
    print("D3/D2 range:", f"{result.d3_over_d2[0]:.3f} -> {result.d3_over_d2[-1]:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
