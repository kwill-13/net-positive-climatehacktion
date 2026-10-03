# Handoff: using the model

William owns the energy model (`sunsafe/energy/`) and the lifecycle/finance model
(`sunsafe/lifecycle/`). Setup is in the [README](README.md). All assumptions are in
`sunsafe/config.py`; anything marked TODO is a placeholder.

The model freeze was lifted on 3 Oct 2026; git tag `model-freeze-2026-10-03` marks the
frozen state. Changes to defaults or model logic still go through William, with a sourced
reason. The fake model (`run_sunsafe_fake`) has been removed: `sunsafe/interface.py` now
holds only the `Inputs`/`Results` definitions.

## App

**Status:** the app uses the real model (`from sunsafe.model import run_sunsafe` in
`app/components/layout.py`). If the import or a run fails, the app shows the error in the
sidebar and on Site Setup, and shows no results. There is no fallback to made-up numbers.

**Every `Results` field is real.**

- **`sizing`:** the recommended design. This is the lowest 15-year-cost design that meets
  `renewable_target` in **every** year. It is not the cheapest design for year 1 only.
- **`lifecycle`:** one row per year.
  - `share_funded_year_15`: the same system with its planned battery replacement.
  - `share_funded_day_one`: the same system never replaced.
  - `battery_capacity_kwh`: **usable** capacity with no replacement, as the
    `interface.py` comment says.
- **`finance`:**
  - `om_fund_per_year_usd`: O&M plus savings towards the battery replacement.
  - The two levelised costs per kWh: hybrid and diesel-only.
  - `payback_years`: can be `inf` if diesel savings never cover O&M.
- **`fuel_shock`:** **8 months**, 2026-03 to 2026-10. Each month gives the cost of
  diesel-only vs hybrid, following Apia's 2026 retail price changes applied to the site's
  price.
- **`headroom`:** monthly surplus solar, new loads that fit the leanest month, and
  electricity's share of the community's energy use.
- **`warnings`:** the recommended strategy plus every placeholder still in use. Show them.

**Assumptions.** All are in `sunsafe/config.py`, which starts with a sources block. Each
value is commented with its source, or with TODO if it is still a placeholder.

Still placeholders (TODO):
- **Load:** generic 24-hour profile shape.
- **Capital costs:** PV $2,500/kWp (evidence suggests up to ~$4,000/kWp for remote atolls; see `SOURCES.md` P2).
- **Ageing:** lithium battery fade 2.5%/yr.
- **Headroom:**
  - Candidate loads: school cooking 12 and outboard charging 15 kWh/day. The freezer, 25 kWh/day,
    is sourced.
  - Non-electric energy: 3x electric load, with Fakaofo set at 1,800 kWh/day.
- **Not counted:** generator capex and battery salvage value.
- **Weather:** if NASA POWER is unreachable, a synthetic tropical year is used and a
  warning says so.

Now sourced:
- **Diesel:**
  - Tokelau delivered price USD 1.87/L (Apia 2026 average x1.25 freight, ITP 2013); scenarios:
    low 1.22, high 2.70.
  - Generator efficiency 3.0 kWh/L.
  - Generator O&M USD 0.04/kWh, applied to both diesel-only and hybrid generator output.
- **Fuel shock:** Apia monthly retail diesel, Mar-Oct 2026, as changes relative to March,
  applied to the site's own price. It peaks at x1.78 in June. `fuel_shock` now has
  **8 months** (2026-03 to 2026-10).
- **Lithium:** battery $600/kWh; life 12 yrs.
- **Lead-acid:** life 8 yrs; capex $350/kWh (ITP 2013 replacement estimate); fade 3%/yr.
- **Demand growth:** 9%/yr (Tokelau 2008-13 measured; ITP 2019). This is the app default; the
  interface's own default stays 0.03.
- **PV capex:** sourced range USD 2,500-4,000/kW; the default is the low end.
- **Ageing:** PV derate 0.5%/yr; battery price decline 4%/yr.
- **O&M:** PV $70/kW/yr; battery $10/kWh/yr.
- **Discount rate:** 8%, with 6% as a sensitivity case.

