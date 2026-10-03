"""
Choose PV and battery size for a site.

Grid search over PV kW and battery kWh. Keep options whose year-1 renewable share
meets the target, then pick the one with the lowest annualised cost:

    annual cost = PV capex x CRF(discount, PV life)
                + battery capex x CRF(discount, battery life)
                + generator fuel + generator O&M

A coarse grid is searched first, then a finer grid around the best coarse point.
Costs and lifetimes are in config.py (placeholders until sourced).
"""

from dataclasses import dataclass, replace
from typing import Optional

import numpy as np

from sunsafe import config
from sunsafe.energy.diesel import generator_cost_usd, litres_from_kwh
from sunsafe.energy.simulate import SimResult, annual_gen_kwh, battery_params, simulate
from sunsafe.lifecycle.degradation import capacity_factor, demand, pv_derate


@dataclass
class SizingOption:
    pv_kw: float                 # kWp
    battery_kwh: float           # kWh nominal, as installed (new)
    capex_usd: float             # USD, PV + battery installed (no generator, no BOS extras)
    annualised_cost_usd: float   # USD/yr, annualised capex + generator fuel and O&M
    renewable_share: float       # 0-1, in the design year
    diesel_litres: float         # litres/yr, in the design year
    meets_target: bool           # False only if nothing in the search range met the target
    sim: Optional[SimResult] = None  # full design-year simulation (set on the returned option only)
    design_year: int = 1         # year whose faded battery + grown load the option was sized for


def capital_recovery_factor(rate: float, years: float) -> float:
    """
    Fraction of capital cost paid each year to repay it over `years` at `rate`.

    Args:
        rate: discount rate per year, 0-1 (0.08 = 8%).
        years: lifetime, years.

    Returns:
        CRF, 1/yr.
    """
    if rate == 0:
        return 1.0 / years
    g = (1 + rate) ** years
    return rate * g / (g - 1)


def capex_usd(pv_kw: float, battery_kwh: float, chemistry: str) -> float:
    """
    Installed capital cost of PV + battery.

    Args:
        pv_kw: kWp. battery_kwh: kWh nominal. chemistry: "lithium" or "lead_acid".

    Returns:
        USD.
    """
    return (pv_kw * config.PV_COST_USD_PER_KW
            + battery_kwh * config.BATTERY_COST_USD_PER_KWH[chemistry])


def _evaluate(pv_kw, battery_kwh, load_kw, pv_per_kw, chemistry, diesel_price, target,
              cap_factor):
    # Costs use the installed (nominal) battery; performance uses the faded capacity.
    # annual_gen_kwh = simulate(...).gen_kwh without the hourly arrays (grid search speed).
    gen_kwh = annual_gen_kwh(pv_kw, battery_kwh * cap_factor, load_kw, pv_per_kw, chemistry)
    load_kwh = float(load_kw.sum())
    share = 1.0 - gen_kwh / load_kwh if load_kwh > 0 else 1.0
    life = battery_params(chemistry)["life_years"]
    annual = (pv_kw * config.PV_COST_USD_PER_KW
              * capital_recovery_factor(config.DISCOUNT_RATE, config.PV_LIFE_YEARS)
              + battery_kwh * config.BATTERY_COST_USD_PER_KWH[chemistry]
              * capital_recovery_factor(config.DISCOUNT_RATE, life)
              + generator_cost_usd(gen_kwh, diesel_price))
    return SizingOption(
        pv_kw=float(pv_kw), battery_kwh=float(battery_kwh),
        capex_usd=capex_usd(pv_kw, battery_kwh, chemistry),
        annualised_cost_usd=float(annual),
        renewable_share=share,
        diesel_litres=litres_from_kwh(gen_kwh),
        meets_target=share >= target - 1e-9,
    )


def _search(pv_grid, batt_grid, args) -> list:
    return [_evaluate(pv, b, *args) for pv in pv_grid for b in batt_grid]


def _best(options: list) -> Optional[SizingOption]:
    feasible = [o for o in options if o.meets_target]
    return min(feasible, key=lambda o: o.annualised_cost_usd) if feasible else None


