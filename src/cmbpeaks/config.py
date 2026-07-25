"""Cosmological parameters and project-wide constants.

All parameter names are the exact strings ``classy`` expects. Two naming traps
worth keeping straight:

- ``omega_b`` (lowercase) is the *physical* density Omega_b * h^2.
  ``Omega_b`` (capital) is the fractional density. They are not interchangeable.
- ``'ln10^{10}A_s'`` is a literal key string, braces and all.
"""

from pathlib import Path

# --- Paths -------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
FIGURE_DIR = ROOT / "figures"

PLANCK_TT_BINNED = DATA_DIR / "COM_PowerSpect_CMB-TT-binned_R3.01.txt"
PLANCK_TT_BINNED_URL = (
    "https://irsa.ipac.caltech.edu/data/Planck/release_3/"
    "ancillary-data/cosmoparams/COM_PowerSpect_CMB-TT-binned_R3.01.txt"
)

# --- Baseline cosmology ------------------------------------------------------

L_MAX = 2500

# Planck 2018 base-LCDM best fit, TT,TE,EE+lowE+lensing (arXiv:1807.06209).
# Neutrinos follow the Planck baseline: one massive eigenstate at 0.06 eV plus
# 2.0328 ultra-relativistic species, giving N_eff = 3.044. Dropping the massive
# neutrino shifts the high-l spectrum at the ~1% level, so it stays in.
PLANCK_2018_BASE = {
    "output": "tCl,pCl,lCl",
    "lensing": "yes",
    "l_max_scalars": L_MAX,
    "omega_b": 0.02237,
    "omega_cdm": 0.1200,
    "h": 0.6736,
    "ln10^{10}A_s": 3.044,
    "n_s": 0.9649,
    "tau_reio": 0.0544,
    "T_cmb": 2.7255,
    "N_ur": 2.0328,
    "N_ncdm": 1,
    "m_ncdm": 0.06,
}

# Omega_Lambda is deliberately absent. CLASS enforces spatial flatness through
# the closure equation sum_i Omega_i = 1 + Omega_k and fills in the first
# unspecified dark-energy component. Setting it by hand would break flatness as
# omega_cdm varies during the sweep.

# Planck 2018 acoustic scale, for the fixed-theta_s branch of the sweep.
# Passing this means dropping 'h' -- CLASS accepts exactly one of h, H0, or
# 100*theta_s and errors out if the Hubble sector is over-determined.
THETA_S_100 = 1.04092

# --- Measured benchmarks -----------------------------------------------------

# Planck 2018 I (arXiv:1807.06205), Table 5. Used as acceptance tests, not as
# fitted quantities -- nothing in this project measures these.
PLANCK_PEAKS = {
    1: {"ell": 220.6, "ell_err": 0.6, "Dl": 5733.0, "Dl_err": 39.0},
    2: {"ell": 538.1, "ell_err": 1.3, "Dl": 2586.0, "Dl_err": 23.0},
    3: {"ell": 809.8, "ell_err": 1.0, "Dl": 2518.0, "Dl_err": 17.0},
}

# --- Sweep grid --------------------------------------------------------------

OMEGA_CDM_GRID_MIN = 0.05
OMEGA_CDM_GRID_MAX = 0.20
OMEGA_CDM_GRID_N = 16
OMEGA_CDM_PLANCK = 0.1200
