"""Stage 5 Test F: corrected collapse, F1 (shared shape + offsets) and F2 (log-log slope).

Test E normalised each peak to its own value at omega_cdm=0.12, which forces
three different reference abscissas x_ref (ell_eq differs by grid point but
ell_peak is fixed per peak, so x_ref = ell_peak,ref/ell_eq,ref differs across
peaks: 1.54, 3.76, 5.66 for peaks 1/2/3). Under D_peak = A_peak * B(x), that
normalisation guarantees three vertically-offset curves even if B is exactly
universal -- Test E could not have told "hypothesis wrong" from "normalisation
wrong" apart.

F1 fits ln D_peak = offset_peak + f(x) with one shared shape f (quadratic)
across all 48 points and three free offsets, and reports the residual RMS
against Test E's shared-fit RMS of 0.162.

F2 is the decisive one: differentiating kills the offset entirely. If B is
universal, d(ln D_peak)/d(ln x) must be the same function of x for every
peak. Peaks 2 and 3 overlap in x; compare their derivatives there, with a
per-peak finite-difference-vs-smooth-fit residual as the noise floor.

No CLASS runs -- cached lensed sweep (data/sweep_fixed_theta_s.npz) and
cmbpeaks.keq.compute_ell_eq, same as Tests D and E.
"""

import sys

import numpy as np

from cmbpeaks.config import DATA_DIR, FIGURE_DIR, OMEGA_CDM_PLANCK
from cmbpeaks.keq import compute_ell_eq
from cmbpeaks.sweep import SweepResult


