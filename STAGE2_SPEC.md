# Stage 2 handoff spec (for Claude Code)

Working doc, not repo content. Delete before Stage 4 packaging.

Stage 2 code already exists from the night-one scaffold. This spec covers the
edits to make *before* running, then the run and the checks.

---

## 0. `git init` first — before touching any code

There's no commit history in this folder yet. Initialise and commit the scaffold
**as it stands right now**, before the Stage 2 edits.

```
git init
git add -A
git commit -m "Stage 1: baseline LCDM spectrum with Planck 2018 overlay"
```

Then the Stage 2 edits land as their own reviewable diff. A professor skimming
`git log` should see someone working incrementally, not one monolithic initial
commit containing a finished project.

---

## 1. Persist spectra so Stage 3 doesn't recompute

Right now `scripts/02_sweep.py` calls `run_sweep()` without `keep_spectra=True`,
and `SweepResult.save()` drops the spectra on the floor. `scripts/03_paired_figures.py`
then re-runs both sweeps from scratch. That's three full sweeps where two would do,
and it means the Stage 2 fixed-θ_s curve and the Stage 3 fixed-θ_s panel are
separately computed — if they ever disagreed you'd never see it.

**`src/cmbpeaks/sweep.py`**

- In `SweepResult.save()`, also write `ell` (1-D, shared across grid points) and
  `dl_grid` (shape `(n_grid, n_ell)`, NaN rows for failed points). Guard for the
  case where `spectra` is empty so the fixed-h/fixed-θ_s npz stays writable either way.
- Add `SweepResult.load(path)` as a `@classmethod` that reconstructs the dataclass,
  including repopulating `spectra` as the `(ell, dl)` list when `dl_grid` is present.
- `load()` must restore `None` for grid points whose `dl_grid` row is all-NaN, so the
  in-memory representation after a load is identical to the one after a fresh sweep.
  Downstream code (`plot_paired_sweeps`) filters on `is not None` and depends on it.
  Without this, a NaN row reconstructs as `(ell, all-NaN array)`, the filter silently
  stops working, and matplotlib gets handed NaN spectra.
- `mode` is a Python `str`; it comes back from `np.load` as a 0-d array. Cast it
  with `str(arr["mode"])` on load or the `f"...{result.mode}"` filename formatting
  in the scripts produces something ugly.

Size check: 16 × 2499 float64 ≈ 320 kB before compression, per mode. Fine to commit,
but check `.gitignore` — if `data/*.npz` is currently ignored, decide deliberately
whether to keep ignoring it. My take: ignore the npz, keep the figures, and let the
notebook regenerate. Reviewers clone small repos.

**`scripts/02_sweep.py`**

- Default `--mode both`, running `fixed_h` then `fixed_theta_s` and writing
  `data/sweep_fixed_h.npz` and `data/sweep_fixed_theta_s.npz`. Keep the single-mode
  choices for iteration.
- Pass `keep_spectra=True`.

**`scripts/03_paired_figures.py`**

- Load both npz files if present; only run the sweeps if a file is missing.
- Add `--force` to recompute regardless.

---

## 2. Third panel on the Stage 2 figure

`plot_sweep()` in `plotting.py` goes from 2 panels to 3, sharing the x-axis:

1. `D1/D2` and `D3/D2` vs `omega_cdm` (unchanged)
2. `z_eq` vs `omega_cdm` (unchanged)
3. **new:** first-peak position ℓ₁ vs `omega_cdm`

Panel 3 is the validation panel. In `fixed_theta_s` mode it should be a flat line
at ℓ₁ ≈ 220 — that's direct evidence CLASS's shooting solver actually locked the
acoustic scale, which is the assumption Stage 3's whole argument rests on. In
`fixed_h` mode the same panel slopes, which is the contrast.

Draw a horizontal reference line at the Planck ℓ₁ = 220.6.

**Y-limits must be mode-dependent.** Pin them to 220.6 ± 40 in `fixed_theta_s` mode,
so a flat line reads as flat instead of being autoscaled into what looks like noise.
Leave `fixed_h` autoscaled. Hardcoding ±40 in both modes would compress the fixed-h
slope until it also looks flat, which destroys the exact contrast the panel exists
to show.

---

## 3. Two failure modes to expect

**The `[180, 280]` first-peak guard may fire in `fixed_h` mode at the low end.**
At `omega_cdm = 0.05` with `h` pinned at 0.6736, the sound horizon grows faster than
the distance to last scattering, so θ_s grows and ℓ₁ drops. It may land near or below
180 and raise `ValueError` from `find_acoustic_peaks`, NaN-ing out the low-ω grid points.

If that happens, **widen the guard, don't delete it.** Make the bounds a parameter and
pass a looser range for the `fixed_h` branch only. Then record the actual ℓ₁ range in
`PLAN.md` — "ℓ₁ ran from X to 220.6 across the grid at fixed h" is a good sentence to
have in the README, because it quantifies exactly why fixed-θ_s is the better control.

**`z_eq` may not come back from `classy` 3.3.4.0 under that name.** `_safe_derived()`
swallows unknown derived-parameter names silently, so a rename would leave the middle
panel blank with no error. Before the full run, print the derived dict at the first
grid point and confirm `z_eq` is in it. If it isn't, fall back to
`z_eq = omega_m / omega_r - 1` computed from the input parameters and label the panel
as analytic.

