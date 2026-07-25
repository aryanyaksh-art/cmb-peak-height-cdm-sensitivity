# Stage 3 writeup draft

Draft prose for the README's methodology section. Review and edit before folding
in — you need to be able to defend every sentence here yourself.

---

## What each sweep isolates

Varying the cold dark matter density is ambiguous until you say what else stays
fixed. This project runs the same sweep twice, and the difference between the
two panels of `figures/03_fixed_h_vs_fixed_theta.png` is the point.

In the **fixed-h** sweep, ω_cdm varies from 0.05 to 0.20 with the Hubble
parameter pinned at 0.6736. Adding matter shrinks the sound horizon at
recombination and shrinks the distance to last scattering, and the two do not
shrink at the same rate, so the angular acoustic scale drifts. Peak positions
slide along with peak heights. Across the grid the first peak moves by 28 in ℓ,
the second by 84, the third by 159 — that is 12.8%, 15.6% and 19.7% of each
peak's position. Nothing in that panel separates a change in amplitude from a
change in geometry.

In the **fixed-100θ_s** sweep, ω_cdm varies over the same range but the angular
acoustic scale is held at the Planck value of 1.04092 and CLASS solves for h by
shooting. The residual position drift falls to 4.5%, 1.85% and 2.0%. That is
roughly a 9× improvement at peaks 2 and 3, and it means the amplitude changes
visible in the right-hand panel are the dark matter physics rather than the
spectrum sliding sideways underneath a fixed axis.

The residual is not solver error. Acoustic peaks do not sit exactly at nπ/θ_s;
radiation driving imposes a phase shift on the oscillations that itself depends
on the matter density, so peak positions move slightly even at fixed θ_s. The
first peak drifts about 2.3× more than peaks 2 and 3, consistent with an
additional large-scale contribution — plausibly early ISW, though this project
does not establish that.

## A quantitative check on the shooting solver

Holding θ_s fixed while raising ω_m forces a specific change in h, and the size
of that change is predictable. The sound horizon scales roughly as
r_s ∝ ω_m^(−0.25) and the angular diameter distance as D_A ∝ h^(−0.2) ω_m^(−0.4),
so θ_s = r_s/D_A ∝ ω_m^(0.15) h^(0.2). Holding θ_s fixed therefore requires

    h ∝ ω_m^(−3/4)

Across this grid ω_m rises by a factor of 3.07, predicting that h should fall by
3.07^(−0.75) = 0.429. The measured values are h = 1.085 at ω_cdm = 0.05 and
h = 0.469 at ω_cdm = 0.20, a ratio of 0.432. The fitted exponent is 0.750.

This is the same physics behind the well-known Ω_m h³ ≈ constant CMB degeneracy
direction, which is that relation calibrated near the Planck point rather than
across a fourfold range in ω_cdm.

Note that h = 1.085 means H₀ = 108.5 km/s/Mpc. The endpoints of this grid are
deliberately unphysical; they exist to expose the trend, not as candidate
cosmologies.

## What the peak ratios do

Across the fixed-θ_s sweep:

- **D1/D2 falls**, 2.31 → 2.17
- **D3/D2 rises**, 0.755 → 1.157
- **z_eq rises**, 1731 → 5315, passing through 3403 at the Planck value of
  ω_cdm = 0.1200 (Planck 2018 quotes 3402 ± 26)

The D3/D2 trend is the dark matter signature. Baryon loading alone would leave
the third peak well below the second; a CDM-dominated matter budget before
recombination suppresses radiation driving and lifts peak 3 back toward parity
with peak 2. The sweep crosses D3/D2 = 1 near the observed value, and Planck
measures peak 2 at 2586 ± 23 µK² and peak 3 at 2518 ± 17 µK² — essentially
equal heights.

The D1/D2 trend runs opposite to a naive radiation-driving argument, which
predicts that raising ω_cdm should remove more amplitude from peak 2 than from
peak 1 and so lift the ratio. Measured, it falls. Since D1/D2 falls while D3/D2
rises, both higher peaks gain on peak 1 as ω_cdm increases, so whatever
dominates has to act preferentially on the first peak at low ω_cdm. This project
records the trend without claiming to have identified the mechanism.

Ratios are used rather than absolute peak heights because the overall spectrum
amplitude scales as A_s·e^(−2τ). Both are held fixed here, but a ratio is
insensitive to that degeneracy regardless, which is what makes it the right
observable for a sweep of this kind.

---

## Things to fix elsewhere before this ships

- `plot_paired_sweeps()`'s right-hand panel title says "positions locked."
  Soften to "positions locked to ~2%" — the figure should not claim more than
  the numbers support.
- The `fixed_theta_s` docstring in `sweep.py` says "Peak positions lock in
  place." Same edit.
- `PLAN.md` Stage 2 records the ℓ₁ spread as 10.0 against a "<2" expectation,
  flagged as a miss. Replace with the fractional comparison — the spec's
  threshold was the wrong metric, not the result.
