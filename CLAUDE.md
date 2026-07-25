# CLAUDE.md

## What this project is
A portfolio-grade cosmology project reproducing the CMB temperature power spectrum's
acoustic peak-height asymmetry using the CLASS Boltzmann code (via the `classy` Python
wrapper), then running a sensitivity study on the cold dark matter density and overlaying
real Planck 2018 data. Full technical reference: see `RESEARCH_BLUEPRINT.md` in this repo.

## Honesty rule (non-negotiable)
This reproduces a known textbook result. It is NOT novel research and NOT a parameter
measurement. Never write code comments, README text, or commit messages that overclaim
(no "discovered," "proved dark matter," "new constraint"). The accurate framing lives in
section 7 of the blueprint. I need to be able to explain every physics choice myself, so
when you make one, explain the reasoning briefly rather than burying it.

## Tool division of labor
Avoid running conflicting tasks on the same files at the same time.

- **Claude Code** — terminal commands, installing/building `classy`, running code and
  tests, surgical single-file edits, debugging tracebacks, git operations.
- **Cowork** — larger visual work: discussing multi-file structure, reviewing the repo
  layout side by side, planning features, reasoning about the physics or the writeup
  before code exists.

Rough rule: if it touches the terminal or edits one file precisely, it's Code. If it's
"let's think/look at several things together," it's Cowork.

## Working style
- I code regularly in Python, so don't over-explain syntax; do explain physics and
  cosmology choices (units, what's held fixed in a sweep, etc.).
- I prefer brief, direct responses.
- Pin versions when installing (classy is currently 3.3.4.0). Use a virtual environment.
- Before committing, sanity-check against the blueprint's benchmarks (first peak at
  l ~ 220.6, D_l ~ 5733 uK^2).
