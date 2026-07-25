"""Stage 5 Test E: scaling collapse against x = ell_peak / ell_eq(omega_cdm).

The real test of the k_eq-envelope hypothesis: if suppression depends only on
where a mode sits relative to the equality scale, all three peaks should fall
on one curve when plotted against x, not sit as three separate curves.

No CLASS runs -- uses the cached lensed sweep (data/sweep_fixed_theta_s.npz),
for consistency with Tests C and D, and cmbpeaks.keq.compute_ell_eq (the same
function scripts/04b_keq_test.py and 04c_keq_geomean_check.py use) rather than
recomputing ell_eq a third way.
"""

import sys

import numpy as np

from cmbpeaks.config import DATA_DIR, FIGURE_DIR, OMEGA_CDM_PLANCK
from cmbpeaks.keq import compute_ell_eq
from cmbpeaks.sweep import SweepResult


def main() -> int:
    result = SweepResult.load(DATA_DIR / "sweep_fixed_theta_s.npz")
    omega_cdm = result.omega_cdm
    h = result.h
    ref_idx = int(np.argmin(np.abs(omega_cdm - OMEGA_CDM_PLANCK)))

    _, _, ell_eq = compute_ell_eq(omega_cdm, h)

    peak_dls = result.peak_dls  # (16, 3)
    peak_ells = result.peak_ells  # (16, 3)
    ref_dl = peak_dls[ref_idx]  # (3,)

    n_grid, n_peaks = peak_dls.shape
    x_all, y_all, peak_id = [], [], []
    for p in range(n_peaks):
        x = peak_ells[:, p] / ell_eq
        y = peak_dls[:, p] / ref_dl[p] - 1.0
        x_all.append(x)
        y_all.append(y)
        peak_id.append(np.full(n_grid, p))

    x_all = np.concatenate(x_all)
    y_all = np.concatenate(y_all)
    peak_id = np.concatenate(peak_id)

    print("x = ell_peak / ell_eq, y = fractional change in D_peak vs omega_cdm=0.12")
    print("peak  omega_cdm    ell_peak   ell_eq       x        y")
    for p in range(n_peaks):
        for i, oc in enumerate(omega_cdm):
            print(f"  {p + 1}   {oc:.4f}    {peak_ells[i, p]:8.1f}   {ell_eq[i]:7.1f}   "
                  f"{peak_ells[i, p] / ell_eq[i]:6.3f}   {peak_dls[i, p] / ref_dl[p] - 1.0:+.4f}")

    # Tightness of collapse: fit one smooth curve (quadratic in x) to all 48
    # points combined, then compare each peak's RMS residual from that shared
    # fit against its own individually-fit quadratic. If the shared fit does
    # nearly as well as each peak's own fit, the collapse is tight.
    coeffs_shared = np.polyfit(x_all, y_all, 2)
    y_shared_fit = np.polyval(coeffs_shared, x_all)
    rms_shared_total = np.sqrt(np.mean((y_all - y_shared_fit) ** 2))

    print(f"\nRMS residual from one shared quadratic fit (all 48 points): {rms_shared_total:.4f}")
    print("\npeak  RMS resid (shared fit)  RMS resid (own fit)  x range")
    for p in range(n_peaks):
        m = peak_id == p
        resid_shared = y_all[m] - y_shared_fit[m]
        rms_shared = np.sqrt(np.mean(resid_shared**2))
        coeffs_own = np.polyfit(x_all[m], y_all[m], 2)
        resid_own = y_all[m] - np.polyval(coeffs_own, x_all[m])
        rms_own = np.sqrt(np.mean(resid_own**2))
        print(f"  {p + 1}          {rms_shared:.4f}                {rms_own:.4f}          "
              f"{x_all[m].min():.2f} -- {x_all[m].max():.2f}")

    import matplotlib.pyplot as plt

    markers = ["o", "s", "^"]
    colors = ["tab:blue", "tab:orange", "tab:green"]
    fig, ax = plt.subplots(figsize=(8, 6))
    for p in range(n_peaks):
        m = peak_id == p
        ax.plot(x_all[m], y_all[m], markers[p], color=colors[p], ms=6,
                label=f"peak {p + 1}", mec="k", mew=0.4)

    x_line = np.linspace(x_all.min(), x_all.max(), 200)
    ax.plot(x_line, np.polyval(coeffs_shared, x_line), "k--", lw=1,
            label="shared quadratic fit")
    ax.axhline(0.0, color="0.6", lw=0.8)
    ax.set_xlabel(r"$x = \ell_{\rm peak} / \ell_{eq}(\omega_{cdm})$")
    ax.set_ylabel(r"$D_{\rm peak}(\omega_{cdm}) / D_{\rm peak}(0.12) - 1$")
    ax.set_title("Test E: scaling collapse against the equality scale")
    ax.legend()

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURE_DIR / "06_scaling_collapse.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
