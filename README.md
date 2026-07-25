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

That is the standard picture, and the sweep below shows it is incomplete. It
predicts D1/D2 should rise with `omega_cdm`; measured, the ratio falls. See
"What the peak ratios do."

**Why the third peak is the fingerprint.** Baryon loading alone would leave peak
3 well below peak 2. Dark matter's suppression of radiation driving lifts it
back up. Planck 2018 measures peak 2 at 2586 ± 23 µK² (ℓ = 538.1) and peak 3 at
2518 ± 17 µK² (ℓ = 809.8) — essentially equal. That near-parity is the direct
evidence that dark matter dominated the matter budget before recombination.

## Methodology

Varying the cold dark matter density is ambiguous until you say what else
stays fixed. This project runs the same sweep twice, and the difference
between the two panels of `figures/03_fixed_h_vs_fixed_theta.png` is the
point.

### What each sweep isolates

In the **fixed-h** sweep, ω_cdm varies from 0.05 to 0.20 with the Hubble
parameter pinned at 0.6736. Adding matter shrinks the sound horizon at
recombination and shrinks the distance to last scattering, and the two do not
shrink at the same rate, so the angular acoustic scale drifts. Peak positions
slide along with peak heights. Across the grid the first peak moves by 28 in
ℓ, the second by 84, the third by 159 — that is 12.8%, 15.6% and 19.7% of each
peak's position. Nothing in that panel separates a change in amplitude from a
change in geometry.

In the **fixed-100θ_s** sweep, ω_cdm varies over the same range but the
angular acoustic scale is held at the Planck value of 1.04092 and CLASS solves
for h by shooting. The residual position drift falls to 4.5%, 1.85% and 2.0%.
That is roughly a 9× improvement at peaks 2 and 3, and it means the amplitude
changes visible in the right-hand panel are the dark matter physics rather
than the spectrum sliding sideways underneath a fixed axis.

The residual is not solver error. Acoustic peaks do not sit exactly at
nπ/θ_s; radiation driving imposes a phase shift on the oscillations that
itself depends on the matter density, so peak positions move slightly even at
fixed θ_s. The first peak drifts about 2.3× more than peaks 2 and 3,
consistent with an additional large-scale contribution — plausibly early ISW,
though this project does not establish that.

In both sweeps `Omega_Lambda` is left unset so CLASS's closure equation keeps
the universe spatially flat as `omega_cdm` changes. Setting it by hand would
break flatness partway through the sweep.

### A quantitative check on the shooting solver

Holding θ_s fixed while raising ω_m forces a specific change in h, and the
size of that change is predictable. The sound horizon scales roughly as
r_s ∝ ω_m^(−0.25) and the angular diameter distance as
D_A ∝ h^(−0.2) ω_m^(−0.4), so θ_s = r_s/D_A ∝ ω_m^(0.15) h^(0.2). Holding θ_s
fixed therefore requires

    h ∝ ω_m^(−3/4)

Across this grid ω_m rises by a factor of 3.07, predicting that h should fall
by 3.07^(−0.75) = 0.429. The measured values are h = 1.085 at ω_cdm = 0.05 and
h = 0.469 at ω_cdm = 0.20, a ratio of 0.432. The fitted exponent is 0.750.

This is the same physics behind the well-known Ω_m h³ ≈ constant CMB
degeneracy direction, calibrated near the Planck point rather than across a
fourfold range in ω_cdm.

Note that h = 1.085 means H₀ = 108.5 km/s/Mpc. The endpoints of this grid are
deliberately unphysical; they exist to expose the trend, not as candidate
cosmologies.

### What the peak ratios do

Across the fixed-θ_s sweep:

- **D1/D2 falls**, 2.31 → 2.17
- **D3/D2 rises**, 0.755 → 1.157
- **z_eq rises**, 1731 → 5315, passing through 3403 at the Planck value of
  ω_cdm = 0.1200 (Planck 2018 quotes 3402 ± 26)

The D3/D2 trend is the dark matter signature. Baryon loading alone would
leave the third peak well below the second; a CDM-dominated matter budget
before recombination suppresses radiation driving and lifts peak 3 back
toward parity with peak 2. The sweep crosses D3/D2 = 1 near the observed
value, and Planck measures peak 2 at 2586 ± 23 µK² and peak 3 at
2518 ± 17 µK² — essentially equal heights.

The D1/D2 trend runs opposite to a naive radiation-driving argument, which
predicts that raising ω_cdm should remove more amplitude from peak 2 than
from peak 1 and so lift the ratio. Measured, it falls. Since D1/D2 falls
while D3/D2 rises, both higher peaks gain on peak 1 as ω_cdm increases, so
whatever dominates has to act preferentially on the first peak at low ω_cdm.
This project records the trend without claiming to have identified the
mechanism.

Ratios are used rather than absolute peak heights because the overall
spectrum amplitude scales as A_s·e^(−2τ). Both are held fixed here, but a
ratio is insensitive to that degeneracy regardless, which is what makes it
the right observable for a sweep of this kind.

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
