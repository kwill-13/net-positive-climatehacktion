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
- Default diesel price is USD 1.87/L (`config.TOKELAU_DIESEL_PRICE_USD_PER_L`): the Apia 2026 average,
  x1.25 freight to Tokelau (SOURCES.md P1). Scenarios: low 1.22 (2013 landed), high 2.70 (the old
  all-fuel derivation). Below USD 2.34/L (8%) or 2.11/L (6%), diesel-only is cheaper per kWh, and
  that includes the default.
- Shows the recommended strategy (from the `Recommended:` warning), model notes, a stale-inputs warning,
  and a Tokelau validation table for Fakaofo, Nukunonu and Atafu (comparison only, not a pass/fail
  claim; warns when inputs differ from the validation case). Other sites show a "not validated" note.
- Never put engineering calculations in the app. Only app-side conversion: diesel litres to tCO2e
  (2.68 kg CO2/L) in `app/utils/formatting.py`.

## Reference run (Fakaofo, 600 kWh/day, lead-acid, 95%, USD 1.87/L)

- **Recommended:** 315 kWp / 1,481 kWh, with a planned battery replacement in year 10; capex ~USD 1.31M
  (placeholder costs).
- **Strategy:** NPV USD 1.82M vs 2.10M for building big (~13.5% cheaper).
- **Cost per kWh:** at USD 1.87/L the hybrid costs $0.82/kWh vs $0.66/kWh diesel-only, so diesel-only
  is cheaper per kWh (breakeven USD 2.34/L). Simple payback is 12.1 yrs.
- **Validation** (real 2012 systems, IRENA 2013; nominal vs nominal):
  - PV 315 kWp vs Fakaofo's 330 (0.95x).
  - Battery 1,481 kWh vs 3,379 kWh nominal (0.44x); usable 740 vs 1,690 kWh (0.44x).
  - The year-1 optimum (184 kWp / 750 kWh) undersizes further.
- **Real-system payback** at USD 1.87/L: 19.5 yrs (NZD 7M) / 23.7 yrs (NZD 8.5M) vs ~9 reported.
  Config O&M may be overstated (SOURCES.md P11). All reference figures are in `SOURCES.md`.

## Known limitations (state these in any write-up)

- Placeholders: load shape, capital costs, battery fade, demand growth, headroom loads.
- The battery references are reconciled (nominal 2.46-3.38 MWh per atoll; ITP's 1.1-1.6 MWh is the usable half).
- The model's battery is ~0.44x the real one (nominal vs nominal); PV matches.
- Modelled real-system payback is 19.5-23.7 yrs at USD 1.87/L vs ~9 reported (method unknown; config O&M may be high).
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
