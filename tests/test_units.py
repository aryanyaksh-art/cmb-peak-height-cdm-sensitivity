"""Guard against the C_ell -> D_ell unit bug.

These tests don't need CLASS installed; they exercise the conversion in
isolation, which is where the ~10^12 error actually happens.
"""

import numpy as np
import pytest

from cmbpeaks.config import PLANCK_PEAKS
from cmbpeaks.spectra import cl_to_dl


def test_cl_to_dl_prefactor():
    ell = np.array([100.0])
    cl = np.array([1e-10])
    t_cmb = 2.7255
    expected = 100 * 101 / (2 * np.pi) * 1e-10 * (2.7255e6) ** 2
    assert cl_to_dl(ell, cl, t_cmb) == pytest.approx(expected)


def test_realistic_first_peak_magnitude():
    """A first-peak-scale C_ell must land near 5733 microK^2, not 1e-12 or 1e12.

    Catches both a missing T_cmb^2 factor and a missing l(l+1)/2pi factor.
    """
    ell = np.array([220.0])
    # back-solved from D_ell = 5733 at ell = 220: cl = D_ell * 2pi / (ell*(ell+1)) / t0_uk**2
    cl = np.array([9.97e-14])
    dl = cl_to_dl(ell, cl, 2.7255)[0]
    assert 4000 < dl < 8000, f"D_ell = {dl:.3e}, expected order 5.7e3 microK^2"


def test_t_cmb_squared_is_the_giveaway():
    """Dropping T_cmb^2 shifts the answer by roughly 7.4e12."""
    ell, cl = np.array([220.0]), np.array([9.97e-14])
    with_t = cl_to_dl(ell, cl, 2.7255)[0]
    without_t = ell * (ell + 1) / (2 * np.pi) * cl
    assert with_t / without_t[0] == pytest.approx((2.7255e6) ** 2, rel=1e-9)


def test_planck_benchmarks_are_sane():
    """The reference table itself should be internally consistent."""
    assert PLANCK_PEAKS[1]["Dl"] > PLANCK_PEAKS[2]["Dl"]
    # Peaks 2 and 3 within 5% of each other -- the dark-matter fingerprint.
    r = PLANCK_PEAKS[3]["Dl"] / PLANCK_PEAKS[2]["Dl"]
    assert 0.95 < r < 1.0
    ells = [PLANCK_PEAKS[i]["ell"] for i in (1, 2, 3)]
    assert ells == sorted(ells)
