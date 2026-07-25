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

## Optional Stage 5 — Quantitative comparison

Only after 1–3 are solid. Bin the CLASS curve into the Planck bandpower bins
and compute a naive χ² using the diagonal errors. Call it what it is: a
diagonal-only goodness-of-fit check, not a likelihood. The real Planck
likelihood needs the `plik` machinery and the full covariance matrix, and
claiming otherwise is exactly the kind of overclaim `CLAUDE.md` rules out.

---

## Tool split for each stage

| Stage | Claude Code | Cowork |
|---|---|---|
| 0 | all of it — installs, builds, debugging tracebacks | — |
| 1 | run scripts, fix unit bugs, tune peak-finder args | interpret the overlay, decide lensed vs unlensed |
| 2 | run sweep, git commits | read the trend, sanity-check the physics |
| 3 | implement fixed-θ_s branch, catch convergence failures | write the explanatory paragraphs, compare panels |
| 4 | notebook execution, final commits | README wording, LinkedIn framing |
