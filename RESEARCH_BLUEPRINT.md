# Building a Portfolio-Grade CMB Peak-Height Asymmetry Project with CLASS/classy

## TL;DR
- **This is a fully feasible, honest portfolio project**: install `classy` (currently v3.3.4.0, released Nov 24 2025) via `pip install classy`, compute the ΛCDM TT spectrum, sweep `omega_cdm`, measure the first-to-second peak ratio, and overlay Planck 2018 binned TT data — it reproduces a well-established textbook result (dark matter's imprint on the acoustic peaks), not novel research.
- **The core physics you must be able to explain**: cold dark matter provides pressureless gravitational potential wells; more CDM pushes matter-radiation equality earlier, which suppresses "radiation driving" and lowers overall peak amplitudes, while baryon loading (not CDM directly) is what makes odd/compression peaks taller than even/rarefaction peaks — the near-equal height of the third and second peaks (Planck 2018 measures Peak 2 = 2586 ± 23 µK² at ℓ=538 and Peak 3 = 2518 ± 17 µK² at ℓ=810) is the clean fingerprint of dark matter.
- **The subtle part that will impress a professor**: what you hold fixed when varying `omega_cdm` (spatial flatness via automatic Omega_Lambda, the angular sound-horizon scale `100*theta_s`, baryon density) completely changes what the plot isolates; being explicit about this is the difference between a naive and a rigorous project.

## Key Findings

1. **Installation**: `pip install classy` is the recommended path; the current stable release is 3.3.4.0 (Nov 24 2025, confirmed on PyPI — source-only, no wheels). A C compiler is required. Use an isolated virtual environment. The main historical pitfall — a Cython 3 build failure — is fixed in CLASS v3.2.4+ (Sep 30 2024); only older versions need `pip install "Cython<3"`.
2. **Baseline API**: set `output='tCl,pCl,lCl'`, `lensing='yes'`, `l_max_scalars=2500`, call `.compute()`, extract with `.lensed_cl(2500)` (or `.raw_cl` for unlensed). CLASS returns dimensionless C_ell; you must apply `ell(ell+1)/(2π)` and multiply by `(T_cmb×10^6)^2` to get D_ell in µK².
3. **Physics**: two distinct effects — baryon loading (odd/even asymmetry) and radiation driving / potential decay (overall amplitude, set by the matter-to-radiation ratio, hence `omega_cdm`).
4. **What to hold fixed**: CLASS auto-fills Omega_Lambda to enforce flatness; you can fix the acoustic scale with `100*theta_s` instead of `h`. Different choices isolate different physics.
5. **Planck data**: the file `COM_PowerSpect_CMB-TT-binned_R3.01.txt` from the Planck Legacy Archive (mirrored at IRSA/IPAC) contains columns `# l  Dl  -dDl  +dDl  BestFit`, with D_ell already in µK².
6. **Parameter sweep**: use `scipy.signal.find_peaks` on the D_ell array with a `distance` constraint; locate first two peaks, take the ratio, plot vs `omega_cdm`.
7. **Honesty**: accurate one-liner — "I reproduced the known dependence of the CMB acoustic peak heights on the cold dark matter density using a Boltzmann code and validated it against Planck 2018 data."
8. **References**: Wayne Hu's tutorials, Hu & Dodelson 2002, Dodelson's *Modern Cosmology*, Lesgourgues CLASS notes, Planck 2018 VI.

## Details

### 1. Installing CLASS and classy (2025-2026)

**Recommended path.** For this project you only need the Python wrapper, so `pip install classy` is the simplest route. The current stable PyPI release is **classy 3.3.4.0**, and its PyPI page states verbatim "classy 3.3.4.0 ... Released: Nov 24, 2025"; the maintainers listed are lesgourg (Julien Lesgourgues), ThomasTram, nilsor (Nils Schöneberg), and itrharrison. Recent releases: 3.3.3.0 (Sep 24 2025), 3.3.2.0 (Aug 27 2025), 3.3.1.0 (Jul 11 2025), 3.3.0.0 (Feb 18 2025).

**Critical caveat — source-only distribution.** The PyPI `classy` package ships only a source distribution (`classy-3.3.4.0.tar.gz`, ~6.0 MB), with **no pre-built binary wheels**. This means pip must compile the C library CLASS plus the Cython wrapper on your machine at install time. You therefore need:
- A working **C compiler** — `gcc` on Linux (install `build-essential` and `python3-dev`), Xcode command-line tools / clang or gcc on macOS.
- NumPy and Cython available in the build environment (modern pip handles this via build isolation).

**Build from source (alternative).** If you want to modify CLASS or inspect the C code: `git clone https://github.com/lesgourg/class_public.git`, then `make -j` (builds both the `class` executable and the `classy` wrapper), or `cd python && python setup.py build_ext --inplace`. You may need to edit the `Makefile` to set your compiler.

**Known pitfalls, flagged explicitly:**
- **Cython 3 build failure (mostly historical).** Older CLASS versions fail to compile `classy.pyx` under Cython ≥ 3.0 with an error like `'int_t' is not a type identifier`. This was **fixed in CLASS v3.2.4 (Sep 30 2024)**; any current `pip install classy` (3.3.x) builds fine with Cython 3. Only if you deliberately install an old/modified CLASS do you need `pip install "Cython<3"` first. (Note: the Cobaya docs mention a v3.2.1 cutoff for *modified* CLASS forks; the verified maintainer statement in CLASS issue #599 points to v3.2.4 for the public code.)
- **macOS + Anaconda archiver path.** On macOS with Anaconda the path to the `ar` archiver can be wrong, producing a build error; the CLASSpp/AarhusCosmology docs document the fix.
- **macOS clang + OpenMP.** Apple's default clang lacks OpenMP; if a build complains about `-fopenmp`, either install `gcc`/`libomp` via Homebrew or disable the OpenMP flag.
- **Python version.** Use a mainstream Python 3.x (3.10–3.12 are safe). Very new Python releases occasionally precede compatible wheels of dependencies.
- **Always use a virtual environment** (`python -m venv venv && source venv/bin/activate`, or a conda env). This isolates the NumPy/Cython versions CLASS builds against and avoids clobbering system packages. Rebuild `classy` if you later change NumPy major versions.
- CLASS is supported on **Linux and macOS**; Windows is not officially supported (use WSL).

**Sanity check after install:**
```python
from classy import Class
c = Class(); c.set({'output':'mPk'}); c.compute()
print(c.pk(0.1, 0))  # positive number => working
```

### 2. Running a baseline ΛCDM spectrum

**Minimal working example** (the exact idiom from the official Lesgourgues/Tram tutorials):
```python
from classy import Class
import numpy as np

params = {
    'output': 'tCl,pCl,lCl',
    'lensing': 'yes',
    'l_max_scalars': 2500,
    # Planck 2018 base-LCDM (TT,TE,EE+lowE+lensing) best fit:
    'omega_b': 0.02237,
    'omega_cdm': 0.1200,
    'h': 0.6736,
    'ln10^{10}A_s': 3.044,
    'n_s': 0.9649,
    'tau_reio': 0.0544,
    'T_cmb': 2.7255,
    # neutrinos (Planck baseline): one massive species 0.06 eV
    'N_ur': 2.0328,
    'N_ncdm': 1,
    'm_ncdm': 0.06,
}
cosmo = Class()
cosmo.set(params)
cosmo.compute()

lensed = cosmo.lensed_cl(2500)      # dict: 'ell','tt','ee','te','bb','pp',...
raw    = cosmo.raw_cl(2500)         # unlensed
ell    = lensed['ell'][2:]          # skip ell=0,1
Cl_tt  = lensed['tt'][2:]

# Convert dimensionless C_ell -> D_ell in microK^2:
T0_uK  = cosmo.T_cmb() * 1e6        # 2.7255 K -> microK
Dl     = ell*(ell+1)/(2*np.pi) * Cl_tt * T0_uK**2

cosmo.struct_cleanup()              # free memory before re-running
cosmo.empty()                       # clear input for next model
```

**Units and conventions — the single most common student mistake.** By default `classy`'s `.lensed_cl()` / `.raw_cl()` return **dimensionless C_ell** (the C_ell of ΔT/T, with no prefactor), NOT D_ell and NOT µK². To reproduce the familiar "hump" plot with a first peak that Planck 2018 (Planck Collaboration I, arXiv:1807.06205, Table 5) measures at ℓ = 220.6 ± 0.6 with amplitude 5733 ± 39 µK², you must:
1. Multiply by `ell(ell+1)/(2π)` to get D_ell.
2. Multiply by `T_cmb²` expressed in µK² (i.e. `(2.7255×10^6)²`), because CLASS's C_ell are in units of (ΔT/T)².

Note the contrast with CLASS's **command-line/file output**, which already includes the `ℓ(ℓ+1)/(2π)` factor — so the Python wrapper behaves differently from the `.dat` files. This trips up nearly everyone once.

**Parameter names classy expects** (exact strings):
- `omega_b` = Ω_b h² (physical baryon density) — lowercase omega. `Omega_b` (capital) is the fractional density Ω_b; don't mix them.
- `omega_cdm` = Ω_c h² (physical CDM density).
- `h` (dimensionless) or `H0` (km/s/Mpc) — supply exactly one.
- `A_s` OR `ln10^{10}A_s` (the literal key string is `'ln10^{10}A_s'`) — supply one. Planck: `ln10^{10}A_s = 3.044`, equivalently `A_s ≈ 2.100e-9`.
- `n_s`, `tau_reio`, `T_cmb`.

**Planck 2018 base-ΛCDM best-fit values (TT,TE,EE+lowE+lensing).** From Planck 2018 VI (arXiv:1807.06209, Table 1/2): Ω_b h² = 0.02237, Ω_c h² = 0.1200, H0 = 67.36 km/s/Mpc (h = 0.6736), ln(10^10 A_s) = 3.044, n_s = 0.9649, τ = 0.0544. Neutrinos: the Planck baseline assumes one massive eigenstate of 0.06 eV, represented in CLASS as `N_ncdm=1, m_ncdm=0.06, N_ur=2.0328` (so that N_eff = 3.044). CLASS's built-in baseline files use very close values (omega_b=0.02238280, omega_cdm=0.1201075, h=0.67810, A_s=2.100549e-9, n_s=0.9660499); these differ from the headline paper values only at the 4th–5th significant figure and are immaterial here.

### 3. The peak-height asymmetry physics (the heart of the project)

There are **two physically distinct effects** that students routinely conflate. Getting them straight is what a professor will probe.

**(a) Baryon loading → odd/even (compression/rarefaction) asymmetry.** Before recombination, photons and baryons are a single tightly-coupled fluid oscillating in the gravitational potential wells sourced (mainly) by dark matter. Baryons are non-relativistic: they add inertia and gravitational mass ("load") to the fluid but contribute no pressure. This displaces the zero-point of the oscillation deeper into the well — the standard analogy is a mass hung on a spring, which lowers the equilibrium point so downward stretches (compressions) become more extreme than upward ones (rarefactions). Consequently **odd-numbered peaks (1st, 3rd, 5th… = compressions into the wells) are enhanced relative to even-numbered peaks (2nd, 4th… = rarefactions)**. The size of this modulation is controlled by the baryon-to-photon momentum ratio R ∝ Ω_b h², so the odd/even ratio is primarily a **baryometer**. Raising `omega_b` deepens the loading and boosts odd peaks further.

**(b) Radiation driving / potential decay → overall peak amplitude, controlled by CDM.** For modes that entered the horizon during radiation domination (the higher peaks, and to some extent the first), the gravitational potentials Φ, Ψ are not constant: because radiation pressure resists collapse, the potentials **decay** as those modes oscillate. This decay is timed such that it "drives" the oscillation — it tends to leave the fluid maximally compressed just as the potential vanishes, and the near-simultaneous disappearance of the gravitational redshift roughly doubles the effect. The net result is that acoustic amplitudes are **boosted** for modes that oscillated while radiation still mattered. Cold dark matter, being pressureless, provides stable (non-decaying) potential wells once it dominates. **More `omega_cdm` → matter-radiation equality (z_eq) occurs earlier → the potentials have stopped decaying by the time more of the modes oscillate → less radiation driving → lower overall peak amplitudes.** Conversely, in a universe with little or no CDM, radiation driving is huge and the peaks would be enormously boosted and nearly equal in an odd/even sense — flatly inconsistent with data. (Planck Collaboration I describes the peaks as being "driven by dark matter potential perturbations," with the fundamental mode at ℓ ≃ 220.)

**Why the third peak is the clean dark-matter fingerprint.** Baryon loading alone (no CDM potential decay) would make successive peaks decrease monotonically in a baryon-dominated universe; you'd expect the third peak to be well below the second. Dark matter's elimination of radiation driving raises the third peak back up. Observing a **third peak comparable to or exceeding the second** is direct evidence that dark matter dominated the matter budget before recombination. Planck 2018 (arXiv:1807.06205, Table 5) measures Peak 2 = 2586 ± 23 µK² at ℓ = 538.1 and Peak 3 = 2518 ± 17 µK² at ℓ = 809.8 — i.e. the third peak is essentially as high as the second, exactly the dark-matter signature. Wayne Hu's phrasing: raising Ω_m h² reduces the driving effect so peak amplitudes decrease, while "having a third peak that is boosted to a height comparable to or exceeding the second peak is an indication that dark matter dominated the matter density in the plasma before recombination."

**How each density moves the ratios:**
- **Increase `omega_cdm`**: earlier z_eq → less radiation driving → all peaks lower in amplitude; the even/odd modulation from baryons becomes relatively *more* prominent (radiation driving had been partly masking it); first-peak position shifts slightly (changes to distance and z_eq).
- **Increase `omega_b`**: stronger baryon loading → odd peaks (1st, 3rd) enhanced relative to even (2nd); slightly lowers the sound speed, nudging peak positions.

For the sweep in this project, since you are varying `omega_cdm`, the dominant, cleanest observable is the **overall amplitude change from radiation driving**, best captured by the first-to-second (or better, first-to-third) peak height ratio.

### 4. The compensation / what-to-hold-fixed subtlety

This is where the project becomes rigorous rather than a toy. When you drive `omega_cdm` toward zero, you must decide what else stays fixed, because otherwise you conflate the dark-matter effect with trivial geometric shifts.

**CLASS enforces flatness automatically.** If you specify `omega_b`, `omega_cdm`, and `h` but do NOT set `Omega_Lambda`, `Omega_fld`, or `Omega_k`, CLASS uses the **closure equation** Σ_i Ω_i = 1 + Ω_k (with Ω_k = 0 by default) and fills in the first "unspecified" dark-energy component — by default Omega_Lambda — so the universe stays spatially flat. From `explanatory.ini` (verbatim): "The code will then use the first unspecified component to satisfy the closure equation (sum_i Omega_i) equals (1 + Omega_k) (default: 'Omega_fld' and 'Omega_scf' set to 0 and 'Omega_Lambda' inferred by code)". Practically: **do not set Omega_Lambda by hand**; let CLASS absorb the change. This means as you lower `omega_cdm` at fixed `h`, dark energy rises to compensate, keeping flatness — a physically sensible choice.

**Fixing the acoustic scale — `100*theta_s` vs letting it float.** The angular size of the sound horizon θ_s (≈ the peak spacing) is the single best-measured CMB quantity — Planck 2018 VI states in its abstract: "The angular acoustic scale is measured to 0.03% precision, with 100θ∗ = 1.0411 ± 0.0003" (the best-fit value in the parameter tables is 100θ_MC = 1.04092). CLASS lets you **fix it directly instead of `h`** using the input key `'100*theta_s'` (the literal dictionary-key string, with the asterisk; the alias `theta_s_100` is also accepted). explanatory.ini defines it as "the peak scale parameter defined exactly as 100(ds_dec/da_dec) with a decoupling time given by maximum of visibility function (quite different from theta_MC of CosmoMC and slightly different from theta_* of CAMB)". You must pass exactly one of `h`, `H0`, or `100*theta_s` — passing more than one over-determines the Hubble sector and CLASS errors out. CLASS then solves for H0 by a shooting (root-finding) algorithm.

**What each "held-fixed" choice isolates — and how the plots differ:**
- **Hold `h` fixed, let θ_s float** (simplest): lowering `omega_cdm` lowers Ω_m h², moves z_eq later, boosts the peaks via radiation driving, AND shifts peak *positions* (because the sound horizon and distance to last scattering change). Your plot shows both amplitude and horizontal shifts — pedagogically honest but "busy."
- **Hold `100*theta_s` fixed** (adjust `h`/H0 to compensate): peak *positions* stay locked, so the plot cleanly isolates the **amplitude/driving** effect of dark matter — the peaks rise and the odd/even modulation changes without sliding left/right. This is the choice that most cleanly visualizes "dark matter changes peak heights." Recommended for the headline figure.
- **Fix total matter (`omega_b + omega_cdm`) vs fix baryons**: if you lower `omega_cdm` while *raising* `omega_b` to hold Ω_m fixed, you isolate the baryon-loading (odd/even) effect at fixed z_eq. If instead you fix `omega_b` and just lower `omega_cdm` (the natural choice here), you change both the baryon *fraction* and z_eq. Wayne Hu's "baryon fraction" animation does exactly the former (raise baryon fraction by lowering CDM at fixed baryon density and fixed h).
- **Effect on z_eq**: `omega_cdm` directly sets matter-radiation equality (1+z_eq ≈ 2.4×10⁴ Ω_m h²). This is the physical driver of the amplitude change and is worth plotting/annotating alongside the peak ratio.

**Recommendation**: produce two figures — (i) the "naive" fixed-`h` sweep showing everything moving, and (ii) the fixed-`100*theta_s` sweep isolating amplitude — and explain in text what each isolates. That contrast is exactly the kind of methodological awareness that impresses.

### 5. Overlaying real Planck 2018 data

**Where to get it.** The Planck 2018 binned TT power spectrum is the file **`COM_PowerSpect_CMB-TT-binned_R3.01.txt`**, available from the Planck Legacy Archive (PLA, `pla.esac.esa.int`) and conveniently mirrored at IRSA/IPAC: `https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/cosmoparams/`. It is a small (~7 KB) ASCII file.

**File contents/format.** Columns are:
```
# l    Dl    -dDl    +dDl    BestFit
47.7   1479.3   50.8   50.8   1461.1
76.5   2035.0   54.7   54.7   2062.4
...
```
i.e. the effective (possibly non-integer) bin multipole ℓ, the band-power **D_ell = ℓ(ℓ+1)C_ℓ/2π already in µK²**, lower and upper 1σ error bars, and the ΛCDM best-fit D_ell. Because the values are already D_ell in µK², they overlay directly on your CLASS D_ell curve with **no unit conversion** — provided you converted your CLASS output to D_ell in µK² as in §2.

Two companion products are useful: the full (unbinned) high-ℓ spectrum `COM_PowerSpect_CMB-TT-full_R3.01.txt`, and the low-ℓ (2 ≤ ℓ ≤ 29) portion from Commander. For a clean portfolio plot the binned file is ideal; it spans roughly ℓ ≈ 30–2500.

**Loading and plotting:**
```python
import numpy as np, matplotlib.pyplot as plt
data = np.loadtxt('COM_PowerSpect_CMB-TT-binned_R3.01.txt')
lb, Db, errm, errp = data[:,0], data[:,1], data[:,2], data[:,3]
plt.errorbar(lb, Db, yerr=[errm, errp], fmt='.', label='Planck 2018')
plt.plot(ell, Dl, label='CLASS ΛCDM')  # from section 2
plt.xlabel(r'$\ell$'); plt.ylabel(r'$D_\ell^{TT}\ [\mu K^2]$')
plt.legend()
```

**Practical unit/binning tips (flag these):**
- Confirm both curves are D_ell (not C_ell) and both in µK² (not K²). The Planck binned file is µK²; your CLASS curve must be scaled by `(T_cmb×10^6)²`.
- The Planck points are **binned** (band powers) while CLASS gives every integer ℓ — do not try to bin CLASS unless you want a formal residual/χ² comparison; for a visual overlay, plotting the full CLASS curve through the Planck points is standard and correct.
- Some Planck theory files (e.g. `...minimum-theory_R3.01.txt`) are in **C_ell**, not D_ell — read the header. The binned data file, however, is D_ell.
- Don't attempt a real likelihood/χ²; that requires the full `plik`/covariance machinery and is out of scope (see Honesty).

### 6. The parameter sweep

**Structure:**
```python
import numpy as np
from scipy.signal import find_peaks

omega_cdm_grid = np.linspace(0.05, 0.20, 16)  # bracket Planck's 0.12
ratios = []
for oc in omega_cdm_grid:
    p = dict(base_params); p['omega_cdm'] = oc
    # (optional) hold acoustic scale fixed: drop 'h', set '100*theta_s': 1.04092
    cosmo = Class(); cosmo.set(p); cosmo.compute()
    cl = cosmo.lensed_cl(2500)
    ell = cl['ell'][2:]; Cl = cl['tt'][2:]
    Dl = ell*(ell+1)/(2*np.pi)*Cl*(cosmo.T_cmb()*1e6)**2
    peaks, props = find_peaks(Dl, distance=80, prominence=50)
    # first two acoustic peaks:
    h1, h2 = Dl[peaks[0]], Dl[peaks[1]]
    ratios.append(h1/h2)
    cosmo.struct_cleanup(); cosmo.empty()

import matplotlib.pyplot as plt
plt.plot(omega_cdm_grid, ratios, 'o-')
plt.xlabel(r'$\omega_{cdm}$'); plt.ylabel(r'$D_{\ell,1}/D_{\ell,2}$')
```

**Robust peak-finding tips (flag these):**
- Use `scipy.signal.find_peaks` on the **D_ell** array (peaks are pronounced there; on raw C_ell the damping tail hides them). A local maximum is any sample whose two neighbors are lower.
- Set a **`distance`** parameter (peaks are spaced by Δℓ ≈ 300; `distance=80–150` in integer-ℓ index prevents catching noise wiggles) and/or a **`prominence`** threshold. Planck-style papers require a point to exceed all others within `[ℓ−10, ℓ+10]`.
- Work on the **lensed** spectrum for realism, but note lensing slightly smooths peaks; for pure peak-location physics the unlensed spectrum is cleaner. State which you used.
- At high ℓ, diffusion (Silk) damping plus discrete integer ℓ makes precise peak location tricky; for the 1st/2nd peaks this is a non-issue, but if you extend to the 3rd/4th, consider a local parabola fit around each `find_peaks` index for sub-ℓ precision.
- Guard against edge cases: if `omega_cdm` is pushed very low, peak amplitudes and spacing change enough that you should assert `len(peaks) >= 2` and sanity-check the first peak sits near ℓ≈200–250.

**Expected result**: as `omega_cdm` decreases, radiation driving strengthens and the peaks (especially higher ones) rise; the first/second ratio changes monotonically over the grid. You will visually reproduce the textbook trend and can annotate the Planck best-fit value (0.12) on the curve.

### 7. Honesty and framing

**What this project legitimately demonstrates:**
- Competence installing and driving a research-grade Boltzmann code (CLASS) via its Python API.
- Correct handling of cosmological unit conventions (C_ell → D_ell, µK²).
- Understanding of the physics of acoustic peaks, radiation driving, and baryon loading.
- A controlled numerical experiment (parameter sweep) with awareness of degeneracies (what's held fixed).
- Comparison of theory to real Planck 2018 public data.

**What it does NOT demonstrate / must not be claimed:**
- It is **not novel research**. Everything here is a well-established textbook result from the 1990s–2000s (Hu & Sugiyama, Hu & Dodelson) and confirmed by WMAP/Planck.
- It is **not a cosmological parameter fit or measurement**. A visual overlay is not a likelihood analysis; you are not "measuring" Ω_c from Planck (that needs the plik likelihood + covariance + MCMC).
- Don't claim to have "discovered" or "proven" dark matter — you reproduced the *known signature*.

**Accurate one-sentence description**: *"Using the CLASS Boltzmann code, I reproduced the known dependence of the CMB temperature power spectrum's acoustic-peak heights on the cold dark matter density, quantified it with a peak-height-ratio sweep, and validated the baseline model against Planck 2018 data."* That is honest, specific, and genuinely impressive for a high-school student.

### 8. Relevant references

**CMB acoustic-peak physics (accessible → advanced):**
- **Wayne Hu's CMB tutorials** — `background.uchicago.edu` — especially the "Intermediate" tour (Baryons/Inertia, Baryonmeter, Higher Peaks/Driving Force, Dark Matter Density pages). The single best intuition-building resource; includes animations of varying Ω_c h² and Ω_b h².
- **Hu & Dodelson (2002)**, "Cosmic Microwave Background Anisotropies," Ann. Rev. Astron. Astrophys. 40, 171 — the standard review; the odd/even and driving physics with the spring analogy.
- **Wayne Hu, "Lecture Notes on CMB Theory: From Nucleosynthesis to Recombination"** (arXiv:0802.3688) — detailed, figure-rich.
- **Dodelson & Schmidt, *Modern Cosmology* (2nd ed.)** — textbook derivations of the Boltzmann hierarchy and acoustic oscillations.
- **Hu & Sugiyama (1995, 1996)** — original radiation-driving and potential-decay treatment.

**CLASS code and documentation:**
- CLASS website `class-code.net` and GitHub `github.com/lesgourg/class_public`; the `explanatory.ini` file is the complete input-parameter reference.
- **Lesgourgues (2011)**, "The Cosmic Linear Anisotropy Solving System (CLASS)" — arXiv:1104.2932 (overview) and arXiv:1104.2933 (Part II: approximation schemes) — the papers to cite.
- Lesgourgues/Tram tutorial slides and the `classy` wrapper notebooks (the ICG/CosmoTools lecture series) for the Python API.

**Planck 2018 (parameters and data):**
- **Planck 2018 results VI. Cosmological parameters** (arXiv:1807.06209) — Table 1/2 for the best-fit values.
- **Planck 2018 results I. Overview** (arXiv:1807.06205) — Table 5 for the measured peak positions/amplitudes.
- **Planck 2018 results V. CMB power spectra and likelihoods** (A&A 641, A5) — how the spectra/data products are constructed.
- **Planck Legacy Archive** (`pla.esac.esa.int`) and IRSA mirror for the `COM_PowerSpect_CMB-*` files.

## Recommendations

**Stage 1 — Environment & baseline (do first).** Create a fresh venv, `pip install classy numpy scipy matplotlib`, run the sanity check, then reproduce the Planck baseline TT curve and overlay `COM_PowerSpect_CMB-TT-binned_R3.01.txt`. **Success benchmark**: your first peak sits at ℓ ≈ 220.6 with D_ell ≈ 5733 ± 39 µK² (the Planck 2018 measured value) and the curve threads the Planck error bars. If units look off by ~10^12 or the peak is at the wrong height, you forgot the `T_cmb²`-in-µK² factor — the #1 bug.

**Stage 2 — Physics sweep.** Implement the `omega_cdm` sweep with `find_peaks`; produce the peak-ratio-vs-`omega_cdm` plot. **Benchmark**: monotonic trend, Planck's 0.12 marked. Add a second panel plotting z_eq vs `omega_cdm` to connect cause (equality) to effect (driving).

**Stage 3 — The rigor upgrade (what sets it apart).** Produce the paired figures from §4: one fixed-`h` sweep (everything moves) and one fixed-`100*theta_s` sweep (positions locked, amplitude isolated). Write 2–3 paragraphs explaining what each isolates. **This is the single highest-leverage addition for impressing a professor.**

**Stage 4 — Packaging.** Put it in a GitHub repo with: a `requirements.txt` pinning versions, a `README` with the honest one-sentence framing, a reproducibility note (classy version 3.3.4.0, Planck file version R3.01), and clean commented notebooks. Write the LinkedIn post around the honest framing, not hype. In cold emails, lead with the methodological awareness ("I was careful to hold the acoustic scale fixed to isolate the driving effect") — that signals maturity.

**What would change these recommendations:** If you want to go further and can invest more time, the natural next step is a real χ² against the binned Planck data (still not a full likelihood, but quantitative) — only pursue this once Stages 1–3 are solid. If installation via pip fails repeatedly on your OS, switch to building from source or use WSL/conda before spending more time debugging pip.

## Caveats
- **Not a measurement or novel result** — see §7. Frame accordingly.
- **Wrapper vs file-output convention differs**: the Python wrapper returns bare C_ell; CLASS's `.dat` files include the `ℓ(ℓ+1)/2π` factor. Don't assume they match.
- **Neutrino settings matter at the ~1% level**: use the Planck baseline (`N_ncdm=1, m_ncdm=0.06, N_ur=2.0328`) for a faithful reproduction; omitting massive neutrinos shifts the high-ℓ spectrum slightly.
- **Lensing smooths peaks**: choose lensed vs unlensed deliberately and state your choice; it slightly affects peak heights (a few %) but not the qualitative trend.
- **The `100*theta_s` shooting** adds compute time per model and occasionally fails to converge for extreme parameter values; catch exceptions in the sweep loop.
- **Cython/version drift**: if you revisit the project months later and NumPy has had a major release, rebuild `classy` in a clean env to avoid ABI mismatches.
- **Peak-finding fragility** at low `omega_cdm` or high ℓ — assert you found ≥2 peaks and validate positions.
- **Source-quality note**: the parameter values quoted are cross-checked against Planck 2018 VI (arXiv:1807.06209) and the CLASS baseline files; the two differ at the 4th–5th significant figure (different dataset combinations/rounding), which is immaterial for this project.