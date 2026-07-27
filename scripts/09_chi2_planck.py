"""Stage 7: diagonal chi^2 of the cached baseline against Planck's binned TT data.

This is NOT a likelihood analysis -- see PLAN.md's Stage 7 section and
README.md for the full caveats. Three reasons in brief: (1) Planck's bandpowers
are correlated bin to bin and this uses diagonal errors only, so the resulting
chi^2 has no calibrated statistical interpretation; (2) the model is sampled at
each bin's effective multipole via linear interpolation rather than integrated
against the bin's window function; (3) the model parameters came from Planck's
own fit to this data, so a good chi^2 shows pipeline consistency, not an
independent confirmation of LCDM.

The number that actually means something is the comparison between two chi^2
values computed the same way: our cached CLASS spectrum against Planck's `Dl`
column, and Planck's own `BestFit` column against that same `Dl` column. The
second is the floor -- what the diagonal method gives for a model that
genuinely is the best fit -- so "ours is close to Planck's" is the expected,
boring, correct outcome.

No CLASS runs -- reads data/baseline_Dl.npz (written by scripts/01_baseline.py)
and the committed Planck file via cmbpeaks.planck.
"""

import sys

import numpy as np

from cmbpeaks.config import DATA_DIR, FIGURE_DIR
from cmbpeaks.planck import bin_theory_to_planck, load_planck_tt


def chi_square(model: np.ndarray, data: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    return (model - data) ** 2 / sigma**2


def main() -> int:
    baseline = np.load(DATA_DIR / "baseline_Dl.npz")
    ell, dl = baseline["ell"], baseline["dl"]

    planck = load_planck_tt()

    # Restrict to Planck bins inside the cached spectrum's ell range so
    # interpolation never extrapolates.
    in_range = (planck.ell >= ell.min()) & (planck.ell <= ell.max())
    n_dropped = int((~in_range).sum())
    n_used = int(in_range.sum())
    print(f"cached baseline ell range: {ell.min():.0f}-{ell.max():.0f}")
    print(f"Planck binned ell range:   {planck.ell.min():.2f}-{planck.ell.max():.2f}")
    print(f"bins used: {n_used}/{len(planck.ell)} ({n_dropped} dropped as out of range)")

    p_ell = planck.ell[in_range]
    p_dl = planck.dl[in_range]
    p_err_low = planck.err_low[in_range]
    p_err_high = planck.err_high[in_range]
    p_best_fit = planck.best_fit[in_range]

    max_asym = float(np.max(np.abs(p_err_high - p_err_low)))
    if max_asym == 0.0:
        print("\n-dDl and +dDl are identical in every used bin -- symmetrising costs nothing.")
    else:
        print(f"\n-dDl and +dDl differ by up to {max_asym:.4f} uK^2 across used bins.")
    sigma = 0.5 * (p_err_low + p_err_high)

    model_at_bins = bin_theory_to_planck(ell, dl, planck)[in_range]

    chi2_ours_per_bin = chi_square(model_at_bins, p_dl, sigma)
    chi2_planck_per_bin = chi_square(p_best_fit, p_dl, sigma)

    chi2_ours = float(chi2_ours_per_bin.sum())
    chi2_planck = float(chi2_planck_per_bin.sum())
    n = n_used  # no parameters fitted here, so dof = N, not N - k

    print(f"\nN (bins used)     = {n}")
    print(f"chi2_ours         = {chi2_ours:.2f}   chi2_ours/N   = {chi2_ours / n:.3f}")
    print(f"chi2_planck       = {chi2_planck:.2f}   chi2_planck/N = {chi2_planck / n:.3f}")
    print(
        "\n(dof = N here because no parameters were fitted -- the baseline\n"
        " params came from the Planck 2018 paper, not from fitting this data.)"
    )

    resid_ours = (model_at_bins - p_dl) / sigma
    resid_planck = (p_best_fit - p_dl) / sigma

    worst = np.argsort(-np.abs(resid_ours))[:5]
    print("\nlargest |residual| bins (ours):")
    print("  ell        model      data       sigma      resid_sigma")
    for i in worst:
        print(f"  {p_ell[i]:8.2f}  {model_at_bins[i]:8.2f}  {p_dl[i]:8.2f}  "
              f"{sigma[i]:7.3f}  {resid_ours[i]:+.2f}")

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 5.5))
    bins = np.linspace(-4, 4, 25)
    ax.hist(resid_ours, bins=bins, density=True, alpha=0.55, color="tab:blue",
            label=f"ours (chi2/N={chi2_ours / n:.2f})", edgecolor="k", linewidth=0.4)
    ax.hist(resid_planck, bins=bins, density=True, alpha=0.55, color="tab:orange",
            label=f"Planck BestFit (chi2/N={chi2_planck / n:.2f})", edgecolor="k", linewidth=0.4)

    x = np.linspace(-4, 4, 200)
    ax.plot(x, np.exp(-x**2 / 2) / np.sqrt(2 * np.pi), "k--", lw=1.2,
            label="unit Gaussian")

    ax.set_xlabel(r"(model $-$ data) / $\sigma$")
    ax.set_ylabel("density")
    ax.set_title("Stage 7: diagonal residuals vs Planck TT bandpowers")
    ax.legend(fontsize=9)

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURE_DIR / "09_chi2_residual_histogram.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"\nwrote {path}")

    print(f"\nresid_ours   mean={resid_ours.mean():+.3f}  std={resid_ours.std():.3f}")
    print(f"resid_planck mean={resid_planck.mean():+.3f}  std={resid_planck.std():.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
