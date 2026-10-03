# SunSafe

## Core idea

SunSafe helps Pacific island energy officers plan diesel-to-solar mini-grids that still
work in year 15, and turns the plan into a funding case.

- The default recommendation is the lowest 15-year-cost design that meets the renewable target every year, not the design-year-1 result.

## Ownership

- William: energy model (`sunsafe/energy/`) AND lifecycle/finance model (`sunsafe/lifecycle/`),
  plus `sunsafe/config.py` and `sunsafe/model.py`.
- Teammates: app (Streamlit), data/validation (load profiles, `scripts/run_tokelau.py`).

## Ground rules

- `sunsafe/interface.py` is the model-app contract: do not rename or change its fields.
- All assumptions live in `sunsafe/config.py` with units; placeholders are marked TODO.
- Don't tune the model to hit the Tokelau validation numbers; report the gap.
- Dependencies: numpy, pandas, requests, pytest only (ask before adding more).
- Setup and repo map: README.md. How each part calls the model: HANDOFF.md.
