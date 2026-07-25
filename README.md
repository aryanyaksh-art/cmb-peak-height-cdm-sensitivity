# CMB Acoustic Peak Heights and the Cold Dark Matter Density

Using the CLASS Boltzmann code, I reproduced the known dependence of the CMB
temperature power spectrum's acoustic-peak heights on the cold dark matter
density, quantified it with a peak-height-ratio parameter sweep, and validated
the baseline model against Planck 2018 data.

**Scope, stated plainly:** this reproduces a textbook result established in the
1990s–2000s (Hu & Sugiyama, Hu & Dodelson) and confirmed by WMAP and Planck. It
is not novel research, and the Planck overlay is a visual comparison, not a
likelihood analysis — nothing here measures Ω_c.

---

## The physics

Two effects shape the acoustic peaks, and they're routinely conflated.

**Baryon loading** produces the odd/even asymmetry. Before recombination,
photons and baryons oscillate as one tightly-coupled fluid inside gravitational
potential wells. Baryons add inertia and gravitating mass but no pressure, which
displaces the oscillation's zero-point deeper into the well — like hanging a
mass on a spring. Compressions (odd peaks: 1st, 3rd) become more extreme than
rarefactions (even peaks: 2nd, 4th). The size of the effect scales with the
baryon-to-photon momentum ratio R ∝ Ω_b h², making the odd/even ratio a
baryometer rather than a dark matter probe.

**Radiation driving** sets the overall amplitude, and this is what dark matter
controls. Modes entering the horizon during radiation domination oscillate in
potentials that are decaying, because radiation pressure resists collapse. The
decay is timed to leave the fluid maximally compressed just as the potential
vanishes, and the simultaneous disappearance of the gravitational redshift
roughly doubles the effect — so those modes get boosted. Cold dark matter is
pressureless and supplies stable wells once it dominates. More `omega_cdm` moves
matter–radiation equality earlier, so the potentials have stopped decaying by
the time most modes oscillate, less driving survives, and the peaks come out
lower.

**Why the third peak is the fingerprint.** Baryon loading alone would leave peak
3 well below peak 2. Dark matter's suppression of radiation driving lifts it
back up. Planck 2018 measures peak 2 at 2586 ± 23 µK² (ℓ = 538.1) and peak 3 at
2518 ± 17 µK² (ℓ = 809.8) — essentially equal. That near-parity is the direct
evidence that dark matter dominated the matter budget before recombination.

## What's held fixed, and why it matters

Varying `omega_cdm` alone is ambiguous until you say what else stays put. The
project runs the sweep twice:

- **Fixed `h`.** Lowering `omega_cdm` changes the sound horizon and the distance
  to last scattering, so peak positions slide as well as heights. Everything
  moves at once.
- **Fixed `100*theta_s` = 1.04092.** CLASS solves for H0 by shooting, peak
  positions lock, and the figure isolates the amplitude change — the actual
  dark-matter physics.

In both cases `Omega_Lambda` is left unset so CLASS's closure equation keeps the
universe spatially flat as `omega_cdm` changes. Setting it by hand would break
flatness partway through the sweep.

## Repository layout

```
src/cmbpeaks/       config, spectra, peak finding, Planck loader, sweep, plots
scripts/            numbered pipeline, run in order
tests/              unit-conversion and peak-finder tests (no CLASS needed)
data/               Planck R3.01 band powers + cached computed spectra
figures/            output
docs/SETUP_WSL.md   environment setup
PLAN.md             staged build order with benchmarks
RESEARCH_BLUEPRINT.md   full technical reference
```

## Running it

CLASS is Linux/macOS only; on Windows use WSL. Setup: `docs/SETUP_WSL.md`.

```bash
pip install -r requirements.txt && pip install -e .
python scripts/00_sanity_check.py
python scripts/fetch_planck_data.py
python scripts/01_baseline.py
python scripts/02_sweep.py
python scripts/03_paired_figures.py
pytest
```

## The unit convention that catches everyone

`classy`'s `lensed_cl()` returns dimensionless C_ℓ — no ℓ(ℓ+1)/2π factor, in
units of (ΔT/T)². Getting to the familiar plot needs both:

```
D_ℓ [µK²] = ℓ(ℓ+1)/(2π) × C_ℓ × (T_cmb × 10⁶)²
```

CLASS's command-line `.dat` output already includes the ℓ(ℓ+1)/2π factor, so
the Python wrapper and the files disagree. A spectrum off by ~10¹² means the
`T_cmb²` term is missing. `tests/test_units.py` exists specifically for this.

## Reproducibility

classy 3.3.4.0 · Planck product `COM_PowerSpect_CMB-TT-binned_R3.01.txt` ·
Planck 2018 base-ΛCDM (TT,TE,EE+lowE+lensing), one massive neutrino at 0.06 eV
(`N_ncdm=1, m_ncdm=0.06, N_ur=2.0328`, N_eff = 3.044) · lensed spectra
throughout.

## References

- Hu & Dodelson 2002, *Ann. Rev. Astron. Astrophys.* **40**, 171
- Hu, "Lecture Notes on CMB Theory" (arXiv:0802.3688); tutorials at
  `background.uchicago.edu`
- Lesgourgues 2011, CLASS overview (arXiv:1104.2932)
- Planck 2018 VI, cosmological parameters (arXiv:1807.06209)
- Planck 2018 I, overview, Table 5 for measured peaks (arXiv:1807.06205)
