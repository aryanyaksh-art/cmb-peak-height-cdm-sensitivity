"""Round-trip tests for SweepResult.save/load, no CLASS required.

These guard the save/load asymmetry found while reading sweep.py: ``mode``
comes back from np.load as a 0-d array rather than a str, and a NaN dl_grid
row must reconstruct as None rather than as an (ell, all-NaN) tuple, or
plot_paired_sweeps's `is not None` filter silently stops working.
"""

import numpy as np
import pytest

from cmbpeaks.sweep import SweepResult


def _synthetic_result(mode="fixed_theta_s", with_spectra=True):
    """Four grid points: three successful, one failed (None/NaN throughout)."""
    n = 4
    n_ell = 20
    omega_cdm = np.linspace(0.05, 0.20, n)
    ell = np.arange(2, 2 + n_ell, dtype=float)

    d1_over_d2 = np.array([2.1, 2.2, np.nan, 2.3])
    d3_over_d2 = np.array([0.95, 0.97, np.nan, 0.99])
    peak_ells = np.array([
        [220.0, 538.0, 810.0],
        [220.1, 538.1, 810.1],
        [np.nan, np.nan, np.nan],
        [220.3, 538.3, 810.3],
    ])
    peak_dls = np.array([
        [5700.0, 2580.0, 2510.0],
        [5710.0, 2590.0, 2520.0],
        [np.nan, np.nan, np.nan],
        [5730.0, 2600.0, 2530.0],
    ])
    z_eq = np.array([1800.0, 2900.0, np.nan, 4900.0])
    h = np.array([0.55, 0.62, np.nan, 0.78])

    spectra = []
    if with_spectra:
        rng = np.random.default_rng(0)
        for i in range(n):
            if i == 2:
                spectra.append(None)  # the failed grid point
            else:
                spectra.append((ell, rng.random(n_ell) * 1000.0))

    return SweepResult(
        mode=mode,
        param_values=omega_cdm,
        d1_over_d2=d1_over_d2,
        d3_over_d2=d3_over_d2,
        peak_ells=peak_ells,
        peak_dls=peak_dls,
        z_eq=z_eq,
        h=h,
        spectra=spectra,
    )


def test_array_fields_round_trip(tmp_path):
    result = _synthetic_result()
    path = tmp_path / "sweep_fixed_theta_s.npz"
    result.save(path)
    loaded = SweepResult.load(path)

    np.testing.assert_allclose(loaded.param_values, result.param_values)
    assert loaded.param == result.param
    np.testing.assert_allclose(loaded.d1_over_d2, result.d1_over_d2, equal_nan=True)
    np.testing.assert_allclose(loaded.d3_over_d2, result.d3_over_d2, equal_nan=True)
    np.testing.assert_allclose(loaded.peak_ells, result.peak_ells, equal_nan=True)
    np.testing.assert_allclose(loaded.peak_dls, result.peak_dls, equal_nan=True)
    np.testing.assert_allclose(loaded.z_eq, result.z_eq, equal_nan=True)
    np.testing.assert_allclose(loaded.h, result.h, equal_nan=True)


def test_mode_round_trips_as_str(tmp_path):
    result = _synthetic_result(mode="fixed_h")
    path = tmp_path / "sweep_fixed_h.npz"
    result.save(path)
    loaded = SweepResult.load(path)

    assert isinstance(loaded.mode, str)
    assert f"sweep_{loaded.mode}.npz" == "sweep_fixed_h.npz"


def test_spectra_repopulated_with_right_shapes(tmp_path):
    result = _synthetic_result()
    path = tmp_path / "sweep.npz"
    result.save(path)
    loaded = SweepResult.load(path)

    assert len(loaded.spectra) == len(result.spectra)
    for orig, got in zip(result.spectra, loaded.spectra):
        if orig is None:
            continue
        ell_orig, dl_orig = orig
        ell_got, dl_got = got
        assert ell_got.shape == ell_orig.shape
        assert dl_got.shape == dl_orig.shape
        np.testing.assert_allclose(ell_got, ell_orig)
        np.testing.assert_allclose(dl_got, dl_orig)


def test_failed_grid_point_comes_back_as_none(tmp_path):
    result = _synthetic_result()
    path = tmp_path / "sweep.npz"
    result.save(path)
    loaded = SweepResult.load(path)

    assert loaded.spectra[2] is None
    assert all(s is not None for i, s in enumerate(loaded.spectra) if i != 2)


def test_empty_spectra_round_trips(tmp_path):
    result = _synthetic_result(with_spectra=False)
    assert result.spectra == []
    path = tmp_path / "sweep_no_spectra.npz"
    result.save(path)  # must not raise despite spectra=[]
    loaded = SweepResult.load(path)

    assert loaded.spectra == []


def test_loads_pre_stage6_npz_without_param_key(tmp_path):
    """Files saved before the omega_b sweep only have an "omega_cdm" key.

    load() must still work on the sweep_*.npz files already committed to
    data/, defaulting param to "omega_cdm" when "param_values" is absent.
    """
    result = _synthetic_result()
    path = tmp_path / "sweep_old_format.npz"
    np.savez_compressed(
        path,
        mode=result.mode,
        omega_cdm=result.param_values,
        d1_over_d2=result.d1_over_d2,
        d3_over_d2=result.d3_over_d2,
        peak_ells=result.peak_ells,
        peak_dls=result.peak_dls,
        z_eq=result.z_eq,
        h=result.h,
    )
    loaded = SweepResult.load(path)

    assert loaded.param == "omega_cdm"
    np.testing.assert_allclose(loaded.param_values, result.param_values)
