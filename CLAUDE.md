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

- **The model is frozen** (tag `model-freeze-2026-10-03`). No changes to defaults or model logic.
  If a number looks wrong, raise it with William; do not edit `config.py`.
- `sunsafe/interface.py` is the model-app contract: do not rename or change its fields.
- All assumptions live in `sunsafe/config.py` with units; placeholders are marked TODO.
- Don't tune the model to hit the Tokelau validation numbers; report the gap and source the assumptions.
- Dependencies: numpy, pandas, requests, pytest for the model. `streamlit` (>=1.39) is allowed
  for `app/` only; the model must not import it. Ask before adding more.
- Setup and repo map: README.md. How each part calls the model: HANDOFF.md.
- Upload source files only (no `__pycache__`/`.pyc`); prefer git from the command line.

## App (`app/`)

- Run from repo root: `streamlit run app/app.py`. Live link deployed on Streamlit Cloud.
- Uses the real model: `from sunsafe.model import run_sunsafe` in `app/components/layout.py`.
  If the import or run fails, it falls back to the fake model and shows the error in the sidebar.
- Only `app/components/layout.py` imports the model. Pages read fields off `Results`.
- Results are cached with `st.cache_data`; a new site fetches NASA POWER weather (~15 s).
- Default diesel price is USD 2.70/L (Tokelau delivered price). Below about USD 2.3/L (8%) or
  2.1/L (6%) diesel-only is cheaper per kWh. Apia retail (~USD 1.10) is a lower bound, not a site price.
- Shows the recommended strategy (from the `Recommended:` warning), model notes, a stale-inputs warning,
  and a Fakaofo validation table (comparison only, not a pass/fail claim).
- Never put engineering calculations in the app. Only app-side conversion: diesel litres to tCO2e
  (2.68 kg CO2/L) in `app/utils/formatting.py`.

## Reference run (Fakaofo, 600 kWh/day, lead-acid, 95%, USD 2.70/L)

Recommended: 315 kWp / 1,481 kWh, planned battery replacement in year 10; capex ~USD 1.31M
(placeholder costs); payback ~7.7 yrs vs ~9 reported; ~13% cheaper over 15 years than building big.
Year-1 optimum (184 kWp / 750 kWh) undersizes against the real 2012 install (265-365 kWp, 1.1-1.6 MWh).
Reference sources still need citing (see `SOURCES.md`).

## Known limitations (state these in any write-up)

- Placeholders: load shape, capital costs, battery fade, demand growth, headroom loads.
- The two battery reference sources differ by about 2x.
- Model capex is lower than the real project's; model payback differs from the reported ~9 years.
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
