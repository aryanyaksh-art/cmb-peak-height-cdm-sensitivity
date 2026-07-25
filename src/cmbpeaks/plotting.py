"""Figure generation."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from .config import FIGURE_DIR, OMEGA_CDM_PLANCK, PLANCK_PEAKS

PLANCK_ELL_1 = PLANCK_PEAKS[1]["ell"]

plt.rcParams.update(
    {
        "figure.dpi": 130,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "font.size": 11,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "legend.frameon": False,
    }
)


def _save(fig, name: str):
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURE_DIR / name
    fig.savefig(path)
    print(f"wrote {path}")
    return path


def plot_baseline_overlay(ell, dl, planck, peaks=None, name="01_baseline_overlay.png"):
    """Baseline LCDM curve over the Planck 2018 binned band powers."""
    fig, (ax, axr) = plt.subplots(
        2, 1, figsize=(9, 7), sharex=True, height_ratios=[3, 1]
    )

    ax.errorbar(
        planck.ell,
        planck.dl,
        yerr=planck.yerr,
        fmt=".",
        color="0.3",
        ms=5,
        elinewidth=1,
        label="Planck 2018 (binned TT)",
    )
    ax.plot(ell, dl, color="crimson", lw=1.6, label="CLASS $\\Lambda$CDM (lensed)")

    if peaks:
        for i, p in enumerate(peaks, start=1):
            ax.annotate(
                f"{i}",
                xy=(p.ell, p.dl),
                xytext=(0, 9),
                textcoords="offset points",
                ha="center",
                color="crimson",
                fontsize=10,
            )

    ax.set_ylabel(r"$D_\ell^{TT}\ [\mu K^2]$")
    ax.legend(loc="upper right")
    ax.set_title("CMB temperature power spectrum: CLASS vs Planck 2018")

    resid = np.interp(planck.ell, ell, dl) - planck.dl
    sigma = 0.5 * (planck.err_low + planck.err_high)
    axr.errorbar(planck.ell, resid / sigma, yerr=1.0, fmt=".", color="0.3", ms=4)
    axr.axhline(0, color="crimson", lw=1)
    axr.set_ylabel(r"$\Delta / \sigma$")
    axr.set_xlabel(r"multipole $\ell$")
    axr.set_ylim(-5, 5)

    return _save(fig, name)


def plot_sweep(result, name="02_sweep_ratio.png"):
    """Peak-height ratios, matter-radiation equality, and ell_1 vs omega_cdm.

    The third panel shows how far the first peak wanders across the grid.
    Read it against the fixed_h version rather than on its own: absolute
    spread in ell is the wrong unit for comparing modes, because rescaling
    the acoustic scale moves higher peaks further in ell than lower ones.
    On fractional spread (spread / peak position) the fixed_theta_s sweep
    holds peaks 2 and 3 to ~2% against ~16-20% at fixed h. ell_1 is the
    loosest of the three at 4.5%, so this panel is the *weakest* evidence
    that the shooting solver locked theta_s, not the strongest -- see the
    Methodology section of README.md for the full comparison.
    """
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 9.5), sharex=True)

    ax1.plot(result.omega_cdm, result.d1_over_d2, "o-", label=r"$D_1/D_2$")
    ax1.plot(result.omega_cdm, result.d3_over_d2, "s-", label=r"$D_3/D_2$")
    ax1.axvline(OMEGA_CDM_PLANCK, color="0.5", ls="--", lw=1)
    ax1.annotate(
        "Planck 2018\n$\\omega_{cdm}=0.1200$",
        xy=(OMEGA_CDM_PLANCK, ax1.get_ylim()[1]),
        xytext=(4, -4),
        textcoords="offset points",
        va="top",
        fontsize=9,
        color="0.4",
    )
    ax1.set_ylabel("peak-height ratio")
    ax1.legend()
    ax1.set_title(f"Acoustic peak ratios vs CDM density ({result.mode})")

    ax2.plot(result.omega_cdm, result.z_eq, "o-", color="darkgreen")
    ax2.axvline(OMEGA_CDM_PLANCK, color="0.5", ls="--", lw=1)
    ax2.set_ylabel(r"$z_{eq}$")

    ell_1 = result.peak_ells[:, 0]
    ax3.plot(result.omega_cdm, ell_1, "o-", color="darkorange")
    ax3.axvline(OMEGA_CDM_PLANCK, color="0.5", ls="--", lw=1)
    ax3.axhline(PLANCK_ELL_1, color="0.5", ls=":", lw=1.2,
                label=f"Planck $\\ell_1={PLANCK_ELL_1:.1f}$")
    ax3.set_ylabel(r"$\ell_1$")
    ax3.set_xlabel(r"$\omega_{cdm} = \Omega_c h^2$")
    ax3.legend(loc="best", fontsize=9)
    if result.mode == "fixed_theta_s":
        # Pinned rather than autoscaled: a flat line only *reads* as flat if
        # the axis isn't zoomed into a sub-1-ell wobble.
        ax3.set_ylim(PLANCK_ELL_1 - 40, PLANCK_ELL_1 + 40)

    return _save(fig, name)


def plot_paired_sweeps(
    res_fixed_h, res_fixed_theta, name="03_fixed_h_vs_fixed_theta.png"
):
    """Side-by-side spectra for both sweep modes.

    Requires both sweeps to have been run with keep_spectra=True. The left panel
    shows peaks sliding horizontally as well as changing height; the right panel
    locks the positions so only the amplitude effect remains.
    """
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    titles = [
        r"Fixed $h$ — positions and amplitudes both move",
        r"Fixed $100\theta_s$ — positions locked to ~2%, amplitude isolated",
    ]

    for ax, res, title in zip(axes, (res_fixed_h, res_fixed_theta), titles):
        spectra = [s for s in res.spectra if s is not None]
        if not spectra:
            ax.text(0.5, 0.5, "no spectra retained\n(run with keep_spectra=True)",
                    ha="center", va="center", transform=ax.transAxes)
            continue
        cmap = plt.cm.viridis(np.linspace(0, 1, len(spectra)))
        oc_vals = [oc for oc, s in zip(res.omega_cdm, res.spectra) if s is not None]
        for (ell, dl), c, oc in zip(spectra, cmap, oc_vals):
            ax.plot(ell, dl, color=c, lw=1.1)
        sm = plt.cm.ScalarMappable(
            cmap="viridis",
            norm=plt.Normalize(min(oc_vals), max(oc_vals)),
        )
        fig.colorbar(sm, ax=ax, label=r"$\omega_{cdm}$")
        ax.set_xlim(0, 1500)
        ax.set_xlabel(r"multipole $\ell$")
        ax.set_title(title, fontsize=11)

    axes[0].set_ylabel(r"$D_\ell^{TT}\ [\mu K^2]$")
    return _save(fig, name)


def report_benchmarks(peaks) -> bool:
    """Print computed peaks next to the Planck 2018 measured values.

    This is a reproduction check, not a measurement -- these Planck numbers are
    the target, not a result derived here.
    """
    print("\n  peak   ell (CLASS)   ell (Planck)    Dl (CLASS)   Dl (Planck)")
    ok = True
    for i, p in enumerate(peaks[:3], start=1):
        ref = PLANCK_PEAKS[i]
        d_ell = abs(p.ell - ref["ell"])
        d_dl = abs(p.dl - ref["Dl"]) / ref["Dl"]
        flag = "" if (d_ell < 5 and d_dl < 0.03) else "   <-- off"
        ok = ok and not flag
        print(
            f"    {i}      {p.ell:8.1f}      {ref['ell']:8.1f}     "
            f"{p.dl:9.0f}     {ref['Dl']:9.0f}{flag}"
        )
    return ok
