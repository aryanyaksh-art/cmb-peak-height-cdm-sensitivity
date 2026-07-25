"""Load the Planck 2018 binned TT power spectrum.

File: ``COM_PowerSpect_CMB-TT-binned_R3.01.txt`` from the Planck Legacy Archive
(mirrored at IRSA/IPAC). Columns:

    # l    Dl    -dDl    +dDl    BestFit

The band powers are D_ell already in microK^2, so they overlay a converted CLASS
curve with no further scaling. Some other Planck products -- notably the
``...minimum-theory_R3.01.txt`` files -- are C_ell instead, so read the header
before trusting any of them.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import PLANCK_TT_BINNED, PLANCK_TT_BINNED_URL


@dataclass
class PlanckTT:
    ell: np.ndarray  # effective bin multipole, generally non-integer
    dl: np.ndarray  # band power, microK^2
    err_low: np.ndarray
    err_high: np.ndarray
    best_fit: np.ndarray  # Planck's own LCDM best fit, microK^2

    @property
    def yerr(self) -> np.ndarray:
        """Asymmetric error array shaped for matplotlib's errorbar."""
        return np.vstack([self.err_low, self.err_high])


def load_planck_tt(path=PLANCK_TT_BINNED) -> PlanckTT:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run scripts/fetch_planck_data.py, or download "
            f"it directly from:\n  {PLANCK_TT_BINNED_URL}"
        )
    d = np.loadtxt(path)
    return PlanckTT(
        ell=d[:, 0], dl=d[:, 1], err_low=d[:, 2], err_high=d[:, 3], best_fit=d[:, 4]
    )


def bin_theory_to_planck(
    ell: np.ndarray, dl: np.ndarray, planck: PlanckTT
) -> np.ndarray:
    """Interpolate a theory curve onto the Planck bin centres.

    This is a convenience for residual plots and nothing more. Real bandpowers
    are weighted averages over each bin's window function, not point samples at
    the effective multipole, so treat any chi^2 built on this as a rough
    diagonal-only goodness-of-fit check rather than a likelihood.
    """
    return np.interp(planck.ell, ell, dl)