def size_system(load_kw: np.ndarray, pv_per_kw: np.ndarray, renewable_target: float,
                chemistry: str, diesel_price: float, design_year: int = 1,
                demand_growth: float = config.DEMAND_GROWTH_PER_YEAR,
                battery_year: Optional[int] = None) -> SizingOption:
    """
    Lowest annualised-cost PV + battery that meets the renewable target in the design year.

    design_year = 1 sizes for a new battery and today's load. design_year = N sizes so the
    target is still met in year N: load is grown by (1 + demand_growth)^(N-1), PV output is
    derated by (1 - PV_ANNUAL_DERATE)^(N-1), and battery performance uses
    nominal x (1 - annual_fade)^(battery_year-1) (sunsafe/lifecycle/degradation.py).
    battery_year defaults to design_year (no replacement); pass a smaller value when the
    battery has been replaced, e.g. replaced at the start of year 9 -> in year 15 it is
    in its 7th year. The objective uses diesel
    in the design year and capex of the installed (nominal) battery.

    Search range (config.SIZING_*): PV 0.5x-15x average design-year load (kW); battery 0-3
    days of design-year daily load (kWh), divided by the capacity factor so the range of
    *effective* capacity searched is the same in every design year.

    Args:
        load_kw: hourly demand, kW, shape (8760,).
        pv_per_kw: hourly PV output per kWp, kW/kWp, shape (8760,).
        renewable_target: required renewable share, 0-1.
        chemistry: "lithium" or "lead_acid".
        diesel_price: delivered diesel price, USD/litre.
        design_year: year of operation to size for, >= 1.
        demand_growth: demand growth per year, 0-1 (only used when design_year > 1).
        battery_year: year of the battery's life in the design year, 1 = new.

    Returns:
        SizingOption (battery_kwh is nominal as installed). If no option in the range meets the target, returns the option with
        the highest renewable share and meets_target=False (callers should warn).
    """
    cap_factor = capacity_factor(chemistry, battery_year or design_year)
    load_kw = demand(design_year, load_kw, demand_growth)
    pv_per_kw = np.asarray(pv_per_kw, dtype=float) * pv_derate(design_year)
    avg_kw = load_kw.mean()
    daily_kwh = load_kw.sum() / (len(load_kw) / 24)
    pv_lo = config.SIZING_PV_MIN_X_AVG_LOAD * avg_kw
    pv_hi = config.SIZING_PV_MAX_X_AVG_LOAD * avg_kw
    b_hi = config.SIZING_BATTERY_MAX_DAYS * daily_kwh / cap_factor
    args = (load_kw, pv_per_kw, chemistry, diesel_price, renewable_target, cap_factor)

    pv_grid = np.linspace(pv_lo, pv_hi, config.SIZING_COARSE_STEPS_PV)
    b_grid = np.linspace(0.0, b_hi, config.SIZING_COARSE_STEPS_BATTERY)
    coarse = _search(pv_grid, b_grid, args)
    best = _best(coarse)
    if best is None:
        best = max(coarse, key=lambda o: (o.renewable_share, -o.annualised_cost_usd))
        return _with_sim(best, load_kw, pv_per_kw, chemistry, cap_factor, design_year)

    # Refine: finer grid spanning one coarse step either side of the coarse optimum.
    dpv, db = pv_grid[1] - pv_grid[0], b_grid[1] - b_grid[0]
    n = config.SIZING_REFINE_STEPS
    pv_fine = np.linspace(max(pv_lo, best.pv_kw - dpv), min(pv_hi, best.pv_kw + dpv), n)
    b_fine = np.linspace(max(0.0, best.battery_kwh - db), min(b_hi, best.battery_kwh + db), n)
    best = _best(_search(pv_fine, b_fine, args) + [best])
    return _with_sim(best, load_kw, pv_per_kw, chemistry, cap_factor, design_year)


def _with_sim(option, load_kw, pv_per_kw, chemistry, cap_factor, design_year) -> SizingOption:
    # Grid options keep only summaries (memory); re-run the chosen one for its hourly arrays.
    sim = simulate(option.pv_kw, option.battery_kwh * cap_factor, load_kw, pv_per_kw, chemistry)
    return replace(option, sim=sim, design_year=design_year)