---

## 4. Run order

```
git init && git add -A && git commit -m "Stage 1: baseline LCDM spectrum with Planck 2018 overlay"
# ... make the section 1-3 and section 6 edits, then:
pytest
# smoke test both modes, coarse
python scripts/02_sweep.py --mode both --n 4
# full run
python scripts/02_sweep.py --mode both
```

Full run is 32 Boltzmann computations plus 16 shooting solves. Budget 15–25 min.

---

## 5. Numbers to check before committing

These are what you should be able to defend in an email to a professor. Check the
signs yourself before accepting the output.

| Check | Expected | Why |
|---|---|---|
| `z_eq` at ω_cdm = 0.1200 | ≈ 3400 | Planck 2018 quotes z_eq = 3402 ± 26 |
| `z_eq` range across grid | ≈ 1750 → 5400 | z_eq ≈ ω_m/ω_r − 1, near-linear in ω_cdm |
| `D1/D2` trend | **rises** with ω_cdm | see below |
| `D3/D2` trend | **sign not predicted — record it, don't debug it** | two effects compete; see below |
| ℓ₁ spread, fixed θ_s | < ~2 across the whole grid | the shooting solver worked |
| ℓ₁ spread, fixed h | tens of ℓ | the geometric contamination Stage 3 removes |
| `h` in fixed-θ_s mode | monotonically **rising**, ≈ 0.55 → 0.78 | holding θ_s while adding matter needs a larger H₀ |
| Peaks found | 3 at every grid point | no NaN rows |

**Why D1/D2 rises.** More CDM pushes matter–radiation equality earlier. Modes that
cross the horizon while radiation still dominates get an amplitude boost — the
gravitational potential decays under them and drives the oscillation resonantly,
rather than just providing a static well. Peak 2's mode entered deeper in the
radiation era than peak 1's, so it collects more of this driving. Raising ω_cdm
shortens the radiation era and removes more boost from peak 2 than from peak 1,
lifting D1/D2. Baryon loading pushes the same way — peak 1 is odd, peak 2 is even,
and suppressing the driving that partly masks the odd/even modulation raises odd
peaks relative to even. Both effects agree, so the sign is safe.

**Why D3/D2's sign is left open.** Peaks 2 and 3 are close together in ℓ, so the
two effects that reinforced each other for D1/D2 now pull against each other:

- *Radiation driving* — peak 3 entered deeper in the radiation era than peak 2, so
  it collects more driving boost and loses more of it as ω_cdm rises. Pushes
  D3/D2 **down**.
- *Baryon loading becoming visible* — driving partly masks the odd/even modulation.
  Suppress the driving and the loading signature stands out more, lifting odd peaks
  (1 and 3) against even (2). Pushes D3/D2 **up**.

Which one wins is quantitative, and it isn't settled in prose. Wayne Hu's framing
points the opposite way from a naive driving-only argument: he treats a third peak
comparable in height to the second as the indicator that dark matter dominated the
pre-recombination matter budget, which reads as D3/D2 *rising* with ω_cdm.

**So: whichever direction the sweep gives, record it — do not treat it as a bug and
go hunting for one.** The measured answer is a better README paragraph than either
prediction would have been, because it says which effect dominates over this range
instead of asserting it.

D3/D2 is still the sharper dark-matter fingerprint of the two ratios, for the reason
Hu gives: baryon loading alone would leave peak 3 well below peak 2, and peak 3's
near-parity with peak 2 is what a CDM-dominated matter budget produces.

**Why ratios rather than absolute heights.** The overall spectrum amplitude scales as
A_s·e^(−2τ), and both are held fixed here anyway — but stating that the ratio is
insensitive to that degeneracy is worth a line in the README, because it's the reason
a ratio is the right observable to sweep.

---

## 6. Add `tests/test_sweep_io.py`

The `mode` 0-d array issue in section 1 is one save/load asymmetry found by reading.
That's the class of bug that stays invisible until Stage 3 loads a file and quietly
plots garbage. Write the test alongside the `save`/`load` changes, not after.

No CLASS needed — build a synthetic `SweepResult` with `numpy` and a `tmp_path`
fixture, round-trip it through `save()` and `load()`, and assert:

- every array field equals its original, `np.testing.assert_allclose` with
  `equal_nan=True` so NaN rows for failed grid points compare equal
- `mode` comes back as a `str`, not `np.ndarray` — assert `isinstance(loaded.mode, str)`
  and that `f"sweep_{loaded.mode}.npz"` formats to the expected filename, since that
  string goes straight into a path
- `spectra` is repopulated from `dl_grid` as a list of `(ell, dl)` tuples with the
  right shapes
- failed grid points come back as `None`, not as NaN-filled tuples — this is the
  section 1 requirement, and it's what `plot_paired_sweeps`'s `is not None` filter
  depends on
- a result saved with `spectra=[]` round-trips without raising, and comes back with
  empty spectra rather than a malformed array

Include at least one NaN row and one failed-point `None` in `spectra` in the synthetic
fixture — the all-clean case is the one that would have passed anyway.

Total suite should go from 9 tests to roughly 13–14. Run `pytest` before committing.
