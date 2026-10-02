"""
Choose PV and battery size for a site.

Grid search over PV kW and battery kWh. Keep options whose year-1 renewable share
meets the target, then pick the one with the lowest annualised cost:

    annual cost = PV capex x CRF(discount, PV life)
                + battery capex x CRF(discount, battery life)
                + diesel litres x diesel price

A coarse grid is searched first, then a finer grid around the best coarse point.
Costs and lifetimes are in config.py (placeholders until sourced).
"""

from dataclasses import dataclass, replace
from typing import Optional

import numpy as np

from sunsafe import config
from sunsafe.energy.diesel import diesel_cost
from sunsafe.energy.simulate import SimResult, battery_params, simulate


@dataclass
class SizingOption:
    pv_kw: float                 # kWp
    battery_kwh: float           # kWh nominal
    capex_usd: float             # USD, PV + battery installed (no generator, no BOS extras)
    annualised_cost_usd: float   # USD/yr, annualised capex + diesel
    renewable_share: float       # 0-1, year 1
    diesel_litres: float         # litres/yr, year 1
    meets_target: bool           # False only if nothing in the search range met the target
    sim: Optional[SimResult] = None  # full year-1 simulation (set on the returned option only)


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


def _evaluate(pv_kw, battery_kwh, load_kw, pv_per_kw, chemistry, diesel_price, target):
    sim = simulate(pv_kw, battery_kwh, load_kw, pv_per_kw, chemistry)
    life = battery_params(chemistry)["life_years"]
    annual = (pv_kw * config.PV_COST_USD_PER_KW
              * capital_recovery_factor(config.DISCOUNT_RATE, config.PV_LIFE_YEARS)
              + battery_kwh * config.BATTERY_COST_USD_PER_KWH[chemistry]
              * capital_recovery_factor(config.DISCOUNT_RATE, life)
              + diesel_cost(sim.diesel_litres, diesel_price))
    return SizingOption(
        pv_kw=float(pv_kw), battery_kwh=float(battery_kwh),
        capex_usd=capex_usd(pv_kw, battery_kwh, chemistry),
        annualised_cost_usd=float(annual),
        renewable_share=sim.renewable_share,
        diesel_litres=sim.diesel_litres,
        meets_target=sim.renewable_share >= target - 1e-9,
    )


def _search(pv_grid, batt_grid, args) -> list:
    return [_evaluate(pv, b, *args) for pv in pv_grid for b in batt_grid]


def _best(options: list) -> Optional[SizingOption]:
    feasible = [o for o in options if o.meets_target]
    return min(feasible, key=lambda o: o.annualised_cost_usd) if feasible else None


def size_system(load_kw: np.ndarray, pv_per_kw: np.ndarray, renewable_target: float,
                chemistry: str, diesel_price: float) -> SizingOption:
    """
    Lowest annualised-cost PV + battery that meets the renewable target in year 1.

    Search range (config.SIZING_*): PV 0.5x-15x average load (kW); battery 0-3 days of daily load (kWh).

    Args:
        load_kw: hourly demand, kW, shape (8760,).
        pv_per_kw: hourly PV output per kWp, kW/kWp, shape (8760,).
        renewable_target: required renewable share, 0-1.
        chemistry: "lithium" or "lead_acid".
        diesel_price: delivered diesel price, USD/litre.

    Returns:
        SizingOption. If no option in the range meets the target, returns the option with
        the highest renewable share and meets_target=False (callers should warn).
    """
    load_kw = np.asarray(load_kw, dtype=float)
    avg_kw = load_kw.mean()
    daily_kwh = load_kw.sum() / (len(load_kw) / 24)
    pv_lo = config.SIZING_PV_MIN_X_AVG_LOAD * avg_kw
    pv_hi = config.SIZING_PV_MAX_X_AVG_LOAD * avg_kw
    b_hi = config.SIZING_BATTERY_MAX_DAYS * daily_kwh
    args = (load_kw, pv_per_kw, chemistry, diesel_price, renewable_target)

    pv_grid = np.linspace(pv_lo, pv_hi, config.SIZING_COARSE_STEPS_PV)
    b_grid = np.linspace(0.0, b_hi, config.SIZING_COARSE_STEPS_BATTERY)
    coarse = _search(pv_grid, b_grid, args)
    best = _best(coarse)
    if best is None:
        best = max(coarse, key=lambda o: (o.renewable_share, -o.annualised_cost_usd))
        return _with_sim(best, load_kw, pv_per_kw, chemistry)

    # Refine: finer grid spanning one coarse step either side of the coarse optimum.
    dpv, db = pv_grid[1] - pv_grid[0], b_grid[1] - b_grid[0]
    n = config.SIZING_REFINE_STEPS
    pv_fine = np.linspace(max(pv_lo, best.pv_kw - dpv), min(pv_hi, best.pv_kw + dpv), n)
    b_fine = np.linspace(max(0.0, best.battery_kwh - db), min(b_hi, best.battery_kwh + db), n)
    best = _best(_search(pv_fine, b_fine, args) + [best])
    return _with_sim(best, load_kw, pv_per_kw, chemistry)


def _with_sim(option, load_kw, pv_per_kw, chemistry) -> SizingOption:
    # Grid options keep only summaries (memory); re-run the chosen one for its hourly arrays.
    return replace(option, sim=simulate(option.pv_kw, option.battery_kwh, load_kw,
                                        pv_per_kw, chemistry))
