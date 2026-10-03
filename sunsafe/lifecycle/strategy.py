"""
Choose the design that stays on target EVERY year at the lowest project-life cost.

Two strategies, same renewable target, over project_years (P):

A  "Build big": size for year P (faded battery, grown load, derated PV), never replace.
B  "Moderate + planned replacement", for each N in config.STRATEGY_REPLACEMENT_AFTER_YEARS:
   the battery is replaced at the start of year N+1. The two hardest years are year N
   (oldest first battery) and year P (biggest load, second battery P-N years old). Each is
   sized with size_system(); taking the larger PV and the larger battery of the two meets
   both, because renewable share only rises with more PV or more battery.

Every candidate is then checked with run_years() in every year, and the feasible one with
the lowest NPV (capex + O&M + replacement + generator fuel and O&M) is recommended. The year-1
cost-optimal design is kept for reporting only.
"""

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from sunsafe import config
from sunsafe.energy.sizing import SizingOption, capex_usd, size_system
from sunsafe.lifecycle import finance
from sunsafe.lifecycle.projection import YearResult, run_years


@dataclass
class Strategy:
    name: str                        # "A: build big" or "B: replace in year 9", etc.
    pv_kw: float                     # kWp
    battery_kwh: float               # kWh nominal, as installed (and as replaced)
    replacement_year: Optional[int]  # year of operation the battery is replaced in, or None
    capex_usd: float                 # USD up front, PV + battery
    replacement_usd: float           # USD at time of replacement (0 if none)
    annual_om_usd: float             # USD/yr
    npv_usd: float                   # USD, present value of capex + O&M + replacement + diesel
    years: List[YearResult]          # with the planned replacement (if any)
    min_share: float                 # 0-1, lowest renewable share over the project
    meets_target_every_year: bool


@dataclass
class StrategyComparison:
    recommended: Strategy            # lowest NPV among feasible (or best min_share if none)
    candidates: List[Strategy]       # A first, then B for each N
    year1_optimal: SizingOption      # cheapest design meeting the target in year 1 only (report)
    any_feasible: bool               # False if no candidate held the target every year
    target: float = 0.0
    project_years: int = 15
    notes: List[str] = field(default_factory=list)


def evaluate(name: str, pv_kw: float, battery_kwh: float, replacement_year: Optional[int],
             load_kw: np.ndarray, pv_per_kw: np.ndarray, target: float, chemistry: str,
             diesel_price: float, project_years: int, growth: float) -> Strategy:
    """
    Run a design over the project with its planned replacement and cost it.

    Args:
        name: label for reports.
        pv_kw: kWp. battery_kwh: kWh nominal.
        replacement_year: year of operation the battery is replaced in, or None.
        load_kw: year-1 hourly load, kW. pv_per_kw: year-1 PV kW/kWp.
        target: renewable share required every year, 0-1.
        chemistry: "lithium" or "lead_acid". diesel_price: USD/litre.
        project_years: years to evaluate. growth: demand growth per year, 0-1.

    Returns:
        Strategy.
    """
    years = run_years(pv_kw, battery_kwh, load_kw, pv_per_kw, chemistry, project_years,
                      replace_battery_in=[replacement_year] if replacement_year else None,
                      growth=growth)
    capex = capex_usd(pv_kw, battery_kwh, chemistry)
    repl = (finance.replacement_cost_usd(battery_kwh, chemistry, replacement_year)
            if replacement_year else 0.0)
    om = finance.annual_om_usd(pv_kw, battery_kwh)
    npv = finance.lifetime_npv_usd(capex, om, [y.gen_kwh for y in years], diesel_price,
                                   replacement_year, repl)
    min_share = min(y.renewable_share for y in years)
    return Strategy(name=name, pv_kw=pv_kw, battery_kwh=battery_kwh,
                    replacement_year=replacement_year, capex_usd=capex, replacement_usd=repl,
                    annual_om_usd=om, npv_usd=npv, years=years, min_share=min_share,
                    meets_target_every_year=min_share >= target - 1e-9)


def compare_strategies(load_kw: np.ndarray, pv_per_kw: np.ndarray, target: float,
                       chemistry: str, diesel_price: float, project_years: int = 15,
                       growth: float = config.DEMAND_GROWTH_PER_YEAR,
                       replacement_after_years=config.STRATEGY_REPLACEMENT_AFTER_YEARS
                       ) -> StrategyComparison:
    """
    Compare "build big" with "moderate + planned replacement" and recommend one.

    Args:
        load_kw: year-1 hourly load, kW (8760). pv_per_kw: year-1 PV kW/kWp (8760).
        target: renewable share required in EVERY year, 0-1.
        chemistry: "lithium" or "lead_acid". diesel_price: USD/litre.
        project_years: project length, years.
        growth: demand growth per year, 0-1.
        replacement_after_years: values of N to try for strategy B (replace in year N+1).

    Returns:
        StrategyComparison; `recommended` is the lowest-NPV design that meets the target every
        year. If none does, it is the one with the highest minimum share and any_feasible=False.
    """
    common = dict(load_kw=load_kw, pv_per_kw=pv_per_kw, chemistry=chemistry,
                  diesel_price=diesel_price)
    run = dict(common, target=target, project_years=project_years, growth=growth)
    size = dict(common, renewable_target=target, demand_growth=growth)

    candidates = []
    big = size_system(design_year=project_years, **size)
    candidates.append(evaluate("A: build big", big.pv_kw, big.battery_kwh, None, **run))

    for n in replacement_after_years:
        r = n + 1                                 # replacement year
        if r > project_years:
            continue
        first = size_system(design_year=n, **size)                       # old first battery
        last = size_system(design_year=project_years, battery_year=project_years - n, **size)
        candidates.append(evaluate(f"B: replace in year {r}", max(first.pv_kw, last.pv_kw),
                                   max(first.battery_kwh, last.battery_kwh), r, **run))

    feasible = [c for c in candidates if c.meets_target_every_year]
    if feasible:
        recommended = min(feasible, key=lambda c: c.npv_usd)
    else:
        recommended = max(candidates, key=lambda c: (c.min_share, -c.npv_usd))

    return StrategyComparison(
        recommended=recommended, candidates=candidates,
        year1_optimal=size_system(**size), any_feasible=bool(feasible),
        target=target, project_years=project_years,
    )
