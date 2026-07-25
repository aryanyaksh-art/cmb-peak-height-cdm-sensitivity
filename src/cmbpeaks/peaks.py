"""Locate the acoustic peaks in a D_ell spectrum.

Peak finding runs on D_ell rather than C_ell. On raw C_ell the l(l+1) growth and
the Silk damping tail together bury the oscillations; on D_ell the peaks are the
obvious features they look like in every textbook figure.

Acoustic peaks are spaced by roughly Delta_l = 300, so a ``distance`` constraint
of ~80-150 samples rejects numerical wiggles without merging real peaks.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks


@dataclass
class Peak:
    index: int
    ell: float  # sub-integer, from the parabola refinement
    dl: float  # microK^2

    def __repr__(self) -> str:
        return f"Peak(ell={self.ell:.1f}, Dl={self.dl:.0f})"


def _refine(ell: np.ndarray, dl: np.ndarray, idx: int) -> tuple[float, float]:
    """Fit a parabola through three samples to get sub-integer peak position.

    Integer multipole sampling limits raw peak positions to +/-0.5 in ell, which
    is coarse next to Planck's quoted 220.6 +/- 0.6. Three points around the
    maximum give the vertex analytically.
    """
    if idx <= 0 or idx >= len(dl) - 1:
        return float(ell[idx]), float(dl[idx])

    y0, y1, y2 = dl[idx - 1], dl[idx], dl[idx + 1]
    denom = y0 - 2.0 * y1 + y2
    if denom == 0:
        return float(ell[idx]), float(dl[idx])

    offset = 0.5 * (y0 - y2) / denom  # in units of the sample spacing
    step = float(ell[idx + 1] - ell[idx])
    peak_ell = float(ell[idx]) + offset * step
    peak_dl = float(y1 - 0.25 * (y0 - y2) * offset)
    return peak_ell, peak_dl


def find_acoustic_peaks(
    ell: np.ndarray,
    dl: np.ndarray,
    n_peaks: int = 3,
    distance: int = 100,
    prominence: float = 50.0,
    ell_max_search: float = 1500.0,
    first_peak_bounds: tuple[float, float] = (180.0, 280.0),
) -> list[Peak]:
    """Return the first ``n_peaks`` acoustic peaks, ordered by multipole.

    ``ell_max_search`` cuts off before the damping tail, where the peaks get
    shallow and the finder starts returning junk.

    ``first_peak_bounds`` is a sanity window on the first peak's position, not
    a physical constant -- it defaults to Planck's ell_1 +/- 60 but the
    fixed-h sweep branch can drop as low as ~150 at the low-omega_cdm end
    (see PLAN.md), so callers that expect that shift should widen it rather
    than disable the check.

    Raises
    ------
    ValueError
        If fewer than ``n_peaks`` peaks are found, or the first peak falls
        outside ``first_peak_bounds``. Both checks matter for the sweep: at
        very low omega_cdm the spectrum changes enough that silently
        returning wrong peaks would corrupt the whole ratio curve.
    """
    mask = ell <= ell_max_search
    ell_s, dl_s = ell[mask], dl[mask]

    idx, _ = find_peaks(dl_s, distance=distance, prominence=prominence)
    if len(idx) < n_peaks:
        raise ValueError(
            f"found {len(idx)} peaks below ell={ell_max_search:.0f}, "
            f"need {n_peaks}. Loosen prominence or widen the search range."
        )

    peaks = []
    for i in idx[:n_peaks]:
        peak_ell, peak_dl = _refine(ell_s, dl_s, int(i))
        peaks.append(Peak(index=int(i), ell=peak_ell, dl=peak_dl))

    lo, hi = first_peak_bounds
    if not (lo <= peaks[0].ell <= hi):
        raise ValueError(
            f"first peak at ell={peaks[0].ell:.1f}, outside the expected "
            f"[{lo:.0f}, {hi:.0f}]. The finder probably latched onto a "
            "non-acoustic feature."
        )
    return peaks


def peak_ratios(peaks: list[Peak]) -> dict[str, float]:
    """Peak-height ratios.

    D1/D2 is the headline number for an omega_cdm sweep. D3/D2 is the sharper
    dark-matter fingerprint: baryon loading alone would leave the third peak
    well below the second, and it's dark matter suppressing radiation driving
    that lifts peak 3 back up to near-parity with peak 2.
    """
    out = {"D1_over_D2": peaks[0].dl / peaks[1].dl}
    if len(peaks) >= 3:
        out["D3_over_D2"] = peaks[2].dl / peaks[1].dl
    return out
