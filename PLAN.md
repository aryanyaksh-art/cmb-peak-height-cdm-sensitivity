# Build Plan

Staged build order for the CMB peak-height asymmetry project. Each stage has a
concrete deliverable and a numeric benchmark you can check before moving on.
Full physics reference: `RESEARCH_BLUEPRINT.md`. Tool split: `CLAUDE.md`.

---

## Stage 0 — Environment (WSL)

**Why WSL.** CLASS is supported on Linux and macOS only. `pip install classy`
compiles C source at install time, and the build assumes a POSIX toolchain.
Full instructions: `docs/SETUP_WSL.md`.

Two things that bite people and are worth getting right the first time:

- **Put the venv in the WSL home directory, not in this OneDrive folder.**
  OneDrive tries to sync every file in a venv, and `/mnt/c/...` is slow enough
  under WSL that compiling there is painful. Code lives in the synced folder;
  the environment lives at `~/venvs/cmb`.
- **Pin versions.** `requirements.txt` pins `classy==3.3.4.0`. If you rebuild
  months from now after a NumPy major release, rebuild `classy` in a clean env
  rather than reusing the old one.

**Deliverable:** `python -c "from classy import Class"` succeeds in WSL.
**Benchmark:** `scripts/00_sanity_check.py` prints a positive P(k) and the
installed classy version.

---

## Stage 1 — Baseline spectrum + Planck overlay ✅ DONE 2026-07-25

Results, lensed spectrum, Planck 2018 baseline parameters:

| peak | ℓ (CLASS) | ℓ (Planck) | D_ℓ (CLASS) | D_ℓ (Planck) |
|---|---|---|---|---|
| 1 | 220.3 | 220.6 | 5730 | 5733 |
| 2 | 536.1 | 538.1 | 2593 | 2586 |
| 3 | 812.9 | 809.8 | 2540 | 2518 |

D1/D2 = 2.210, D3/D2 = 0.980. All 9 tests pass. Figure at
`figures/01_baseline_overlay.png`, cached spectrum at `data/baseline_Dl.npz`.



Reproduce the Planck 2018 base-ΛCDM TT spectrum and overlay the binned data.

**Deliverable:** `figures/01_baseline_overlay.png`, plus a saved
`data/baseline_Dl.npz` so later stages don't recompute.

**Benchmarks (from Planck 2018 I, Table 5):**

| Quantity | Target | Tolerance to accept |
|---|---|---|
| First peak position | ℓ = 220.6 | ±3 |
| First peak amplitude | D_ℓ = 5733 µK² | ±2% |
| Second peak | ℓ = 538.1, 2586 µK² | ±5 in ℓ, ±3% |
| Third peak | ℓ = 809.8, 2518 µK² | ±5 in ℓ, ±3% |

If the amplitude is off by ~10¹², the `(T_cmb × 10⁶)²` factor is missing. That
is the single most common bug and `tests/test_units.py` exists to catch it.

**What to state in the writeup:** whether the curve is lensed or unlensed. The
default here is lensed, because that's what Planck measures.

---

## Stage 2 — The `omega_cdm` sweep ✅ DONE 2026-07-25

16-point grid, both modes, ω_cdm ∈ [0.05, 0.20]. No NaN rows in either mode —
the `[180, 280]` first-peak guard held for `fixed_theta_s`; `fixed_h` needed
the widened `(120, 280)` bound (ℓ₁ actually ranges 211.5 → 239.7 there, well
inside the old guard, so it never fired at this grid resolution, but the
widened bound is now in place for anyone who reruns with a lower ω_cdm floor).

