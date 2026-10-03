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

Assumes 9%/yr demand growth and 3%/yr lead-acid fade (both Tokelau-derived).
- **Recommended: staged expansion (C).** Build 363 kWp / 1,612 kWh (capex ~USD 1.47M). In year 9,
  add 332 kWp and a new 2,858 kWh battery.
  - This matches what Tokelau actually did: built in 2012, then in 2020 (~year 8) added 210 kWp
    and ~2 MWh of Li-ion.
- **Strategy:** NPV USD 2.80M vs 3.76M for building big (~26% cheaper) and 3.46M for the best
  same-size replacement (~19% cheaper).
- **Cost per kWh:** at USD 1.87/L the hybrid costs $0.86/kWh vs $0.66/kWh diesel-only. Breakeven is
  USD 2.48/L (8%); simple payback 14.2 yrs.
- **Validation** (real 2012 systems, IRENA 2013; nominal vs nominal):
  - The first build vs Fakaofo's 330 kWp / 3,379 kWh: PV 1.10x, battery 0.48x (0.48x usable too).
    The year-1 optimum (184 kWp / 750 kWh) is 0.56x / 0.22x.
  - The real system (330 / 3,379) at 600 kWh/day with 9% growth first drops below 95% in year 9
    (year 7 at 720), matching its actual upgrade after ~8 yrs.
  - Measured 2013 solar fraction: model 96-97% (Atafu) / 95-96% (Nukunonu) on actual 2012-13
    weather vs 92.5% / 93.5% measured. The model is mildly optimistic (run_tokelau.py section 8).
- **Real-system payback** at USD 1.87/L: 19.5 yrs (NZD 7M) / 23.7 yrs (NZD 8.5M); 13.8 / 16.7 yrs
  with ITP's solar O&M; ~9 reported. All reference figures are in `SOURCES.md`.

## Known limitations (state these in any write-up)

- Placeholders: load shape, PV capex point value (sourced range USD 2,500-4,000/kW), lithium fade,
  headroom inputs (except the freezer).
- The battery references are reconciled (nominal 2.46-3.38 MWh per atoll; ITP's 1.1-1.6 MWh is the usable half).
- Staged expansion (C) assumes the upgrade happens on time and is funded; added PV is costed at
  today's real price and derated like the original panels.
- The model over-predicts the 2013 solar fraction by ~1-4 points (outages, shading and generator
  charging are not modelled).
- Modelled real-system payback is 13.8-23.7 yrs (O&M dependent) vs ~9 reported (method unknown).
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
