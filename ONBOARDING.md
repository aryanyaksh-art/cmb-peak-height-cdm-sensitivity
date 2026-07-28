# Onboarding

For anyone joining the project. Written for someone who has seen some physics
but does not write Python every day.

Read this once, then keep `README.md` and `PLAN.md` open as references.
`README.md` is the front door and holds the physics argument. `PLAN.md` is the
build log and holds every measured number.

---

## 1. What the project is

We use the CLASS Boltzmann code to compute the CMB temperature power spectrum,
locate its first three acoustic peaks, and measure how the peak-height ratios
respond when we vary the cold dark matter density and the baryon density one at
a time.

Two sweeps, same observable, different mechanism:

- `omega_cdm` acts through **radiation driving**. More dark matter moves
  matter-radiation equality earlier, so gravitational potentials stop decaying
  sooner and less driving survives.
- `omega_b` acts through **baryon loading**. Baryons add inertia to the
  photon-baryon fluid without adding pressure, which pushes the oscillation's
  zero point deeper into the well and favours the compression peaks.

Getting both from one pipeline is the point of the project.

### What it is not

This reproduces results established in the 1990s and 2000s. It is not novel
research, it does not measure any cosmological parameter, and the Planck
comparison is a diagonal goodness-of-fit check rather than a likelihood
analysis.

That framing is not modesty. It is the thing that makes the project credible to
a working cosmologist, and it appears in three places in the README on purpose.
Never write a comment, commit message, README line or LinkedIn caption that
walks it back. No "discovered", no "proved dark matter", no "new constraint".

---

## 2. Ground rules

Four of these were learned by getting them wrong first.

**You have to be able to defend every choice yourself.** If you cannot explain
in your own words why a parameter is held fixed or why a diagnostic was built
that way, it does not go in. This matters because the project exists to be
discussed with professors, and the first follow-up question will be about a
choice, not a result.

**Do not put predicted signs in a checklist.** During Stage 2 we predicted the
direction of three trends. Two of those predictions were wrong, and because
they sat in a checklist as expectations, correct results looked like bugs and
we went hunting for a problem that did not exist. Phrase expectations as
"record the sign, do not debug it" unless the reasoning is airtight.

**Check that a diagnostic can distinguish the hypotheses before you spend
compute on it.** Two Stage 5 tests were badly designed. One compared absolute
multipole spread for a quantity that rescales, so the comparison meant nothing.
One normalised in a way that baked a per-peak offset into the result, which
made a valid hypothesis untestable. Both made good results look like failures.
Write down what each possible outcome would imply before you run it. If two
different physical answers give the same output, the test is broken.

**The Stage 5 anomaly is an open question, not a bug.** All three peaks fall as
`omega_cdm` rises, but at very different rates: 48.4%, 45.2% and 16.5%. Peak 3
resists. Four candidate mechanisms have been eliminated (early ISW on peak 1,
lensing, the Omega_Lambda going negative at the top of the grid, and a
universal k_eq-scaled driving envelope). Do not propose a fifth without a
strong reason, and do not "fix" it.

---

## 3. Getting it running

CLASS compiles from C source and supports Linux and macOS only. On Windows that
means WSL.

Full instructions with every failure mode we hit: **`docs/SETUP_WSL.md`**. Read
it rather than improvising, especially the `/etc/wsl.conf` metadata fix, which
is non-obvious and blocks `pip install -e .` completely.

Short version:

```bash
sudo apt update && sudo apt install -y build-essential python3-dev python3-venv gfortran
python3 -m venv ~/venvs/cmb
source ~/venvs/cmb/bin/activate
pip install -r requirements.txt
pip install -e .
python scripts/00_sanity_check.py
```

Two things the setup doc assumes that you will need to change for your own
machine:

- Paths under `/mnt/c/Users/aryan/...` are Aryan's. Use your own clone location.
- Keep the venv in your Linux home (`~/venvs/cmb`), not inside the project
  folder. The project folder is on OneDrive, which will try to sync thousands
  of compiled artifacts, and `/mnt/c` I/O under WSL is slow enough to make the
  CLASS build noticeably worse.

