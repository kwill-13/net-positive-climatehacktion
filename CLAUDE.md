# SunSafe

## Core idea

SunSafe helps Pacific island energy officers plan diesel-to-solar mini-grids that still
work in year 15, and turns the plan into a funding case.

- The default recommendation is the lowest 15-year-cost design that meets the renewable target every year, not the design-year-1 result.

## Ownership

- William: energy model (`sunsafe/energy/`) AND lifecycle/finance model (`sunsafe/lifecycle/`),
  plus `sunsafe/config.py` and `sunsafe/model.py`.
- App (Streamlit, `app/`): jkon0035-alt. Currently also covering data/validation
  (load profiles, `scripts/run_tokelau.py`) because the data teammate is unavailable.

## Ground rules

- MODEL FROZEN (3 Oct 2026): do not change defaults in `sunsafe/config.py` or model logic.
  Only documentation, comments, sources and bug fixes agreed with William.

- `sunsafe/interface.py` is the model-app contract: do not rename or change its fields.
- All assumptions live in `sunsafe/config.py` with units; placeholders are marked TODO.
- Don't tune the model to hit the Tokelau validation numbers; report the gap.
- Model dependencies: numpy, pandas, requests, pytest only (ask before adding more).
  Exception: `streamlit` is allowed for the app in `app/` only; the model must not import it.
- Setup and repo map: README.md. How each part calls the model: HANDOFF.md.

## App (`app/`)

- Run from repo root: `streamlit run app/app.py`.
- Only `app/components/layout.py` imports the model. Pages read fields off `Results`.
- Any result carrying a warning containing "FAKE" shows the DEMO MODE banner;
  the banner disappears once the real model replaces the fake one.
- Never put engineering calculations in the app. The only app-side conversion is
  diesel litres to tCO2e (2.68 kg CO2/L) in `app/utils/formatting.py`.
- Pages: Site Setup, System Design, Lifecycle (hero: day-one vs year-15 chart),
  Financials (fuel-shock series), Electrification (headroom), Funding Case
  (Markdown proposal and community one-pager).

## Known interface gaps (agree with model owner, update `interface.py` first)

- Fuel-shock slider needs a function such as `run_fuel_shock(results, shock_pct)`;
  `Results` only has a fixed monthly series, so the app plots that.
- Backup hours are one number; per-critical-load hours are not available.
- Headroom has no kWh/day per new use (cooking, ice, cold storage).
- Validation panel on System Design says "Not yet connected" until predicted-vs-reference
  values are agreed.

## Status checklist (as of 2026-10-03, all open)

App:
- [ ] Switch app from the fake model to `sunsafe.model.run_sunsafe`
- [ ] Lifecycle chart (day-one vs year-15), the hero visual
- [ ] Fuel-shock and headroom views
- [ ] Proposal and community one-pager export
- [ ] Deployed to a public link and tested by someone outside the team

Data and validation:
- [ ] Test 1: sizing vs Tokelau, framed as "day-one undersizes, year-8/15 lands near reality"
- [ ] Test 2: decline checkpoints (Table 2 passes on current numbers; confirm with real lifecycle code)
- [ ] Test 3: REopt cross-check (first to cut if time runs short)
- [ ] Tokelau technical review, if anyone managed to download it

Note: first app build (all pages, exports, DEMO banner) is done and running against
`run_sunsafe_fake`; the app checklist items above still need verifying against the real model.
