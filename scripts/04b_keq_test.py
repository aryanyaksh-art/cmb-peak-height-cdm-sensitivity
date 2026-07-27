"""Stage 5 Test D: does the suppression transition track ell_eq = k_eq * D_A?

No CLASS runs -- everything here comes from data/sweep_fixed_theta_s.npz
(cached spectra + h) plus closed-form cosmology. Note on "D_A from CLASS's
derived parameters": the cached sweep never saved da_rec (sweep.py only
extracts z_eq and h per grid point), and querying it fresh would mean a new
CLASS instance per point, so this recomputes D_A independently:

- Omega_m0, Omega_r0, Omega_Lambda0 from omega_b (fixed), the omega_cdm grid,
  m_ncdm folded in as matter, and the cached h -- all closed-form.
- z_star from the Hu & Sugiyama (1996) fitting formula, standard practice for
  crib estimates of this kind. Checked against the real baseline: predicts
  1091.9 against CLASS's actual z_rec = 1088.78 at omega_cdm=0.12 -- 0.3% off.
- D_C(z_star) = (c/H0) * integral(dz/E(z), 0, z_star), a flat-LambdaCDM
  comoving distance. This -- not the proper/physical angular diameter
  distance da_rec, which is ~13 Mpc at z~1090 and would put ell_eq two orders
  of magnitude too low -- is what "ell = k * D_A" means in this context. It is
  the comoving distance CLASS calls da_rec * (1+z_rec) internally, and what
  the acoustic scale ell_A = pi * D_C / r_s (~301 for this cosmology) uses.
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

    omega_m, _, ell_eq = compute_ell_eq(omega_cdm, h)

    print("omega_cdm    h       omega_m   ell_eq")
    for oc, hi, om, le in zip(omega_cdm, h, omega_m, ell_eq):
        print(f"  {oc:.4f}   {hi:.4f}   {om:.4f}   {le:7.1f}")
    print(f"\nell_eq range: {ell_eq[0]:.1f} -> {ell_eq[-1]:.1f}")

    ref_idx = int(np.argmin(np.abs(omega_cdm - OMEGA_CDM_PLANCK)))
    spectra = result.spectra
    ell = next(s[0] for s in spectra if s is not None)
    ref_dl = spectra[ref_idx][1]

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 6))
    cmap = plt.cm.viridis(np.linspace(0, 1, len(omega_cdm)))
    for i, (oc, s, c) in enumerate(zip(omega_cdm, spectra, cmap)):
        if s is None or i == ref_idx:
            continue
        ratio = s[1] / ref_dl
        ax.plot(ell, ratio, color=c, lw=1.1)
        y_at_eq = np.interp(ell_eq[i], ell, ratio)
        ax.plot(ell_eq[i], y_at_eq, "o", color=c, ms=6, mec="k", mew=0.5)

    ax.axhline(1.0, color="0.5", ls="--", lw=1)
    ax.set_xlim(0, 1500)
    ax.set_xlabel(r"multipole $\ell$")
    ax.set_ylabel(r"$D_\ell(\omega_{cdm}) / D_\ell(\omega_{cdm}=0.12)$")
    ax.set_title(
        r"Suppression vs $\ell$, marked at $\ell_{eq} = k_{eq} D_C$ (fixed $\theta_s$)"
    )
    sm = plt.cm.ScalarMappable(
        cmap="viridis", norm=plt.Normalize(omega_cdm.min(), omega_cdm.max())
    )
    fig.colorbar(sm, ax=ax, label=r"$\omega_{cdm}$")

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURE_DIR / "04b_suppression_vs_keq.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