**Diesel price drives the result.**
- **At the sourced default USD 1.87/L and 9% growth:** holding 95% every year needs 663 kWp /
  2,664 kWh at Fakaofo. That costs $1.07/kWh vs $0.66/kWh for diesel-only (payback ~36 yrs).
- **Breakeven:** USD 3.09/L (8%) or 2.74/L (6%).
- **Why it is expensive:** demand triples over 15 years. Tokelau instead upgraded in stages (2012
  build, 2020 upgrade), and SunSafe does not yet model staged expansion.
- **For the pitch:** this is a price-risk case (see the fuel shock), not a guaranteed saving.

**Demo checklist.** These are app-side changes. Items were checked
by running the real app headless (Streamlit AppTest) with the Fakaofo preset, the plain
defaults, and an edge case (100% target, 5-year horizon). No page raised an error, and the
numbers on screen match the model.

Done:
- [x] Default diesel price comes from config (USD 1.87, sourced), plus a Tokelau preset.
- [x] Results cached with `st.cache_data`.
- [x] `payback_years = inf` shows as "Never (savings don't cover O&M)".
- [x] Streamlit version: `requirements.txt` now says `streamlit>=1.39`. Site Setup
  (`st.map(height=...)`) and Lifecycle (`line_chart(x_label=...)`) crash on 1.35-1.38.

Re-checked after commit `eacc610`, on Streamlit 1.65 and 1.39, in 4 scenarios including
"inputs edited without re-running". No page raised an error.
- [x] Recommended strategy shown as a card on System Design and Lifecycle, and in the proposal.
- [x] Out-of-date banner text fixed.
- [x] Validation table on System Design compares each atoll's real IRENA sizes, nominal vs nominal and
  usable vs usable, for each atoll.
- [x] Model errors shown in the sidebar with the reason.
- [x] Sidebar shows "Results for: <site>", and pages warn when inputs changed since the run.
- [x] Final-year share card, plus a caption explaining the ~100% year-1 share.
- [x] Caption when both lifecycle lines are identical (build big).
- [x] Horizon used in place of "year 15"; warning when payback exceeds the horizon.
- [x] `app/README.md` updated.

Optional:
- [x] **Validation table scope:** now shown for all three Tokelau atolls, because Source A's
  range covers all three systems. It warns when inputs differ from the validation case
  (lead-acid, 95%, ~600 kWh/day). Any other site shows "not validated against a real system".

Housekeeping:
- [ ] **Offline demo:** run each demo site once beforehand, so its NASA weather is cached
  in `data/cache/`.
- [ ] **Git uploads:** browser uploads to GitHub ignore `.gitignore`. Commit `081da0b`
  and `d06797a` re-added `app/**/__pycache__/*.pyc`; they were removed again each time. Upload source files
  only, or use `git` from the command line.

**Reference numbers** for the Fakaofo demo: 600 kWh/day, lead-acid, 95% target,
USD 1.87/L, 9%/yr growth (from `python scripts/run_tokelau.py`):
- **Recommended:** 663 kWp / 2,664 kWh, with a new battery in year 13.
- **Cost:** capex ~$2.59M; $1.07/kWh hybrid vs $0.66/kWh diesel-only; payback ~36 yrs;
  breakeven diesel price $3.09/L (8%) or $2.74/L (6%).
- **Strategy:** about 8% cheaper over 15 years than building big ($3.46M vs $3.76M NPV).
- **Validation:**
  - Against Fakaofo's real system (IRENA 2013: 330 kWp / 3,379 kWh nominal): PV 2.0x, battery
    0.79x.
  - The real system, modelled with 9% growth, drops below 95% in year 9. It was actually
    upgraded after ~8 yrs.
  - 2013 solar fraction: model 95-97% vs 92.5-93.5% measured.
  - Sources are in `SOURCES.md`.

