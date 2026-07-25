"""Peak finder tests on a synthetic spectrum, no CLASS required."""

import numpy as np
import pytest

from cmbpeaks.peaks import find_acoustic_peaks, peak_ratios


def synthetic_spectrum(heights=(5733.0, 2586.0, 2518.0),
                       positions=(220.6, 538.1, 809.8),
                       widths=(60.0, 70.0, 75.0)):
    """Three Gaussian bumps roughly where Planck's peaks sit.

    Widths are narrow enough that neighbouring bumps don't overlap and pull the
    fitted positions -- this fixture tests the finder, not Gaussian blending.
    """
    ell = np.arange(2, 2501, dtype=float)
    dl = np.full_like(ell, 100.0)
    for h, p, w in zip(heights, positions, widths):
        dl += h * np.exp(-0.5 * ((ell - p) / w) ** 2)
    return ell, dl


def test_finds_three_peaks():
    ell, dl = synthetic_spectrum()
    peaks = find_acoustic_peaks(ell, dl, n_peaks=3)
    assert len(peaks) == 3
    assert peaks[0].ell == pytest.approx(220.6, abs=5)
    assert peaks[1].ell == pytest.approx(538.1, abs=5)
    assert peaks[2].ell == pytest.approx(809.8, abs=5)


def test_parabola_refinement_beats_integer_sampling():
    """Refined positions should be non-integer, i.e. actually interpolating."""
    ell, dl = synthetic_spectrum(positions=(220.6, 538.1, 809.8))
    peaks = find_acoustic_peaks(ell, dl, n_peaks=3)
    assert any(abs(p.ell - round(p.ell)) > 1e-6 for p in peaks)


def test_rejects_spectrum_with_too_few_peaks():
    ell, dl = synthetic_spectrum(heights=(5733.0,), positions=(220.6,),
                                 widths=(60.0,))
    with pytest.raises(ValueError, match="found 1 peaks"):
        find_acoustic_peaks(ell, dl, n_peaks=3)


def test_rejects_first_peak_in_wrong_place():
    """A first peak far from ell~220 means the finder caught something else."""
    ell, dl = synthetic_spectrum(heights=(5733.0,), positions=(1000.0,),
                                 widths=(60.0,))
    with pytest.raises(ValueError, match="outside the expected"):
        find_acoustic_peaks(ell, dl, n_peaks=1)


def test_ratios():
    ell, dl = synthetic_spectrum()
    ratios = peak_ratios(find_acoustic_peaks(ell, dl, n_peaks=3))
    assert ratios["D1_over_D2"] > 1.5
    assert 0.8 < ratios["D3_over_D2"] < 1.2
