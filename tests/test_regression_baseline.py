"""Regression pins for Stage 1-7 numbers (docs/STAGE8_SPEC.md section 6b).

Stage 8 touches run_class, planck.py and sweep.py to add polarisation
support. None of that is allowed to move a single Stage 1-7 number. This
recomputes the baseline TT spectrum through the real pipeline (CLASS
included) and checks the cached Stage 2 sweep, against values recorded
before Stage 8 started.

Requires classy; skipped if it isn't installed, same as every other place in
this project that calls run_class.
"""

from __future__ import annotations

import pytest

pytest.importorskip("classy")

from cmbpeaks.config import DATA_DIR
from cmbpeaks.peaks import find_acoustic_peaks
from cmbpeaks.spectra import baseline_params, run_class
from cmbpeaks.sweep import SweepResult


def test_baseline_tt_peak_unchanged():
    """Stage 1: first peak at ell=220.3, Dl=5730 uK^2 -- CLASS's own output,
    not Planck's measured 220.6/5733 (that's the benchmark run_class is
    compared against in scripts/01_baseline.py, not what it must equal)."""
    ell, dl, _ = run_class(baseline_params(), lensed=True)
    peaks = find_acoustic_peaks(ell, dl, n_peaks=3)

    assert peaks[0].ell == pytest.approx(220.3, abs=0.1)
    assert peaks[0].dl == pytest.approx(5730, abs=1)


def test_stage2_ratio_endpoints_unchanged():
    """Stage 2: fixed_theta_s omega_cdm sweep, grid endpoints (PLAN.md)."""
    path = DATA_DIR / "sweep_fixed_theta_s.npz"
    if not path.exists():
        pytest.skip(f"{path} not present -- regenerate with scripts/02_sweep.py")
    result = SweepResult.load(path)

    assert result.d1_over_d2[0] == pytest.approx(2.311, abs=0.01)
    assert result.d1_over_d2[-1] == pytest.approx(2.174, abs=0.01)
    assert result.d3_over_d2[0] == pytest.approx(0.756, abs=0.01)
    assert result.d3_over_d2[-1] == pytest.approx(1.151, abs=0.01)
