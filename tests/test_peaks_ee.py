"""EE peak finding on a cached baseline theory curve (Stage 8 step 5).

No CLASS needed: find_acoustic_peaks operates on arrays, and the curve is a
pre-computed cache (data/baseline_Dl_ee.npz), same pattern as the sweep
round-trip fixtures in test_sweep_io.py.

This only checks that the finder locates the acoustic maxima with an
EE-appropriate prominence -- it does not assign EE peaks a TT-peak-style
index or claim which one is "first" in the docs/STAGE8_SPEC.md section 5
sense. That numbering decision is out of scope here.
"""

from __future__ import annotations

import numpy as np
import pytest

from cmbpeaks.config import (
    DATA_DIR,
    EE_PEAK_ELL_MAX_SEARCH,
    EE_PEAK_FIRST_BOUNDS,
    EE_PEAK_PROMINENCE,
)
from cmbpeaks.peaks import find_acoustic_peaks


def _load_cached_ee():
    path = DATA_DIR / "baseline_Dl_ee.npz"
    if not path.exists():
        pytest.skip(f"{path} not present -- regenerate the baseline EE curve")
    d = np.load(path)
    return d["ell"], d["dl"]


def test_ee_prominence_default_finds_nothing():
    """The TT prominence default (50.0) is the trap docs/STAGE8_SPEC.md section
    6 warns about: it's larger than the entire EE signal (~1-42 uK^2)."""
    ell, dl = _load_cached_ee()
    with pytest.raises(ValueError, match="found 0 peaks"):
        find_acoustic_peaks(ell, dl, n_peaks=1)


def test_ee_preset_finds_five_strong_maxima():
    ell, dl = _load_cached_ee()
    peaks = find_acoustic_peaks(
        ell,
        dl,
        n_peaks=5,
        prominence=EE_PEAK_PROMINENCE,
        first_peak_bounds=EE_PEAK_FIRST_BOUNDS,
        ell_max_search=EE_PEAK_ELL_MAX_SEARCH,
    )
    assert len(peaks) == 5

    found_ell = [p.ell for p in peaks]
    expected_ell = [394.7, 687.9, 990.4, 1298.9, 1607.7]
    for got, want in zip(found_ell, expected_ell):
        assert got == pytest.approx(want, abs=1.0)

    # Monotonic in ell -- find_acoustic_peaks returns peaks ordered by position.
    assert found_ell == sorted(found_ell)


def test_ee_weak_feature_appears_below_its_own_prominence():
    """The ell~140 feature (Dl~1.1 uK^2) has prominence ~0.4345 uK^2. Below
    that threshold it's returned as an extra peak; at or above it, it's gone.
    This pins the threshold, it does not decide whether the feature "counts"."""
    ell, dl = _load_cached_ee()

    below = find_acoustic_peaks(
        ell, dl, n_peaks=6, prominence=0.43,
        first_peak_bounds=(100.0, 500.0), ell_max_search=EE_PEAK_ELL_MAX_SEARCH,
    )
    assert len(below) == 6
    assert below[0].ell == pytest.approx(140.1, abs=1.0)

    at_or_above = find_acoustic_peaks(
        ell, dl, n_peaks=5, prominence=0.4345,
        first_peak_bounds=EE_PEAK_FIRST_BOUNDS, ell_max_search=EE_PEAK_ELL_MAX_SEARCH,
    )
    assert len(at_or_above) == 5
    assert at_or_above[0].ell == pytest.approx(394.7, abs=1.0)
