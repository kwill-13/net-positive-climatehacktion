# SunSafe

## Core idea

SunSafe helps Pacific island energy officers plan diesel-to-solar mini-grids that still
work in their final year (projects of 10-25 years, default 15), and turns the plan into a funding case.

- The recommendation is the lowest-cost plan over the project (NPV, 8%) that meets the renewable target
  every year, chosen from four strategies (A build big, B replace battery once, C expand once, D expand
  in stages), not the design-year-1 result.

## Ownership

- William: energy model (`sunsafe/energy/`) AND lifecycle/finance model (`sunsafe/lifecycle/`),
  plus `sunsafe/config.py` and `sunsafe/model.py`.
- App (Streamlit, `app/`): jkon0035-alt. Also covering data/validation
  (load profiles, `scripts/run_tokelau.py`, `SOURCES.md`) while the data teammate is unavailable.

## Ground rules

- **MODEL FROZEN** (re-frozen 4 Oct 2026 after the rolling plan + growth schedule merged; tag
  `model-freeze-2026-10-04`. Tag `model-freeze-2026-10-03` marks the earlier frozen state.)
  Any change to defaults or model logic goes through William, with a sourced reason.
- `sunsafe/interface.py` is the model-app contract (data definitions only): do not rename or
  change its fields. (`Results.plan_stages` was added 4 Oct as an optional field, default `[]`.) The implementation is `sunsafe.model.run_sunsafe`; there is no fake model.
- All assumptions live in `sunsafe/config.py` with units; placeholders are marked TODO.
- Don't tune the model to hit the Tokelau validation numbers; report the gap and source the assumptions.
- Dependencies: numpy, pandas, requests, pytest for the model. `streamlit` (>=1.45), `folium` and
  `streamlit-folium` are allowed for `app/` only; the model must not import them. Ask before adding more.
- Setup and repo map: README.md. How each part calls the model: HANDOFF.md.
- Upload source files only (no `__pycache__`/`.pyc`); prefer git from the command line.

## App (`app/`)

- Run from repo root: `streamlit run app/app.py`. Live link deployed on Streamlit Cloud (reboot it from
  Manage app after a push).
- Structure: `app/app.py` (page config + `st.navigation`), `app/views/` (home, island, plan, checks),
  `app/components/layout.py` (model call, presets, map, shared UI, one CSS block),
  `app/components/charts.py` (the eight Altair charts + shared theme), `app/exports/proposal.py`.
- Pages: **Home** (hero, Start planning, three step cards); **1 Your island** (folium click map with
  preset markers, inputs in cards, growth schedule default 9% for 5 years then 3%, "Build my plan");
  **2 Your plan** (summary, decision cards, eight charts with decision captions, exports);
  **3 How we know it works** (live Tokelau validation table, sensitivity, sources, placeholders).
  Every page has a header bar with the wordmark and a 1-2-3 stepper.
- Uses the real model: `run_sunsafe_detailed` in `app/components/layout.py` (one cached call per plan,
  growth schedule passed as `growth=`). If the import or a run fails, it shows the error and no results.
- Only `app/components/layout.py` imports the model. Pages read fields off `Results`.
- Results are cached with `st.cache_data`; a new site fetches NASA POWER weather (~15 s). The price
  curve (USD 1.00-3.50/L) reuses the one run: the plan is fixed and costs are linear in diesel price.
- Default diesel price is USD 1.87/L (`config.TOKELAU_DIESEL_PRICE_USD_PER_L`): the Apia 2026 average,
  x1.25 freight to Tokelau (SOURCES.md P1). Scenarios: low 1.22 (2013 landed), high 2.70 (the old
  all-fuel derivation). Below USD 2.42/L (8%) or 2.25/L (6%), diesel-only is cheaper per kWh, and
  that includes the default.
- Non-Pacific coordinates get a note that defaults (freight, growth) are set for Pacific islands. Sites
  other than the Tokelau atolls link "Planning estimate. Engine checked against Tokelau's measured
  performance" to page 3, which also compares a Tokelau-atoll plan with its real 2012 system.
- Never put engineering calculations in the app. Only app-side conversion: diesel litres to tCO2e
  (2.68 kg CO2/L) in `app/utils/formatting.py`.

## Reference run (Fakaofo, 600 kWh/day, lead-acid, 95%, USD 1.87/L)

Assumes 9%/yr demand growth (constant) and 3%/yr lead-acid fade (both Tokelau-derived), 15 years.
Strategies: A build big, B same-size replacement, C staged expansion, D rolling plan (stages of
6/8/10 yrs, new battery + added PV each stage). All figures are from `scripts/run_tokelau.py`, which
runs all four strategies, the same as the app (page 3 shows the same validation table).
- **Recommended: D, rolling plan, 6-yr stages.** Build 305 kWp / 1,277 kWh (638 kWh usable; capex
  ~USD 1.21M). Year 7: +219 kWp and a new 2,141 kWh battery. Year 13: +139 kWp and a new 2,664 kWh battery.
  - Tokelau built in 2012 and upgraded in 2020, after ~8 years: +210 kWp and ~2 MWh of Li-ion. The
    plan's first upgrade is a similar size (PV 1.04x, battery 1.07x) but ~2 years earlier, because the
    cheapest plan builds smaller and upgrades sooner.
