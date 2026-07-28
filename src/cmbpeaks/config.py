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

# EE and TE MUST be R3.02, not R3.01. This is not a preference -- Planck's
# R3.01 TE and EE binned files have their contents swapped (documented on the
# Planck Legacy Archive wiki): COM_PowerSpect_CMB-TE-binned_R3.01.txt actually
# contains EE, and COM_PowerSpect_CMB-EE-binned_R3.01.txt actually contains
# TE. R3.02 fixed this. Grabbing R3.01 for these two out of habit (because the
# TT file above is R3.01) silently turns every EE conclusion into a TE one.
PLANCK_EE_BINNED = DATA_DIR / "COM_PowerSpect_CMB-EE-binned_R3.02.txt"
PLANCK_EE_BINNED_URL = (
    "https://irsa.ipac.caltech.edu/data/Planck/release_3/"
    "ancillary-data/cosmoparams/COM_PowerSpect_CMB-EE-binned_R3.02.txt"
)
PLANCK_TE_BINNED = DATA_DIR / "COM_PowerSpect_CMB-TE-binned_R3.02.txt"
PLANCK_TE_BINNED_URL = (
    "https://irsa.ipac.caltech.edu/data/Planck/release_3/"
    "ancillary-data/cosmoparams/COM_PowerSpect_CMB-TE-binned_R3.02.txt"
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

# --- EE peak-finder preset (Stage 8) ------------------------------------------

# find_acoustic_peaks' TT defaults (prominence=50.0, first_peak_bounds=(180,280))
# are tuned to TT peak heights of thousands of uK^2 and find nothing in EE,
# whose maxima are ~1-42 uK^2. These are passed explicitly by EE callers; they
# do not change find_acoustic_peaks' own defaults, which stay TT's.
#
# EE_PEAK_PROMINENCE=5.0 sits between the prominence of the five strong acoustic
# maxima found on the baseline curve (ell ~ 395, 688, 990, 1299, 1608; scipy
# prominence 9.4-34.6 uK^2) and a weak local maximum near ell ~ 140 (Dl ~ 1.1
# uK^2, prominence ~0.43 uK^2) that sits well below it. At this preset the weak
# feature is not returned. Whether that feature should count as a peak at all
# -- and if so, how it renumbers everything after it -- is the docs/
# STAGE8_SPEC.md section 5 decision and is deliberately not settled here.
EE_PEAK_PROMINENCE = 5.0
EE_PEAK_FIRST_BOUNDS = (300.0, 500.0)  # brackets the first strong maximum, ell~395
EE_PEAK_ELL_MAX_SEARCH = 1800.0

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

# omega_b grid for the baryon-loading companion sweep (Stage 6). Range chosen
# to bracket Planck's 0.02237 by roughly the same multiplicative factor the
# omega_cdm grid brackets 0.1200, not to match its absolute width -- the two
# parameters have very different natural scales.
OMEGA_B_GRID_MIN = 0.017
OMEGA_B_GRID_MAX = 0.030
OMEGA_B_GRID_N = 16
OMEGA_B_PLANCK = PLANCK_2018_BASE["omega_b"]

# LaTeX labels and Planck reference values for whichever parameter a sweep
# varies, keyed by the CLASS parameter name -- lets plotting stay generic
# across sweeps instead of hardcoding omega_cdm everywhere.
PARAM_LATEX = {
    "omega_cdm": r"\omega_{cdm}",
    "omega_b": r"\omega_b",
}
PARAM_PLANCK = {
    "omega_cdm": OMEGA_CDM_PLANCK,
    "omega_b": OMEGA_B_PLANCK,
}
PARAM_XLABEL = {
    "omega_cdm": r"$\omega_{cdm} = \Omega_c h^2$",
    "omega_b": r"$\omega_b = \Omega_b h^2$",
}
