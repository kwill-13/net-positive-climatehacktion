# Handoff: using the model

William owns the energy model (`sunsafe/energy/`) and the lifecycle/finance model
(`sunsafe/lifecycle/`). Setup is in the [README](README.md). All assumptions are in
`sunsafe/config.py`; anything marked TODO is a placeholder.

The model freeze was lifted on 3 Oct 2026; git tag `model-freeze-2026-10-03` marks the
frozen state. It was unfrozen again on 3-4 Oct for the rolling plan and growth schedule
(branch `rolling-plan`; see "Rolling plan" below), and is re-frozen after that. Changes to defaults or model logic still go through William, with a sourced
reason. The fake model (`run_sunsafe_fake`) has been removed: `sunsafe/interface.py` now
holds only the `Inputs`/`Results` definitions.

## App

**Status:** the app uses the real model (`run_sunsafe_detailed` in `app/components/layout.py`, one
cached call per plan). If the import or a run fails, the app shows the error in the sidebar and on
Your island, and shows no results. There is no fallback to made-up numbers.

**Pages (rebuilt 4 Oct 2026 as a planning flow):** 1 Your island, 2 Your plan, 3 How we know it works.
`layout.run_plan()` returns a bundle: `results`, best NPV per strategy family (A-D), per-year plan data,
and cost per kWh vs diesel price (diesel only, full hybrid, island-paid "if donors fund the first build")
with both breakevens. Exports take `(results, plan)`.

**Every `Results` field is real.**

- **`sizing`:** the recommended design's **first build**. This is the lowest 15-year-cost plan
  that meets `renewable_target` in **every** year; it is not the cheapest design for year 1
  only. If the plan is a staged expansion, the upgrade (year, added kWp, new battery kWh) is in
  the `Recommended:` warning, which the app shows as a card.
- **`lifecycle`:** one row per year.
  - `share_funded_year_15`: the plan as funded, with its battery replacement or staged upgrade.
  - `share_funded_day_one`: the first build only, never replaced or upgraded.
  - `battery_capacity_kwh`: **usable** capacity with no replacement, as the
    `interface.py` comment says.
- **`finance`:**
  - `om_fund_per_year_usd`: O&M plus savings towards the battery replacement or upgrade.
  - The two levelised costs per kWh: hybrid and diesel-only.
  - `payback_years`: can be `inf` if diesel savings never cover O&M.
- **`fuel_shock`:** **8 months**, 2026-03 to 2026-10. Each month gives the cost of
  diesel-only vs hybrid, following Apia's 2026 retail price changes applied to the site's
  price.
- **`headroom`:** monthly surplus solar, new loads that fit the leanest month, and
  electricity's share of the community's energy use.
- **`warnings`:** the recommended strategy plus every placeholder still in use. Show them.
- **`plan_stages`** (new, optional, added 4 Oct 2026): every investment in the recommended plan,
  in year order, as `PlanStage(year, pv_added_kw, battery_installed_kwh, capex_usd)`. The first
  entry is the initial build (= `sizing`). Later entries are battery replacements (B), the
  staged upgrade (C) or each rolling-plan stage (D). It defaults to `[]`, so old callers work
  unchanged. Use it to show a multi-upgrade timeline, because D can have 2-4 upgrades.

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
- **At the sourced default USD 1.87/L and 9% growth:** the recommended rolling plan costs
  $0.84/kWh vs $0.66/kWh for diesel-only, with a 10.9-yr simple payback on the first build.
- **Breakeven:** USD 2.42/L (8%) or 2.25/L (6%).
- **Staged investment:** build smaller, then add PV and a new battery in years 7 and 13 (Tokelau
  built in 2012 and upgraded in 2020). It is 27% cheaper over 15 years than building big for year 15.
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
USD 1.87/L, constant 9%/yr growth, 15 years, all four strategies (from `python scripts/run_tokelau.py`;
page 3 of the app shows the same table):
- **Recommended:** D, rolling plan with 6-yr stages. Build 305 kWp / 1,277 kWh (638 usable); year 7
  add 219 kWp and a new 2,141 kWh battery; year 13 add 139 kWp and a new 2,664 kWh battery.
- **Cost:** capex ~$1.21M; $0.84/kWh hybrid vs $0.66/kWh diesel-only; simple payback 10.9 yrs on
  the first build; breakeven diesel price $2.42/L (8%) or $2.25/L (6%).