- **Strategy:** NPV USD 2.74M vs 3.76M for building big (27% cheaper); best C 2.80M, best B 3.46M.
- **Cost per kWh:** at USD 1.87/L the hybrid costs $0.84/kWh vs $0.66/kWh diesel-only. Breakeven is
  USD 2.42/L (8%) or 2.25/L (6%); simple payback on the first build 10.9 yrs (upgrades not included).
- **Validation** (real 2012 systems, IRENA 2013):
  - The first build vs Fakaofo's 330 kWp / 3,379 kWh nominal (1,690 usable): PV 0.93x, battery 0.38x
    (nominal and usable). The year-1 optimum (184 kWp / 750 kWh) is 0.56x / 0.22x.
  - The real system (330 / 3,379) at 600 kWh/day with 9% growth first drops below 95% in year 9
    (year 7 at 720), matching its actual upgrade after ~8 yrs.
  - Measured 2013 solar fraction: model 96-97% (Atafu) / 95-96% (Nukunonu) on actual 2012-13
    weather vs 92.5% / 93.5% measured. The model is mildly optimistic (run_tokelau.py section 8).
- **Real-system payback** at USD 1.87/L: 19.5 yrs (NZD 7M) / 23.7 yrs (NZD 8.5M); 13.8 / 16.7 yrs
  with ITP's solar O&M; ~9 reported. All reference figures are in `SOURCES.md`.
- **App default** (same site, growth 9% for 5 yrs then 3%): **C, expand once in year 9.** Build 324 kWp /
  1,439 kWh (720 usable), $1.31M; year 9 +94 kWp and a new 1,717 kWh battery (859 usable), $668k. NPV
  $2.06M, 9% below building big. Set aside $100k/yr. $0.74/kWh full hybrid vs $0.66 diesel; the island
  pays $0.27/kWh if donors fund the first build; full-cost breakeven $2.12/L.

## Known limitations (state these in any write-up)

- Placeholders: load shape, PV capex point value (sourced range USD 2,500-4,000/kW), lithium fade,
  headroom inputs (except the freezer).
- The battery references are reconciled (nominal 2.46-3.38 MWh per atoll; ITP's 1.1-1.6 MWh is the usable half).
- Staged expansion (C) and the rolling plan (D) assume each upgrade happens on time and is funded; added PV is costed at
  today's real price and derated like the original panels.
- In the validation case the cheapest plan's first upgrade comes ~2 years earlier than Tokelau's real one.
- The model over-predicts the 2013 solar fraction by ~1-4 points (outages, shading and generator
  charging are not modelled).
- Modelled real-system payback is 13.8-23.7 yrs (O&M dependent) vs ~9 reported (method unknown).
- Results depend heavily on delivered diesel price.
- `om_fund_per_year_usd` saves only toward the first reinvestment; D's later stages are in NPV/LCOE
  but not in the yearly fund figure.
- Interface gaps: no fuel-shock slider function, no per-load backup hours, no kWh/day per new use.

## Status checklist (as of 2026-10-04)

Model:
- [x] Strategies A-D (rolling plan) and the growth schedule; `Results.plan_stages`; model re-frozen
- [x] Validation, sensitivity and Pacific presets all run on the current engine (A-D)

App:
- [x] Real model only; planning flow (Home, Your island, Your plan, How we know it works)
- [x] Click map, decision cards, eight charts with findings in their titles, live validation table
- [x] Funding proposal (HTML with charts) and community one-pager exports
- [x] Checked in Chrome at 1366 px and 800 px; numbers unchanged by styling work
- [ ] Deployed link tested end to end by someone outside the team

Data and validation:
- [x] Test 1: sizing vs Tokelau (first build and first upgrade vs the real 2012 system and 2020 upgrade)
- [x] Measured-performance test: model vs measured 2013 solar fractions (run_tokelau.py section 8)
- [x] Tokelau technical review (IT Power 2013) read and cited by page
- [ ] Test 2: 15-year decline of the real system (script sections 3 and 5), reported across fade 0.03-0.08. Output exists; write down the pass criteria before comparing, with the placeholder-fade caveat.
- [ ] Test 3: REopt cross-check (first to cut if time runs short; keep the API key out of the repo)
- [ ] Source every reference number in `SOURCES.md`
- [ ] Pre-run demo sites online so NASA weather is cached in `data/cache/`
