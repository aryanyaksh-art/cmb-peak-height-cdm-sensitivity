"""ell_eq = k_eq * D_A, computed independently of CLASS.

Shared by scripts/04b_keq_test.py, 04c_keq_geomean_check.py, and
06_test_e_scaling_collapse.py so all three use the same numbers rather than
three drifting copies of the same formula.

No CLASS runs: everything here is closed-form. Omega_m0, Omega_r0 come from
omega_b (fixed), the omega_cdm grid, m_ncdm folded in as matter, and the
cached h from a fixed-theta_s sweep. z_star is the Hu & Sugiyama (1996)
fitting formula -- checked against the real baseline, it predicts 1091.9
against CLASS's actual z_rec = 1088.78 at omega_cdm=0.12, 0.3% off. D_C is
the flat-LambdaCDM comoving distance to z_star, which is what "ell = k * D_A"
means in this acoustic-scale context (ell_A = pi * D_C / r_s ~ 301 for this
cosmology) -- not the proper/physical angular diameter distance, which is
only ~13 Mpc at z~1090 and would put ell_eq two orders of magnitude too low.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import quad

from .config import PLANCK_2018_BASE

C_KM_S = 299792.458
OMEGA_B = PLANCK_2018_BASE["omega_b"]
N_UR = PLANCK_2018_BASE["N_ur"]
OMEGA_NCDM = PLANCK_2018_BASE["m_ncdm"] / 93.14  # single massive neutrino, standard conversion
OMEGA_GAMMA_H2 = 2.4728e-5  # calibrated to T_cmb = 2.7255 K, fixed throughout this sweep
OMEGA_UR_H2 = N_UR * (7 / 8) * (4 / 11) ** (4 / 3) * OMEGA_GAMMA_H2
K_EQ_COEFF = 0.073  # Mpc^-1, per omega_m -- user-supplied approximation


def z_star_hu_sugiyama(omega_m: float, omega_b: float = OMEGA_B) -> float:
    """Hu & Sugiyama 1996 fitting formula for the recombination redshift."""
    g1 = 0.0783 * omega_b ** (-0.238) / (1 + 39.5 * omega_b**0.763)
    g2 = 0.560 / (1 + 21.1 * omega_b**1.81)
    return 1048 * (1 + 0.00124 * omega_b ** (-0.738)) * (1 + g1 * omega_m**g2)


def comoving_distance(z_star: float, h: float, omega_m0: float, omega_r0: float) -> float:
    omega_l0 = 1.0 - omega_m0 - omega_r0
    H0 = 100.0 * h

    def inv_E(z):
        return 1.0 / np.sqrt(omega_r0 * (1 + z) ** 4 + omega_m0 * (1 + z) ** 3 + omega_l0)

    integral, _ = quad(inv_E, 0.0, z_star)
    return (C_KM_S / H0) * integral


def compute_ell_eq(omega_cdm: np.ndarray, h: np.ndarray):
    """Return (omega_m, omega_lambda, ell_eq) arrays for a fixed-theta_s grid.

    omega_m is the physical density (no h^2 division); omega_lambda is the
    fractional density today, from flatness.
    """
    omega_cdm = np.asarray(omega_cdm)
    h = np.asarray(h)

    omega_m = OMEGA_B + omega_cdm + OMEGA_NCDM
    omega_r = OMEGA_GAMMA_H2 + OMEGA_UR_H2
    omega_m0 = omega_m / h**2
    omega_r0 = omega_r / h**2
    omega_lambda = 1.0 - (omega_m + omega_r) / h**2

    z_star = np.array([z_star_hu_sugiyama(om) for om in omega_m])
    d_c = np.array([
        comoving_distance(zs, hi, om0, or0)
        for zs, hi, om0, or0 in zip(z_star, h, omega_m0, omega_r0)
    ])
    ell_eq = K_EQ_COEFF * omega_m * d_c
    return omega_m, omega_lambda, ell_eq
