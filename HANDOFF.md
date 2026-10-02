# Handoff: using the energy model

Energy model owner: William. Setup is in the [README](README.md). All assumptions are in
`sunsafe/config.py`; anything marked TODO is a placeholder.

## Lifecycle / finance

Call `simulate()` once per year with that year's faded battery and grown demand.

```python
simulate(pv_kw, battery_kwh, load_kw, pv_per_kw, chemistry="lithium", start_soc=1.0) -> SimResult
```

| Argument | Unit | Notes |
|---|---|---|
| `pv_kw` | kWp | installed PV |
| `battery_kwh` | kWh | **nominal** capacity that year; pass the faded value. Usable = (1 - min_soc) x this |
| `load_kw` | kW, `np.ndarray` (8760,) | hourly demand that year (grow it yourself) |
| `pv_per_kw` | kW per kWp, `np.ndarray` (8760,) | from `pv_output_per_kw(fetch_weather(lat, lon))` |
| `chemistry` | | `"lithium"` or `"lead_acid"` (underscore, as in `interface.py`) |
| `start_soc` | 0-1 | charge at hour 0 |

`SimResult` fields. Hourly arrays are 8760 values in kW (equal to kWh per hour):
`pv_avail`, `pv_used`, `charge`, `discharge`, `soc` (0-1, end of hour), `gen`, `curtailed`.
Annual totals: `load_kwh`, `pv_kwh`, `gen_kwh`, `curtailed_kwh` (kWh/yr),
`renewable_share` (0-1, = 1 - gen/load), `diesel_litres` (L/yr). Echoed inputs: `pv_kw`,
`battery_kwh`, `chemistry`. One call takes ~2 ms.

```python
from sunsafe.energy.solar import fetch_weather, pv_output_per_kw
from sunsafe.energy.simulate import simulate
from sunsafe.energy.sizing import size_system
from sunsafe.energy.diesel import diesel_cost
from sunsafe.load_profiles import village_profile

pv_per_kw = pv_output_per_kw(fetch_weather(-9.38, -171.24))   # Fakaofo, cached after first run
load = village_profile(600)                                     # kW, 600 kWh/day
opt = size_system(load, pv_per_kw, 0.95, "lead_acid", diesel_price=1.10)

for year in range(1, 16):
    battery_y = opt.battery_kwh * 0.94 ** (year - 1)            # your fade model here
    load_y = load * 1.03 ** (year - 1)                          # your growth model here
    r = simulate(opt.pv_kw, battery_y, load_y, pv_per_kw, "lead_acid")
    print(year, f"{r.renewable_share:.1%}", round(diesel_cost(r.diesel_litres, 1.10)))
```

Also useful:
- `size_system(..., design_year=N)` sizes so the target is met in year N with no
  replacement.
- `capex_usd()` and `capital_recovery_factor()` are in `sizing.py`.
- `backup_hours(battery_kwh, chemistry, critical_load_kw)` is in `backup.py`.

**`sunsafe/lifecycle_placeholder.py` is yours to replace.** It is a temporary compounding
fade and growth model, using `BATTERY_ANNUAL_FADE` and `DEMAND_GROWTH_PER_YEAR` from
config. `size_system` and `scripts/run_tokelau.py` import it. When your version lands,
point those imports at it and delete the placeholder.

**The recommended system should be the lowest 15-year-cost design that stays on target
every year.** This is not the design-year-1 result. That result is cheapest on day one but
drops from 95% to ~58% renewable by year 15 (see `run_tokelau.py`, section 3). Compare at
least:
- **Build big:** size for year 15 (`design_year=15`), no battery replacement.
- **Build moderate + planned replacement:** size for year N and replace the battery every
  N years.

For each, sum 15 years of capex, replacements and diesel (discounted) and check
`renewable_share >= target` in every year. This is not implemented yet.

## App

Use the real model:

```python
from sunsafe.model import run_sunsafe          # instead of sunsafe_interface.run_sunsafe
results = run_sunsafe(inputs)                   # same Inputs -> Results contract
```

- **Real:** `results.sizing` (pv_kw, battery_kwh, capex_usd, renewable_share_year1,
  diesel_litres_avoided_year1) and `results.backup_hours`.
- **Still fake:** `lifecycle`, `finance`, `fuel_shock` and `headroom`. They come from
  `run_sunsafe_fake`.
- **`results.warnings` says which parts are fake and what is assumed.** Show it in the UI:
  - placeholder costs
  - load estimated from diesel use
  - synthetic weather, if NASA POWER was down
  - target not reachable
- A call takes ~1 s. The first call for a new location also downloads its weather, which
  takes a few seconds, so consider `st.cache_data`.

## Data / validation

**Load profiles.** Format: `np.ndarray` of shape `(8760,)`, hourly demand in **kW**, hour 0
= 1 January 00:00 local time, no 29 February. The placeholder is
`village_profile(daily_kwh)` in `sunsafe/load_profiles.py`, a fixed 24-hour shape with an
evening peak. To plug in a better one:
- Add a function in `load_profiles.py` that returns the same format.
- Swap it in where `village_profile` is called: `sunsafe/model.py` (`run_sunsafe`) and
  `scripts/run_tokelau.py`.
- Anything passed to `simulate()` or `size_system()` as `load_kw` works directly.

**Rerun the validation:**

```bash
python scripts/run_tokelau.py
```

It works from any directory and takes ~15 s. It prints three sections:
1. Year-1 cost-optimal sizing vs the real 2012 install (265-365 kWp, 1.1-1.6 MWh, or
   ~2.7 MWh from the other source).
2. Target (0.95 / 0.99 / 1.0) x design year (1 / 8 / 15) table.
3. 15-year forward run of the year-1 optimum vs the real 300 kWp / 1,350 kWh system.

Inputs (site, loads, chemistry, diesel price) are constants at the top of the script.
Don't tune `config.py` to hit the Tokelau numbers: report the gap and source the
assumptions instead (every `TODO` in `config.py`).
