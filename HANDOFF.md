# Handoff: using the model

William owns the energy model (`sunsafe/energy/`) and the lifecycle/finance model
(`sunsafe/lifecycle/`). Setup is in the [README](README.md). All assumptions are in
`sunsafe/config.py`; anything marked TODO is a placeholder.

## App

```python
from sunsafe.model import run_sunsafe          # instead of sunsafe_interface.run_sunsafe
results = run_sunsafe(inputs)                   # same Inputs -> Results contract
```

**Every `Results` field is now real.** Nothing comes from `run_sunsafe_fake`.

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
- **`fuel_shock`:** Jan-Jun 2026 monthly costs, diesel-only vs hybrid, under a placeholder
  +35% price jump from April.
- **`headroom`:** monthly surplus solar, new loads that fit the leanest month, and
  electricity's share of the community's energy use.
- **`warnings`:** the recommended strategy plus every placeholder still in use. Show them.

**Speed:** a call takes **~12 s**, because it compares about 9 strategies. Wrap it in
`st.cache_data`. The first call for a new location also downloads its weather.

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

It works from any directory and takes ~40 s. It prints five sections:
1. Year-1 cost-optimal sizing vs the real 2012 install.
2. Target x design-year table.
3. 15-year decline of the year-1 optimum vs the real 300 kWp / 1,350 kWh system.
4. Strategy A (build big) vs B (moderate + planned replacement), with the recommended
   system's lifecycle curves.
5. The decline in section 3 at battery fade rates 0.04 / 0.06 / 0.08.

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
  demand growth all compound yearly. The rates are placeholders in config.
- **Strategy B sizing:** the battery is replaced at the start of year N+1. The design takes
  the larger PV and the larger battery of the two hardest years (year N and the final
  year). That is always feasible but can be slightly oversized.
- **Finance:**
  - Discount rate 8% real.
  - Capex at t = 0; O&M and diesel at the end of each year; replacement at the start of its
    year, at a price falling 4%/yr.
  - Not included: generator capex and O&M, and battery salvage value.