- **Strategy:** NPV $2.74M, vs $3.76M for building big (27% cheaper); best C $2.80M, best B $3.46M.
- **Validation:**
  - First build against Fakaofo's real system (IRENA 2013: 330 kWp / 3,379 kWh nominal, 1,690
    usable): PV 0.93x, battery 0.38x.
  - The year-7 upgrade (+219 kWp, new 2,141 kWh) is about the size of Tokelau's 2020 upgrade
    (+210 kWp, ~2 MWh Li-ion: PV 1.04x, battery 1.07x), but comes ~2 years earlier (after 6 years
    vs ~8).
  - The real system, modelled with 9% growth, drops below 95% in year 9. It was actually
    upgraded after ~8 yrs.
  - 2013 solar fraction: model 95-97% vs 92.5-93.5% measured.
  - Sources are in `SOURCES.md`.

## Rolling plan and growth schedule (added 4 Oct 2026)

- **Strategy D, rolling plan:** stage length K in `config.ROLLING_STAGE_YEARS` = (6, 8, 10).
  - Stage 1 (PV + battery) is sized to meet the target every year through year K.
  - At the start of each later stage, the existing PV is kept (degraded), PV is added, and a new
    battery is sized to meet the target to the end of that stage.
  - The last stage may be shorter. If it is under half a stage, a variant that merges it into
    the previous stage is also tried, so no battery is bought for a 1-year stub.
  - Each stage's capex is paid in its year: added PV at today's price, the battery at the
    declined price.
- **Recommendation:** the lowest NPV across A, B, C and D among plans that meet the target every year.
- **Growth schedule:** `degradation.GrowthSchedule(fast_rate, fast_years, steady_rate)`.
  - Any `growth` argument in the model accepts this or a constant rate.
  - A constant float uses exactly the old formula. A schedule with `fast_years=0` equals constant
    `steady_rate`, and a test checks this.
  - `Inputs` still carries only a constant `demand_growth_per_year`. Scripts pass a schedule with
    `run_sunsafe_detailed(inputs, growth=GrowthSchedule(0.09, 5, 0.03))`.
- **Everything runs A-D:** the app, `scripts/run_tokelau.py` and page 3's validation table. With
  constant 9%/yr growth the Fakaofo validation case recommends **D, 6-yr stages** (upgrades in years
  7 and 13), NPV $2.74M. With the app's default growth (9% for 5 years, then 3%) the Fakaofo preset
  recommends C, one upgrade in year 9.
- **Site presets:** `config.SITE_PRESETS` is one list of sites for scripts and the app. It holds the
  three Tokelau atolls (validation settings) and 5 **illustrative** Pacific sites:
  - Abaiang, Kiribati; Lifuka, Tonga; Tanna, Vanuatu; Aitutaki, Cook Islands; Jaluit, Marshall Islands.
  - These have real coordinates, but their diesel use (200-600 L/day) and price are made up.
  - The app's Site Setup page still has its own Tokelau `PRESETS` dict and could read this list instead.
- **`python scripts/run_pacific_presets.py`** prints the recommended strategy, stages, NPV, number of
  upgrades and runtime at 15/20/25 years with growth 9% for 5 yrs then 3%.
- **Runtime:** ~9 s for 15 years and ~13 s for 25 years per site. The sizing grid uses a
  summary-only dispatch (`simulate.annual_gen_kwh`), which gives identical numbers to `simulate`,
  and sizing results are shared across A-D.

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

It works from any directory and takes ~45 s. It prints five sections:
1. Year-1 cost-optimal sizing vs the real 2012 install.
2. Target x design-year table.
3. 15-year decline of the year-1 optimum vs the real 330 kWp / 3,379 kWh system.
4. Strategies A (build big), B (same-size battery replacement), C (staged expansion) and D (rolling
   plan); the recommended plan vs Fakaofo's real 2012 system and 2020 upgrade; its lifecycle curves.
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
          replace_battery_in=None, growth=0.03, fade=None,
          upgrade_in=None, upgrade_pv_kw=None, upgrade_battery_kwh=None,
          stages=None) -> list[YearResult]       # stages: [(year, total pv_kw, new battery_kwh)]
size_system(load_kw, pv_per_kw, renewable_target, chemistry, diesel_price,
            design_year=1, demand_growth=0.03, battery_year=None) -> SizingOption
compare_strategies(load_kw, pv_per_kw, target, chemistry, diesel_price,
                   project_years=15, growth=0.03,
                   rolling_stage_years=(6, 8, 10)) -> StrategyComparison
# growth: a constant rate or degradation.GrowthSchedule, everywhere
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
  - Generator O&M (USD 0.04/kWh) is included; generator capex and battery salvage value are not.