A single lensed spectrum to l=2500 takes 10 to 30 seconds. A 16-point sweep
takes several minutes. Sweep results are cached to `data/*.npz`, and those
files are committed, so you can do most analysis and all of the notebook
without running CLASS at all.

### Verify you are set up correctly

```bash
pytest
python scripts/01_baseline.py
```

The baseline should print the first peak at l = 220.3 with D_l = 5730 uK^2,
against Planck's measured 220.6 and 5733. If your numbers differ by more than a
few tenths in l, stop and say so before doing anything else.

---

## 4. The physics you actually need

Enough to work on the code. The README has the fuller version.

**The observable.** `D_l = l(l+1)/(2*pi) * C_l`, in microkelvin squared. Plotted
against multipole `l`, it shows a series of acoustic peaks. Peak 1 sits near
l = 220, peak 2 near 538, peak 3 near 810.

**Where the peaks come from.** Before recombination, photons and baryons are
tightly coupled and oscillate as one fluid inside dark matter potential wells.
Gravity compresses, radiation pressure pushes back. At recombination the photons
free-stream, freezing the oscillation phase of each mode into the sky. Modes
caught at maximum compression or maximum rarefaction give peaks.

**Why peak heights carry information.** Baryon loading makes compressions
(odd peaks) more extreme than rarefactions (even peaks), so it controls the
odd/even asymmetry and scales with `omega_b`. Radiation driving sets the overall
amplitude, and dark matter controls it by setting when matter-radiation equality
happens.

**Why peak 3 is the interesting one.** Baryon loading alone would leave peak 3
well below peak 2. Dark matter's suppression of radiation driving lifts it back
up. Planck measures them at 2586 +/- 23 and 2518 +/- 17 uK^2, which is
essentially equal. That near-parity is the direct evidence that dark matter
dominated the matter budget before recombination.

**Why we use ratios instead of absolute heights.** The overall spectrum
amplitude scales as `A_s * exp(-2*tau)`. Both are held fixed here, but a ratio
is insensitive to that degeneracy regardless.

**The one methodological idea to internalise.** "Vary the dark matter density"
is ambiguous until you say what else is held fixed. We run each sweep two ways:

- `fixed_h` holds the Hubble parameter. The sound horizon and the distance to
  last scattering both change, at different rates, so peak *positions* slide by
  13 to 20 percent along with the heights. Nothing separates amplitude from
  geometry.
- `fixed_theta_s` holds the angular acoustic scale at Planck's 1.04092 and lets
  CLASS solve for h. Positions lock to about 2 percent, so what is left is the
  amplitude change, which is the physics the parameter actually controls.

Every quoted result uses `fixed_theta_s`. The `fixed_h` version exists to show
what the control buys you.

---

## 5. The code

Installed as a package (`pip install -e .`), so `import cmbpeaks` works from
anywhere in the venv.

### `src/cmbpeaks/`

| Module | What it does |
|---|---|
| `config.py` | Every parameter, path and benchmark. Start here. Nothing else hardcodes a cosmology. |
| `spectra.py` | `run_class(params)` returns `(ell, D_l, derived)`. Handles the C_l to D_l conversion. |
| `peaks.py` | `find_acoustic_peaks(ell, dl)` returns three `Peak` objects with sub-integer positions. `peak_ratios(peaks)` gives D1/D2 and D3/D2. |
| `sweep.py` | `run_sweep(...)` loops a parameter over a grid and records peaks, z_eq and h. `SweepResult` saves and loads `.npz`. |
| `planck.py` | Loads the Planck 2018 binned TT band powers. |
| `keq.py` | Closed-form `l_eq = k_eq * D_A`, no CLASS. Used by the Stage 5 tests. |
| `plotting.py` | All figure generation. Generic across sweep parameters. |

Three design decisions worth knowing:

- **`config.py` is the single source of truth.** If you find yourself typing a
  number into a script, it probably belongs in config first.
- **`run_sweep` records failures as NaN rather than raising.** The theta_s
  shooting solver occasionally fails to converge at extreme parameter values,
  and losing one point should not discard a sweep that took five minutes.
