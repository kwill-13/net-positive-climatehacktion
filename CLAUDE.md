# SunSafe

## Core idea

SunSafe helps Pacific island energy officers plan diesel-to-solar mini-grids that still
work in year 15, and turns the plan into a funding case.

- The default recommendation is the lowest 15-year-cost design that meets the renewable target every year, not the design-year-1 result.

## Ownership

- William: energy model (`sunsafe/energy/`) AND lifecycle/finance model (`sunsafe/lifecycle/`),
  plus `sunsafe/config.py` and `sunsafe/model.py`.
- App (Streamlit, `app/`): jkon0035-alt. Also covering data/validation
  (load profiles, `scripts/run_tokelau.py`, `SOURCES.md`) while the data teammate is unavailable.

## Ground rules

- The model freeze was lifted on 3 Oct 2026 (tag `model-freeze-2026-10-03` marks the frozen state).
  Changes to defaults or model logic still go through William, with a sourced reason.
- `sunsafe/interface.py` is the model-app contract (data definitions only): do not rename or
  change its fields. The implementation is `sunsafe.model.run_sunsafe`; there is no fake model.
- All assumptions live in `sunsafe/config.py` with units; placeholders are marked TODO.
- Don't tune the model to hit the Tokelau validation numbers; report the gap and source the assumptions.
- Dependencies: numpy, pandas, requests, pytest for the model. `streamlit` (>=1.39) is allowed
  for `app/` only; the model must not import it. Ask before adding more.
- Setup and repo map: README.md. How each part calls the model: HANDOFF.md.
- Upload source files only (no `__pycache__`/`.pyc`); prefer git from the command line.

## App (`app/`)

- Run from repo root: `streamlit run app/app.py`. Live link deployed on Streamlit Cloud.
- Uses the real model: `from sunsafe.model import run_sunsafe` in `app/components/layout.py`.
  If the import or a run fails, it shows the error (sidebar and Site Setup) and no results.
- Only `app/components/layout.py` imports the model. Pages read fields off `Results`.
- Results are cached with `st.cache_data`; a new site fetches NASA POWER weather (~15 s).
- Default diesel price is USD 2.70/L (Tokelau delivered price, derived; see SOURCES.md item 5).
  Below USD 2.34/L (8%) or 2.11/L (6%) diesel-only is cheaper per kWh. Apia retail 2026
  (USD 1.17-1.93/L) is a lower bound, not a site price.
- Shows the recommended strategy (from the `Recommended:` warning), model notes, a stale-inputs warning,
  and a Fakaofo validation table (comparison only, not a pass/fail claim).
- Never put engineering calculations in the app. Only app-side conversion: diesel litres to tCO2e
  (2.68 kg CO2/L) in `app/utils/formatting.py`.

## Reference run (Fakaofo, 600 kWh/day, lead-acid, 95%, USD 2.70/L)

Recommended: 315 kWp / 1,481 kWh, planned battery replacement in year 10; capex ~USD 1.31M
(placeholder costs); payback ~7.7 yrs vs ~9 reported; ~13% cheaper over 15 years than building big.
Year-1 optimum (184 kWp / 750 kWh) undersizes against the real 2012 install (Source A: 265-365 kWp,
1.1-1.6 MWh per atoll; Source B: over 8 MWh total, ~2.7 MWh per atoll). Recommended battery is
within Source A, about 0.56x Source B. Real-system payback: 10.9 yrs at NZD 7M (NZ advance),
13.3 yrs at NZD 8.5M (total). All reference figures are quoted in `SOURCES.md`.

## Known limitations (state these in any write-up)

- Placeholders: load shape, capital costs, battery fade, demand growth, headroom loads.
- The two battery reference sources differ by about 2x.
- Model capex is lower than the real project's; modelled real-system payback is 10.9-13.3 yrs vs ~9 reported.
- Historical load growth was reported as 9%/yr (ITP 2019); the model uses a 3%/yr placeholder.
- Results depend heavily on delivered diesel price.
- Interface gaps: no fuel-shock slider function, no per-load backup hours, no kWh/day per new use.

## Status checklist (as of 2026-10-03)

App:
- [x] Switch app from the fake model to `sunsafe.model.run_sunsafe`
- [x] Lifecycle chart (day-one vs year-15), the hero visual
- [x] Fuel-shock and headroom views
- [x] Proposal and community one-pager export
- [ ] Deployed link tested end to end by someone outside the team

Data and validation:
- [x] Test 1: sizing vs Tokelau, framed as "day-one undersizes, year-8/15 lands near reality"
- [ ] Test 2: 15-year decline of the real system (script sections 3 and 5), reported across fade 0.04-0.08. Output exists; write down the pass criteria before comparing, with the placeholder-fade caveat.
- [ ] Test 3: REopt cross-check (first to cut if time runs short; keep the API key out of the repo)
- [ ] Source every reference number in `SOURCES.md`
- [ ] Tokelau technical review, if anyone managed to download it
- [ ] Pre-run demo sites online so NASA weather is cached in `data/cache/`