For a strategy comparison screen, `run_sunsafe_detailed(inputs)` returns
`(results, comparison)`:
- `comparison.candidates` is every strategy, with PV, battery, replacement year, NPV,
  minimum share and a feasibility flag.
- `comparison.year1_optimal` is the year-1-only design, for contrast.

## Data / validation

**Load profiles.** Format: `np.ndarray` of shape `(8760,)`, hourly demand in **kW**, hour 0
= 1 January 00:00 local time, no 29 February. The placeholder is
`village_profile(daily_kwh)` in `sunsafe/load_profiles.py`, a fixed 24-hour shape with an
evening peak. To plug in a better one:
- Add a function in `load_profiles.py` that returns the same format.
- Swap it in where `village_profile` is called: `sunsafe/model.py`
  (`run_sunsafe_detailed`) and `scripts/run_tokelau.py`.
- Anything passed to `simulate()`, `size_system()`, `run_years()` or `compare_strategies()`
  as `load_kw` works directly.

**Rerun the validation:**

```bash
python scripts/run_tokelau.py
```

It works from any directory and takes ~60 s. It prints five sections:
1. Year-1 cost-optimal sizing vs the real 2012 install.
2. Target x design-year table.
3. 15-year decline of the year-1 optimum vs the real 300 kWp / 1,350 kWh system.
4. Strategy A (build big) vs B (moderate + planned replacement), with the recommended
   system's lifecycle curves.
5. The real system's decline at battery fade 0.03 / 0.04 / 0.06 / 0.08, and the first year it
   drops below 95% at each.
6. Diesel price x discount rate, including a PV USD 4,000/kW high case.
7. Three-atoll payback, also shown with ITP's solar O&M.
8. Measured-performance test against the 2013 solar fractions.

Inputs are constants at the top of the script. Don't tune `config.py` to hit the Tokelau
numbers: report the gap and source the assumptions instead (every `TODO` in `config.py`).

## Model internals (reference)

```python
simulate(pv_kw, battery_kwh, load_kw, pv_per_kw, chemistry="lithium", start_soc=1.0) -> SimResult
run_years(pv_kw, battery_kwh, load_kw, pv_per_kw, chemistry, years=15,
          replace_battery_in=None, growth=0.03, fade=None) -> list[YearResult]
size_system(load_kw, pv_per_kw, renewable_target, chemistry, diesel_price,
            design_year=1, demand_growth=0.03, battery_year=None) -> SizingOption
compare_strategies(load_kw, pv_per_kw, target, chemistry, diesel_price,
                   project_years=15, growth=0.03) -> StrategyComparison
```

- **Units:**
  - PV in kWp; batteries in kWh **nominal**, where usable = (1 - min_soc) x nominal.
  - Hourly arrays are 8760 values in kW, which equal kWh per hour.
  - Shares are 0-1.
  - Chemistry is `"lithium"` or `"lead_acid"`.
- **`SimResult`:**
  - Hourly arrays: `pv_avail`, `pv_used`, `charge`, `discharge`, `soc`, `gen`, `curtailed`.
  - Annual totals: `load_kwh`, `pv_kwh`, `gen_kwh`, `curtailed_kwh`, `renewable_share`,
    `diesel_litres`.
- **`YearResult`:** `year`, `battery_year`, `battery_kwh`, `demand_kwh_per_day`, `load_kwh`,
  `renewable_share`, `gen_kwh`, `diesel_litres`, `curtailed_kwh`.
- **Degradation** (`sunsafe/lifecycle/degradation.py`): battery fade, PV derate (0.5%/yr) and
  demand growth all compound yearly. The rates are in config; lithium fade is still a placeholder.
- **Strategy B sizing:** the battery is replaced at the start of year N+1. The design takes
  the larger PV and the larger battery of the two hardest years (year N and the final
  year). That is always feasible but can be slightly oversized.
- **Finance:**
  - Discount rate 8% real.
  - Capex at t = 0; O&M and diesel at the end of each year; replacement at the start of its
    year, at a price falling 4%/yr.
  - Not included: generator capex and O&M, and battery salvage value.
