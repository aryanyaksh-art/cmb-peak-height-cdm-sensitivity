"""Load the Planck 2018 binned power spectra (TT, EE, TE).

Files: ``COM_PowerSpect_CMB-{TT,EE,TE}-binned_R3.0x.txt`` from the Planck
Legacy Archive (mirrored at IRSA/IPAC). All three share the same column
layout:

    # l    Dl    -dDl    +dDl    BestFit

The band powers are D_ell already in microK^2 (TE can be negative -- it
crosses zero), so they overlay a converted CLASS curve with no further
scaling. Some other Planck products -- notably the
``...minimum-theory_R3.01.txt`` files -- are C_ell instead, so read the header
before trusting any of them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .config import PLANCK_TT_BINNED


@dataclass
class PlanckBandpowers:
    spectrum: str  # "TT", "EE", or "TE"
    ell: np.ndarray  # effective bin multipole, generally non-integer
    dl: np.ndarray  # band power, microK^2
    err_low: np.ndarray
    err_high: np.ndarray
    best_fit: np.ndarray  # Planck's own LCDM best fit, microK^2

    @property
    def yerr(self) -> np.ndarray:
        """Asymmetric error array shaped for matplotlib's errorbar."""
        return np.vstack([self.err_low, self.err_high])


# Alias kept for code (and imports) written back when this was TT-only.
PlanckTT = PlanckBandpowers


def load_planck_spectrum(path: Path, spectrum: str = "TT") -> PlanckBandpowers:
    """Load a Planck binned bandpower file. EE and TE share TT's column layout."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run scripts/fetch_planck_data.py, or download it "
            f"directly -- see the PLANCK_*_BINNED_URL constants in config.py "
            f"(EE/TE must be R3.02, not R3.01; see the comment there)."
        )
    d = np.loadtxt(path)
    return PlanckBandpowers(
        spectrum=spectrum,
        ell=d[:, 0],
        dl=d[:, 1],
        err_low=d[:, 2],
        err_high=d[:, 3],
        best_fit=d[:, 4],
    )


def load_planck_tt(path=PLANCK_TT_BINNED) -> PlanckBandpowers:
    return load_planck_spectrum(path, spectrum="TT")


def bin_theory_to_planck(
    ell: np.ndarray, dl: np.ndarray, planck: PlanckBandpowers
) -> np.ndarray:
    """Interpolate a theory curve onto the Planck bin centres.

    This is a convenience for residual plots and nothing more. Real bandpowers
    are weighted averages over each bin's window function, not point samples at
    the effective multipole, so treat any chi^2 built on this as a rough
    diagonal-only goodness-of-fit check rather than a likelihood.
    """
    return np.interp(planck.ell, ell, dl)
