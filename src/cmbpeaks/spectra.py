"""Run CLASS and convert its output to the quantity everyone actually plots.

The one conversion that matters
-------------------------------
``classy``'s ``lensed_cl()`` and ``raw_cl()`` return *dimensionless* C_ell --
the power spectrum of Delta_T / T, with no l(l+1)/2pi prefactor. To get the
familiar D_ell in microkelvin squared you need two multiplications:

    D_ell = l(l+1)/(2*pi) * C_ell * (T_cmb * 1e6)^2

Note that CLASS's *command-line* output already includes the l(l+1)/2pi factor,
so the Python wrapper and the .dat files disagree. Forgetting the T_cmb^2 term
puts the spectrum off by about 10^12, which is the giveaway.
"""

from __future__ import annotations

import numpy as np

from .config import L_MAX, PLANCK_2018_BASE


def cl_to_dl(ell: np.ndarray, cl: np.ndarray, t_cmb_k: float) -> np.ndarray:
    """Convert dimensionless C_ell to D_ell in microK^2."""
    t0_uk = t_cmb_k * 1e6
    return ell * (ell + 1.0) / (2.0 * np.pi) * cl * t0_uk**2


DERIVED_WANTED = ["z_eq", "100*theta_s", "h", "Omega_m", "z_rec"]


def _safe_derived(cosmo, names=DERIVED_WANTED) -> dict:
    """Fetch derived parameters, skipping any name CLASS doesn't recognise.

    ``get_current_derived_parameters`` raises on the whole list if a single name
    is unknown, and the exact set varies between CLASS versions. Falling back to
    one-at-a-time keeps a version bump from breaking the sweep.
    """
    try:
        return cosmo.get_current_derived_parameters(list(names))
    except Exception:  # noqa: BLE001
        out = {}
        for name in names:
            try:
                out.update(cosmo.get_current_derived_parameters([name]))
            except Exception:  # noqa: BLE001
                pass
        return out


def run_class(params: dict, lensed: bool = True, l_max: int = L_MAX):
    """Compute a TT spectrum and return (ell, D_ell in microK^2, derived).

    The CLASS object is always cleaned up, including on failure -- otherwise a
    long sweep leaks memory until it dies.

    Parameters
    ----------
    lensed
        Lensed spectra are what Planck measures, so that's the default. Lensing
        smooths the acoustic peaks by a few percent, which slightly lowers peak
        heights without changing the qualitative trend. Whichever you use, say
        so in the writeup.
    """
    from classy import Class  # imported lazily so tests can run without CLASS

    cosmo = Class()
    try:
        cosmo.set(params)
        cosmo.compute()

        cls = cosmo.lensed_cl(l_max) if lensed else cosmo.raw_cl(l_max)
        ell = cls["ell"][2:]  # ell = 0, 1 are not observable
        dl = cl_to_dl(ell, cls["tt"][2:], cosmo.T_cmb())

        derived = _safe_derived(cosmo)
        return ell, dl, derived
    finally:
        cosmo.struct_cleanup()
        cosmo.empty()


def baseline_params(**overrides) -> dict:
    """Planck 2018 baseline with keyword overrides applied.

    Returns a copy, so sweeps can't accidentally mutate the shared baseline.
    """
    params = dict(PLANCK_2018_BASE)
    params.update(overrides)
    return params


def params_fixed_theta_s(theta_s_100: float, **overrides) -> dict:
    """Baseline with the given parameter(s) changed and the acoustic scale held fixed.

    ``overrides`` is typically a single ``omega_cdm=...`` or ``omega_b=...``
    keyword -- whichever parameter a sweep is varying -- and anything else
    stays at the Planck baseline. Drops ``h`` and passes ``100*theta_s``
    instead, so CLASS solves for H0 by shooting. This is the branch that locks
    peak *positions*, so the resulting figure isolates the amplitude change
    from radiation driving rather than mixing it with geometric shifts in the
    sound horizon and the distance to last scattering.
    """
    params = baseline_params(**overrides)
    params.pop("h", None)
    params.pop("H0", None)
    params["100*theta_s"] = theta_s_100
    return params