- **`Omega_Lambda` is deliberately never set.** CLASS enforces flatness through
  its closure equation and fills in the unspecified dark energy component.
  Setting it by hand would break flatness partway through a sweep.

### `scripts/`

Numbered, run in order. `00` through `03` are the main pipeline. `04` through
`07` are the Stage 5 investigation. `08` is the omega_b sweep, `09` is the
chi-squared comparison. Each writes to `data/` and `figures/`.

### `tests/`

Run without CLASS installed. `test_units.py` exists specifically to catch the
unit trap below.

### `notebooks/cmb_peaks.ipynb`

Committed with outputs so figures render on GitHub. Reads cached `.npz` files
and needs no CLASS.

---

## 6. Traps that have already cost us time

**The unit conversion.** `classy`'s `lensed_cl()` returns dimensionless C_l with
no `l(l+1)/2pi` factor. CLASS's command-line `.dat` output *does* include it, so
the Python wrapper and the files disagree. You need both multiplications:

```
D_l [uK^2] = l(l+1)/(2*pi) * C_l * (T_cmb * 1e6)^2
```

A spectrum off by a factor of roughly 1e12 means the `T_cmb^2` term is missing.

**Lowercase vs capital omega.** `omega_b` is the physical density
`Omega_b * h^2`. `Omega_b` is the fractional density. CLASS accepts both and
they are not interchangeable. Same for cdm.

**`'ln10^{10}A_s'`** is a literal dictionary key, braces included.

**The Hubble sector is over-determined if you pass two of h, H0 and
`100*theta_s`.** CLASS errors out. `params_fixed_theta_s()` pops `h` for you.

**ABI mismatch after a NumPy upgrade.** classy compiles against whatever NumPy
was present at install time. After a NumPy major version bump, delete the venv
and rebuild rather than upgrading in place.

---

## 7. How we work together

**Do not both edit the same file at the same time.** The project folder syncs
through OneDrive and two people writing the same file will produce a conflict
copy rather than a merge.

**Tool split.** Claude Code for terminal work, running code, surgical edits and
git. Cowork for planning, physics discussion, multi-file reasoning and writing.

**Git.** Branch per piece of work, then open a pull request. Two reasons beyond
avoiding conflicts. It keeps the history readable, and it makes the authorship
of each contribution unambiguous, which matters because we send this repo to
people who will look at it.

```bash
git checkout -b stage10-polarisation
# work
git add -A && git commit -m "Stage 10: TE spectrum, first pass"
git push -u origin stage10-polarisation
```

**Commit messages** state what changed and what it showed. No overclaiming, and
no "fixed stuff".

**Attribution.** Stages 1 through 7 were Aryan's work and the README's first
person reflects that. Anything from Stage 8 onward gets credited to whoever did
it, in `PLAN.md` and in the commit history. If we end up presenting this
jointly, the README opening changes to match. Getting this right is not
bookkeeping, it is the same honesty rule applied to people instead of physics.

---

## 8. Where to start

In order.

1. **Get the environment working** and confirm the baseline benchmarks. Nothing
   else is worth doing until `scripts/01_baseline.py` prints 220.3 and 5730.
2. **Read `README.md` end to end**, then open
   `figures/03_fixed_h_vs_fixed_theta.png` and make sure you can say out loud
   what the two panels differ by and why that matters.
3. **Open the notebook** and regenerate the figures from cached data. Confirms
   your install without a long CLASS run.
4. **Pick something small and real.** Good candidates:
   - Extend `tests/` to cover `sweep.py`'s save and load round trip, which is
     currently untested.
   - Reproduce one Stage 5 test from `PLAN.md` and check you get the same
     numbers.
5. **Then take an open item.** The three on the table, roughly in order of
   value: extend the pipeline to polarisation spectra (TE and EE), bin theory
   against Planck's actual window functions instead of interpolating to bin
   centres, or chase the peak-3 anomaly if a genuinely new idea appears.

Ask about anything in section 4 that does not land. The physics here is
compressed, and nobody absorbs radiation driving on first contact.
