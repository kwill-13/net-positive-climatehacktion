"""
Choose the design that stays on target EVERY year at the lowest project-life cost.

Three strategies, same renewable target, over project_years (P):

A  "Build big": size for year P (faded battery, grown load, derated PV), never replace.
B  "Moderate + planned replacement", for each N in config.STRATEGY_REPLACEMENT_AFTER_YEARS:
   the battery is replaced (same size) at the start of year N+1. The two hardest years are
   year N (oldest first battery) and year P (biggest load, second battery P-N years old). Each
   is sized with size_system(); taking the larger PV and the larger battery of the two meets
   both, because renewable share only rises with more PV or more battery.
C  "Staged expansion", for each N (what Tokelau did: 2012 build, 2020 upgrade): build only
   what year N needs, then at the start of year N+1 add PV and install a new, right-sized
   battery so that year P is met. It reuses B's two sizings: build = the year-N design;
   upgrade = PV max(year-N PV, year-P PV), battery = the year-P design's battery. The upgrade
   is paid at the start of year N+1 (PV at today's real price, battery at the declined price).

Every candidate is then checked with run_years() in every year, and the feasible one with
the lowest NPV (capex + O&M + replacement/upgrade + generator fuel and O&M) is recommended.
The year-1 cost-optimal design is kept for reporting only.
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
    name: str                        # "A: build big", "B: replace in year 9", "C: expand in year 9 ..."
    pv_kw: float                     # kWp, as first installed
    battery_kwh: float               # kWh nominal, as first installed
    replacement_year: Optional[int]  # year of the battery replacement (B) or upgrade (C), or None
    capex_usd: float                 # USD up front, PV + battery
    replacement_usd: float           # USD paid at the start of replacement_year (0 if none)
    annual_om_usd: float             # USD/yr in year 1
    npv_usd: float                   # USD, present value of capex + O&M + replacement + diesel
    years: List[YearResult]          # with the planned replacement (if any)
    min_share: float                 # 0-1, lowest renewable share over the project
    meets_target_every_year: bool
    om_by_year: List[float] = field(default_factory=list)   # USD/yr for years 1..P
    upgrade_pv_kw: Optional[float] = None       # C only: total kWp after the upgrade
    upgrade_battery_kwh: Optional[float] = None  # C only: new battery, kWh nominal


@dataclass
class StrategyComparison:
    recommended: Strategy            # lowest NPV among feasible (or best min_share if none)
    candidates: List[Strategy]       # A first, then B and C for each N
    year1_optimal: SizingOption      # cheapest design meeting the target in year 1 only (report)
    any_feasible: bool               # False if no candidate held the target every year
    target: float = 0.0
    project_years: int = 15
    notes: List[str] = field(default_factory=list)


def evaluate(name: str, pv_kw: float, battery_kwh: float, replacement_year: Optional[int],
             load_kw: np.ndarray, pv_per_kw: np.ndarray, target: float, chemistry: str,
             diesel_price: float, project_years: int, growth: float,
             upgrade_pv_kw: Optional[float] = None,
             upgrade_battery_kwh: Optional[float] = None) -> Strategy:
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
        upgrade_pv_kw, upgrade_battery_kwh: for a staged upgrade (C) in replacement_year: total
            kWp afterwards and the new battery's kWh nominal. None = same-size battery
            replacement (B), or nothing if replacement_year is None (A).

    Returns:
        Strategy.
    """
    staged = upgrade_pv_kw is not None
    if staged:
        years = run_years(pv_kw, battery_kwh, load_kw, pv_per_kw, chemistry, project_years,
                          growth=growth, upgrade_in=replacement_year,
                          upgrade_pv_kw=upgrade_pv_kw, upgrade_battery_kwh=upgrade_battery_kwh)
        repl = ((upgrade_pv_kw - pv_kw) * config.PV_COST_USD_PER_KW
                + finance.replacement_cost_usd(upgrade_battery_kwh, chemistry, replacement_year))
        om_after = finance.annual_om_usd(upgrade_pv_kw, upgrade_battery_kwh)
    else:
        years = run_years(pv_kw, battery_kwh, load_kw, pv_per_kw, chemistry, project_years,
                          replace_battery_in=[replacement_year] if replacement_year else None,
                          growth=growth)
        repl = (finance.replacement_cost_usd(battery_kwh, chemistry, replacement_year)
                if replacement_year else 0.0)
        om_after = finance.annual_om_usd(pv_kw, battery_kwh)
    capex = capex_usd(pv_kw, battery_kwh, chemistry)
    om = finance.annual_om_usd(pv_kw, battery_kwh)
    om_by_year = [om if (not staged or y < replacement_year) else om_after
                  for y in range(1, project_years + 1)]
    npv = finance.lifetime_npv_usd(capex, om_by_year, [y.gen_kwh for y in years], diesel_price,
                                   replacement_year, repl)
    min_share = min(y.renewable_share for y in years)
    return Strategy(name=name, pv_kw=pv_kw, battery_kwh=battery_kwh,
                    replacement_year=replacement_year, capex_usd=capex, replacement_usd=repl,
                    annual_om_usd=om, npv_usd=npv, years=years, min_share=min_share,
                    meets_target_every_year=min_share >= target - 1e-9, om_by_year=om_by_year,
                    upgrade_pv_kw=upgrade_pv_kw if staged else None,
                    upgrade_battery_kwh=upgrade_battery_kwh if staged else None)


def compare_strategies(load_kw: np.ndarray, pv_per_kw: np.ndarray, target: float,
                       chemistry: str, diesel_price: float, project_years: int = 15,
                       growth: float = config.DEMAND_GROWTH_PER_YEAR,
                       replacement_after_years=config.STRATEGY_REPLACEMENT_AFTER_YEARS
                       ) -> StrategyComparison:
    """
    Compare "build big", "moderate + planned replacement" and "staged expansion"; recommend one.

    Args:
        load_kw: year-1 hourly load, kW (8760). pv_per_kw: year-1 PV kW/kWp (8760).
        target: renewable share required in EVERY year, 0-1.
        chemistry: "lithium" or "lead_acid". diesel_price: USD/litre.
        project_years: project length, years.
        growth: demand growth per year, 0-1.
        replacement_after_years: values of N to try for strategies B and C (act in year N+1).

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
        pv_after = max(first.pv_kw, last.pv_kw)
        candidates.append(evaluate(
            f"C: expand in year {r} (+{pv_after - first.pv_kw:,.0f} kWp, new {last.battery_kwh:,.0f} kWh battery)",
            first.pv_kw, first.battery_kwh, r, **run,
            upgrade_pv_kw=pv_after, upgrade_battery_kwh=last.battery_kwh))

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