| Check | STAGE2_SPEC expectation | Measured |
|---|---|---|
| z_eq at ω_cdm=0.1200 | ≈3400 | 3403 ✅ |
| z_eq range | ≈1750 → 5400 | 1731 → 5315 ✅ |
| D1/D2 trend | rises with ω_cdm | **falls**, 2.31 → 2.17 ❌ opposite sign |
| D3/D2 trend | sign open | rises, 0.755 → 1.157 (matches Hu's framing) |
| ℓ spread (1st/2nd/3rd peak), fixed θ_s | <~2 (absolute ℓ) | 10.0 / 10.0 / 16.1 — i.e. 4.5% / 1.85% / 2.0% of position |
| ℓ spread (1st/2nd/3rd peak), fixed h | tens of ℓ | 28.2 / 84.0 / 159.2 — i.e. 12.8% / 15.6% / 19.7% of position ✅ |
| h, fixed θ_s | rising, 0.55 → 0.78 | **falling**, 1.085 → 0.469 ❌ opposite sign |
| Peaks found | 3 everywhere | ✅ 16/16, no NaN |

The fixed-θ_s ℓ-spread isn't a miss either — "10.0 absolute ℓ" only looks like
it blows past the spec's "<~2" bar because absolute ℓ is the wrong metric for
a comparison across peaks at very different ℓ. As a fraction of peak position
it's 4.5% at peak 1 and under 2% at peaks 2 and 3, against 12.8–19.7% for
fixed h — a ~6–9× improvement, which is the actual claim this check exists to
support.

**Two sign flips from the spec's predictions, not bugs.** Both are reproducible
across coarse (n=4) and full (n=16) grids, consistent with the Stage 1
baseline value at ω_cdm=0.12, and visually confirmed in
`figures/03_fixed_h_vs_fixed_theta.png` (peak 1 visibly shrinks and peak 3
visibly grows as ω_cdm rises, in both modes).

- **h falls, not rises, in fixed_theta_s mode — and quantitatively, not just
  in sign.** Holding θ_s fixed gives h ∝ ω_m^(−3/4), since r_s ∝ ω_m^(−0.25)
  and D_A ∝ h^(−0.2) ω_m^(−0.4). Over the grid ω_m rises 3.07×, predicting an
  h ratio of 3.07^(−0.75) = 0.429; measured 0.469/1.085 = 0.432. Note that
  h = 1.085 means H₀ = 108.5 — the low-ω_cdm end of the grid is deliberately
  unphysical, chosen to expose the trend rather than as a candidate cosmology.
- **D1/D2 falls, not rises.** Radiation driving alone predicts a rise, and
  that prediction is wrong. Baryon loading isn't the explanation either: R =
  3ρ_b/4ρ_γ depends only on ω_b and redshift, not ω_cdm, and this sweep holds
  ω_b fixed, so R at recombination is essentially constant across the whole
  grid — there's no loading-dilution effect to invoke. The more telling fact
  is that D1/D2 falls *while D3/D2 rises*: both higher peaks are gaining on
  peak 1 as ω_cdm increases, so whatever is happening has to preferentially
  boost peak 1 at low ω_cdm rather than suppress peaks 2 and 3 at high ω_cdm.
  Early ISW is the likely candidate — it adds power specifically at the first
  peak's scale and is strongest when the universe hasn't fully left the
  radiation era, i.e. at low ω_cdm — but this is not established here and
  would need a direct calculation to confirm.

Figures: `figures/02_sweep_ratio_fixed_h.png`, `figures/02_sweep_ratio_fixed_theta_s.png`,
`figures/03_fixed_h_vs_fixed_theta.png`. Cached spectra: `data/sweep_fixed_h.npz`,
`data/sweep_fixed_theta_s.npz` (git-ignored; regenerate with `scripts/02_sweep.py`).
14/14 tests pass.

Sweep `omega_cdm` across 0.05–0.20 (bracketing Planck's 0.1200), extract peak
heights, plot the ratio.

**Deliverable:** `figures/02_sweep_ratio.png` — two panels, peak-height ratio
vs `omega_cdm` on top, z_eq vs `omega_cdm` below. The second panel is what
connects cause to effect: `omega_cdm` sets matter–radiation equality, equality
sets how much radiation driving survives, driving sets the peak amplitudes.

**Benchmarks:** monotonic trend across the grid; ≥3 peaks found at every grid
point; first peak lands in ℓ ∈ [180, 280] everywhere. Planck's 0.1200 marked on
the axis.

**Report both ratios.** D₁/D₂ is the obvious one, but D₃/D₂ is the cleaner
dark-matter fingerprint — it's the near-equality of peaks 2 and 3 that says
dark matter dominated the pre-recombination matter budget. Compute both.

---

## Stage 5 — Resolving the D1/D2 anomaly ✅ DONE 2026-07-25

Follow-up investigation into why D1/D2 falls and D3/D2 rises with ω_cdm
(Stage 2's finding, opposite the naive radiation-driving prediction).
Working doc: `STAGE5_SPEC.md` (delete before the next packaging pass, per
its own header).

**Test C — individual peak heights, no CLASS runs.** From the cached
fixed-θ_s spectra: all three peaks fall in absolute height as ω_cdm rises,
but by very different amounts — D1 by 48.4%, D2 by 45.2%, D3 by only 16.5%
(8472→4368, 3665→2009, 2769→2312 µK²). Peaks 1 and 2 track each other
closely; peak 3 is the outlier that resists. This killed the original
working hypothesis (early ISW draining peak 1 specifically) before any
CLASS time was spent on it — the pattern is "peak 3 protected," not "peak 1
drained." Figure: `figures/04_peak_heights_normalised.png`.

**Test A — lensed vs unlensed.** Re-ran the fixed-θ_s sweep with
`lensed=False`. D1/D2 and D3/D2 trends are essentially unchanged (spreads
0.141 vs 0.137, and 0.426 vs 0.395) — lensing ruled out as the cause.
Cached: `data/sweep_fixed_theta_s_unlensed.npz`.

**Tests D, D1, D2 — the k_eq radiation-driving-envelope hypothesis.**
Revised hypothesis after Test C: the driving envelope's characteristic
scale k_eq ∝ ω_m moves to higher ℓ as ω_cdm rises, so peaks below it lose
their driving boost first. ℓ_eq = k_eq·D_A(z*), computed independently of
CLASS (`src/cmbpeaks/keq.py`): D_A via a flat-ΛCDM comoving-distance
integral, z* from the Hu & Sugiyama 1996 fitting formula, checked against
the real baseline — predicts z*=1091.9 vs CLASS's actual 1088.78, 0.3% off.
ℓ_eq runs 86 → 200 across the grid, matching the ballpark estimate used to
set up the test.

- The naive ℓ_eq(ω) marker doesn't sit on each ratio curve's actual
  turnover; the geometric mean √(ℓ_eq(ω)·ℓ_eq(0.12)) is a much better
  predictor (111.7 vs 112.0 measured at the low end), but the residual grows
  smoothly from +0.3% to −20.0% across the grid.
- Ω_Λ = 1−(ω_m+ω_r)/h² was checked and **ruled out** as the cause of that
  residual growth: it crosses zero between ω_cdm=0.19 and 0.20 (the grid's
  top point is not a physical cosmology), but restricting to Ω_Λ>0.3 only
  improves the mean |relative residual| from 11.0% to 9.0% — the residual
  still grows smoothly from +0.3% to −16.4% *within* the healthy-Ω_Λ subset.
  **Kept as an open item**, not resolved. Ω_Λ going negative at ω_cdm=0.20 is
  also a standing caveat on the grid's range, independent of what it did or
  didn't explain here.

**Tests E, F — does one universal envelope B(x) explain all three peaks,
x = ℓ_peak/ℓ_eq?** Test E's naive collapse plot (each peak normalised to its
own value at ω_cdm=0.12) showed three separate curves, but that
normalisation was flawed: it forces three different reference abscissas
(x_ref = 1.52, 3.70, 5.61 for peaks 1/2/3), so three curves were guaranteed
even if B were exactly universal. Test F corrected this:

- **F1**, a shared quadratic shape plus one free offset per peak
  (ln D_peak = offset_peak + f(x)), fits much better than Test E's naive
  shared fit (RMS 0.054 vs 0.162) — confirming the normalisation, not just
  the hypothesis, was part of what Test E measured.
- **F2**, the decisive test: d(ln D_peak)/d(ln x) is offset-free, so if B is
  universal this log-log slope must be the same function of x for every
  peak. Peaks 2 and 3 overlap in x ∈ [4.0, 6.2]. Their slopes disagree by a
  factor of ~3 throughout that overlap (mean difference +0.39), against a
  finite-grid self-consistency noise floor of 0.09 — a 4.2× gap.
  **The envelope is not universal.**

Figures: `figures/06_scaling_collapse.png`, `figures/07_test_f_corrected_collapse.png`.

**Conclusion, stated as what it is.** Three candidate mechanisms were tested
and eliminated (early ISW at peak 1 specifically, lensing, a universal
k_eq-scaled driving envelope). The phenomenology itself is solid and
reproducible: all three peaks fall with ω_cdm, peak 3 resists far more than
peaks 1 and 2, and this is real unlensed physics, not an artifact of the
Ω_Λ→0 grid tail. What mechanism produces the peak-3 resistance specifically
remains open. Per the project's honesty rule, this is written up as a
well-characterised open question with eliminated candidates, not as an
unresolved failure — and no fourth mechanism was proposed after F2's clean
negative result.

---

## Stage 6 — The `omega_b` sweep (the baryometer companion) ✅ DONE 2026-07-27

**Refactor.** `run_sweep()` and `params_fixed_theta_s()` generalised to take
any CLASS parameter name plus a `fixed={...}` dict for pinning everything
else. Defaults are unchanged (`param="omega_cdm"`), so Stages 1/2/5 keep
working with no code changes on their side, and 04b/04c/06/07 still load and
process `data/sweep_fixed_theta_s.npz` exactly as before — verified by
re-running the full test suite and reloading all three cached omega_cdm npz
files after the rename. `SweepResult`'s `omega_cdm` field is now
`param_values` (+ a `param` string); `load()` falls back to reading the old
`omega_cdm` key when `param_values` isn't present, so the already-committed
Stage 2/5 npz files didn't need regenerating.

**Grid.** ω_b ∈ [0.017, 0.030], 16 points, bracketing Planck's 0.02237.
ω_cdm held at 0.1200 explicitly via `fixed=`. Mode: `fixed_theta_s` only —
the point of this sweep is the amplitude effect, not the geometry one, so
there's no reason to run the fixed-h version too.

| Check | Expectation (textbook, stated in advance) | Measured |
|---|---|---|
| D1/D2 trend | rises with ω_b | **rises**, 1.895 → 2.752 ✅ |
| D3/D2 trend | rises with ω_b | **rises**, 0.898 → 1.083 ✅ |
| ℓ spread (1st/2nd/3rd peak), fixed θ_s | small, same mechanism as the ω_cdm sweep | 1.06 / 10.67 / 2.73 — i.e. 0.48% / 1.99% / 0.34% of position |
| Peaks found | 3 everywhere | ✅ 16/16, no NaN |

Unlike Stage 2's two sign flips, this one lands exactly as predicted — baryon
loading's textbook mechanism (R = 3ρ_b/4ρ_γ ∝ ω_b enhances the compression
peaks 1 and 3 over the rarefaction peak 2, and depends on nothing but ω_b) is
solid enough that the prediction was safe to state in the checklist itself,
which the ω_cdm sweep's tangled radiation-driving/eISW story was not. A
correct prediction here is not more interesting than a wrong one was for
ω_cdm; it's just further confirmation that the two parameters work through
genuinely different physics.

z_eq also rises across the grid (3275 → 3585) since ω_m = ω_b + ω_cdm and
ω_cdm is held fixed — a side effect of the parameterisation, not a baryon
signature; the ratio trends are the ones that matter here.

Figure: `figures/08_sweep_ratio_omega_b_fixed_theta_s.png`. Cached spectra:
`data/sweep_omega_b_fixed_theta_s.npz`. 15/15 tests pass (added one round-trip
test for old-format npz files without a `param_values` key).

---

## Stage 3 — The rigor upgrade (highest-leverage stage)

Run the sweep twice and put the results side by side:

- **Fixed `h`, θ_s floats.** Lowering `omega_cdm` changes both peak amplitudes
  and peak positions, because the sound horizon and the distance to last
  scattering both move. Everything slides.
- **Fixed `100*theta_s`, `h` solved by CLASS's shooting method.** Peak
  positions lock, so the figure isolates the amplitude effect — which is the
  actual dark-matter physics.

**Deliverable:** `figures/03_fixed_h_vs_fixed_theta.png` and 2–3 paragraphs in
the README explaining what each panel isolates.

**Caveat to handle in code:** the θ_s shooting solver adds runtime per model
and can fail to converge at extreme parameter values. `sweep.py` catches this
per grid point and records a NaN rather than crashing the whole sweep.

---

## Stage 4 — Packaging

- `README.md` with the honest one-sentence framing (already drafted, don't
  inflate it).
- `requirements.txt` pinned; classy 3.3.4.0, Planck file R3.01 noted.
- One narrative notebook in `notebooks/` that reads the saved arrays and
  reproduces the figures — reviewers open notebooks, not scripts.
- Tests passing.

---

## Stage 7 — Diagonal χ² against Planck ✅ DONE 2026-07-27

**What this is not.** A diagonal-only goodness-of-fit check, not a likelihood.
Three reasons: (1) Planck's bandpowers are correlated bin to bin and this
ignores the covariance matrix entirely — the real analysis needs the `plik`
machinery; (2) the model is linearly interpolated onto each bin's effective
multipole rather than integrated against the bin's window function; (3) the
baseline parameters came from Planck's own fit to this data, so a good χ²
shows pipeline consistency, not an independent confirmation of ΛCDM.

**The control.** Planck's binned file carries a `BestFit` column — their own
ΛCDM model, binned the same way. Computing χ² against `Dl` for both that
column and our cached spectrum, identically, turns "the curve threads the
error bars" into a number with a floor to compare against.

**The floor is not 1, and that's the headline result.** χ²/N for Planck's own
best-fit model against Planck's own data is **0.785**, not 1 — even though
that model *is*, by construction, the best fit. Since nothing here could be
overfit or underfit, that shortfall is a direct empirical measurement of how
much the diagonal-error approximation misestimates the real (correlated)
errors, rather than something asserted from first principles. It's caveat (1)
demonstrated, not just stated.

| | χ² | χ²/N |
|---|---|---|
| ours vs Planck `Dl` | 84.23 | 1.015 |
| Planck `BestFit` vs `Dl` | 65.12 | 0.785 |

N = 83 bins, ℓ = 47.71–2499.02 — every Planck bin falls inside the cached
baseline's ℓ = 2–2500 range, so none were dropped. `-dDl` and `+dDl` are
identical in all 83 bins, so symmetrising into one σ costs nothing. No
parameters were fitted here, so dof = N, not N − k.

**Decomposing the 19.1 excess.** χ²/N = mean² + std² of the residual
distribution exactly (an algebraic identity, not an approximation) — verified
against the direct sum for both rows (84.227 both ways, 65.122 both ways).
Residuals: ours mean = −0.221, std = 0.983; Planck mean = +0.010, std = 0.886.
Splitting `chi2_ours − chi2_planck` = 19.11:

- **4.05** from the mean offset: `83 × (−0.221)² = 4.05`
- **15.05** from broader scatter: `83 × (0.983² − 0.886²) = 15.05`

Most of the gap over Planck's floor is scatter, not a systematic shift — but
the mean offset isn't nothing either: at SE = 0.983/√83 = 0.108, −0.221 is
about 2σ from zero. **Unverified hypothesis, not a claim:** rounding on `A_s`
and `τ` in the baseline params could produce a small overall amplitude
offset, since the spectrum amplitude scales as `A_s·e^(−2τ)` — the same
degeneracy the README's peak-ratio sweeps sidestep by construction (see "What
the peak ratios do"). Plausible, not investigated, and not asserted as the
cause.

**Residual histogram.** Both distributions track a unit Gaussian reasonably
well (`figures/09_chi2_residual_histogram.png`) — no fat tails, no bin
dominating the sum. The single worst point, ℓ≈465 at −2.87σ, is not chased
further: one point beyond 2.87σ in 83 independent-ish draws is unremarkable
(roughly 20% expected under a normal null), not a signal to debug.

Script: `scripts/09_chi2_planck.py`, no CLASS runs — reads
`data/baseline_Dl.npz` and the committed Planck file. 15/15 tests pass.

---

## Tool split for each stage

| Stage | Claude Code | Cowork |
|---|---|---|
| 0 | all of it — installs, builds, debugging tracebacks | — |
| 1 | run scripts, fix unit bugs, tune peak-finder args | interpret the overlay, decide lensed vs unlensed |
| 2 | run sweep, git commits | read the trend, sanity-check the physics |
| 3 | implement fixed-θ_s branch, catch convergence failures | write the explanatory paragraphs, compare panels |
| 4 | notebook execution, final commits | README wording, LinkedIn framing |