def main() -> int:
    result = SweepResult.load(DATA_DIR / "sweep_fixed_theta_s.npz")
    omega_cdm = result.param_values
    h = result.h
    ref_idx = int(np.argmin(np.abs(omega_cdm - OMEGA_CDM_PLANCK)))

    _, _, ell_eq = compute_ell_eq(omega_cdm, h)
    peak_dls = result.peak_dls
    peak_ells = result.peak_ells
    n_grid, n_peaks = peak_dls.shape

    x_by_peak = [peak_ells[:, p] / ell_eq for p in range(n_peaks)]
    lnD_by_peak = [np.log(peak_dls[:, p]) for p in range(n_peaks)]

    print("x_ref (at omega_cdm=0.12) per peak:")
    for p in range(n_peaks):
        print(f"  peak {p + 1}: x_ref = {x_by_peak[p][ref_idx]:.2f}")

    # ---------------- F1: shared shape + per-peak offsets ----------------
    x_all = np.concatenate(x_by_peak)
    lnD_all = np.concatenate(lnD_by_peak)
    peak_id = np.concatenate([np.full(n_grid, p) for p in range(n_peaks)])

    # design matrix: 3 one-hot offset columns + shared quadratic shape (x, x^2)
    onehot = np.eye(n_peaks)[peak_id]
    shape_cols = np.stack([x_all, x_all**2], axis=1)
    X = np.concatenate([onehot, shape_cols], axis=1)
    coeffs, *_ = np.linalg.lstsq(X, lnD_all, rcond=None)
    offsets = coeffs[:n_peaks]
    shape_coeffs = coeffs[n_peaks:]

    lnD_pred = X @ coeffs
    resid = lnD_all - lnD_pred
    rms_f1 = np.sqrt(np.mean(resid**2))

    print(f"\n=== F1: shared quadratic shape + 3 offsets ===")
    print(f"RMS residual: {rms_f1:.4f}  (Test E shared-fit RMS was 0.162)")
    print("fitted offsets (ln A_peak):")
    for p in range(n_peaks):
        print(f"  peak {p + 1}: offset = {offsets[p]:.4f}   "
              f"ln(D_ref) = {lnD_by_peak[p][ref_idx]:.4f}")
    print("per-peak RMS residual:")
    for p in range(n_peaks):
        m = peak_id == p
        print(f"  peak {p + 1}: {np.sqrt(np.mean(resid[m] ** 2)):.4f}")

    # ---------------- F2: log-log slope, offset-free ----------------
    print("\n=== F2: d(ln D_peak) / d(ln x), offset-free ===")

    def slope_finite_diff(x, lnD):
        order = np.argsort(x)
        return x[order], np.gradient(lnD[order], np.log(x[order]))

    def slope_smooth_fit(x, lnD, deg=2):
        c = np.polyfit(x, lnD, deg)
        dc = np.polyder(c)
        # d(lnD)/d(lnx) = x * d(lnD)/dx
        return lambda xq: xq * np.polyval(dc, xq)

    slopes_fd = {}
    noise_floor = {}
    for p in range(n_peaks):
        x_sorted, s_fd = slope_finite_diff(x_by_peak[p], lnD_by_peak[p])
        slopes_fd[p] = (x_sorted, s_fd)
        fit_fn = slope_smooth_fit(x_by_peak[p], lnD_by_peak[p])
        s_fit_at_fd = fit_fn(x_sorted)
        noise = np.sqrt(np.mean((s_fd - s_fit_at_fd) ** 2))
        noise_floor[p] = noise
        print(f"  peak {p + 1}: finite-diff vs smooth-fit self-consistency RMS = {noise:.4f}"
              f"  (x range {x_sorted.min():.2f}-{x_sorted.max():.2f})")

    x2, s2 = slopes_fd[1]
    x3, s3 = slopes_fd[2]
    lo, hi = max(x2.min(), x3.min()), min(x2.max(), x3.max())
    print(f"\npeak2/peak3 overlap region: x in [{lo:.2f}, {hi:.2f}]")

    x_common = np.linspace(lo, hi, 25)
    s2_common = np.interp(x_common, x2, s2)
    s3_common = np.interp(x_common, x3, s3)
    diff = s2_common - s3_common
    combined_noise = np.sqrt(noise_floor[1] ** 2 + noise_floor[2] ** 2)

    print(f"peak2 vs peak3 derivative in overlap: mean diff = {diff.mean():+.4f}, "
          f"RMS diff = {np.sqrt(np.mean(diff**2)):.4f}")
    print(f"combined self-consistency noise floor (peak2, peak3): {combined_noise:.4f}")
    print(f"ratio, RMS diff / noise floor: {np.sqrt(np.mean(diff**2)) / combined_noise:.2f}x")

    print("\nx    d(lnD2)/d(lnx)   d(lnD3)/d(lnx)   diff")
    for xc, a, b in zip(x_common, s2_common, s3_common):
        print(f"  {xc:.2f}    {a:+.4f}          {b:+.4f}          {a - b:+.4f}")

    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    markers = ["o", "s", "^"]
    colors = ["tab:blue", "tab:orange", "tab:green"]
    for p in range(n_peaks):
        ax1.plot(x_by_peak[p], lnD_by_peak[p], markers[p], color=colors[p],
                  ms=6, mec="k", mew=0.4, label=f"peak {p + 1} (data)")
        x_line = np.linspace(x_by_peak[p].min(), x_by_peak[p].max(), 100)
        pred_line = offsets[p] + shape_coeffs[0] * x_line + shape_coeffs[1] * x_line**2
        ax1.plot(x_line, pred_line, "--", color=colors[p], lw=1.2)
    ax1.set_xlabel(r"$x = \ell_{\rm peak}/\ell_{eq}$")
    ax1.set_ylabel(r"$\ln D_{\rm peak}$")
    ax1.set_title(f"F1: shared shape + offsets (RMS={rms_f1:.3f})")
    ax1.legend(fontsize=8)

    for p, (x_s, s_fd) in slopes_fd.items():
        ax2.plot(x_s, s_fd, markers[p] + "-", color=colors[p], ms=5,
                  mec="k", mew=0.3, label=f"peak {p + 1}")
    ax2.axvspan(lo, hi, color="0.85", zorder=0, label="peak2/3 overlap")
    ax2.set_xlabel(r"$x = \ell_{\rm peak}/\ell_{eq}$")
    ax2.set_ylabel(r"$d\ln D_{\rm peak} / d\ln x$")
    ax2.set_title("F2: log-log slope (offset-free)")
    ax2.legend(fontsize=8)

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURE_DIR / "07_test_f_corrected_collapse.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
