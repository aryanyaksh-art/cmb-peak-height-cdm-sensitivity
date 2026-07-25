"""Stage 5 Test D follow-ups: geometric-mean turnover prediction, Omega_Lambda check.

D1. The ratio D_ell(omega)/D_ell(0.12) mixes two spectra with two different
    ell_eq values, so its turnover should sit near sqrt(ell_eq(omega) *
    ell_eq(0.12)), not at ell_eq(omega) alone. Compare that geometric mean
    against the empirical turnover.

D2. Omega_Lambda = 1 - (omega_m + omega_r)/h^2 at every cached grid point,
    using h from the sweep. Flag points where it's <= 0.05 (no dark energy
    left, D_A there isn't trustworthy), then redo D1 restricted to
    Omega_Lambda > 0.3.

No CLASS runs -- reuses data/sweep_fixed_theta_s.npz and the same closed-form
D_A machinery as scripts/04b_keq_test.py.
"""

import sys

import numpy as np

from cmbpeaks.config import DATA_DIR, OMEGA_CDM_PLANCK
from cmbpeaks.keq import compute_ell_eq
from cmbpeaks.sweep import SweepResult


def main() -> int:
    result = SweepResult.load(DATA_DIR / "sweep_fixed_theta_s.npz")
    omega_cdm = result.omega_cdm
    h = result.h
    ref_idx = int(np.argmin(np.abs(omega_cdm - OMEGA_CDM_PLANCK)))

    omega_m, omega_lambda, ell_eq = compute_ell_eq(omega_cdm, h)

    print("=== D2: Omega_Lambda across the grid ===")
    print("omega_cdm    h        Omega_Lambda")
    for oc, hi, ol in zip(omega_cdm, h, omega_lambda):
        flag = "  <-- <= 0.05, no dark energy left, D_A untrustworthy" if ol <= 0.05 else ""
        print(f"  {oc:.4f}   {hi:.4f}    {ol:+.4f}{flag}")

    ell_eq_ref = ell_eq[ref_idx]

    spectra = result.spectra
    ell = next(s[0] for s in spectra if s is not None)
    ref_dl = spectra[ref_idx][1]
    mask = (ell >= 40) & (ell <= 400)

    print("\n=== D1: geometric-mean turnover prediction ===")
    print("omega_cdm  Omega_L   ell_eq(w)  geo_mean   ell_turnover  residual  rel_resid")
    rows = []
    for i, (oc, s, ol) in enumerate(zip(omega_cdm, spectra, omega_lambda)):
        if s is None or i == ref_idx:
            continue
        ratio = s[1] / ref_dl
        ell_w, r_w = ell[mask], ratio[mask]
        idx = np.argmax(r_w) if oc < OMEGA_CDM_PLANCK else np.argmin(r_w)
        ell_turn = ell_w[idx]
        geo_mean = np.sqrt(ell_eq[i] * ell_eq_ref)
        resid = ell_turn - geo_mean
        rel = resid / ell_turn
        rows.append((oc, ol, ell_eq[i], geo_mean, ell_turn, resid, rel))
        print(f"  {oc:.4f}    {ol:+.3f}   {ell_eq[i]:7.1f}   {geo_mean:7.1f}   "
              f"{ell_turn:7.1f}      {resid:+6.1f}   {rel:+.1%}")

    print("\n=== D1, restricted to Omega_Lambda > 0.3 ===")
    print("omega_cdm  Omega_L   geo_mean   ell_turnover  residual  rel_resid")
    restricted = [r for r in rows if r[1] > 0.3]
    for oc, ol, le, geo_mean, ell_turn, resid, rel in restricted:
        print(f"  {oc:.4f}    {ol:+.3f}   {geo_mean:7.1f}   {ell_turn:7.1f}      "
              f"{resid:+6.1f}   {rel:+.1%}")

    all_rel = np.array([r[6] for r in rows])
    restr_rel = np.array([r[6] for r in restricted])
    print(f"\nmean |relative residual|, all points:        {np.abs(all_rel).mean():.1%}")
    print(f"mean |relative residual|, Omega_L > 0.3 only: {np.abs(restr_rel).mean():.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
