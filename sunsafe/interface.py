"""
SunSafe model <-> app interface.

This file is the contract between the model (energy + lifecycle) and the app: the
`Inputs` the app sends and the `Results` it reads back. It holds data definitions only.
- The implementation is `sunsafe.model.run_sunsafe(inputs) -> Results`.
- Keep every field name, type and unit exactly as defined here. If a field needs to
  change, agree it with the model owner and update this file first.
"""

from dataclasses import dataclass, field
from typing import List, Literal, Optional


# ---------------------------------------------------------------- inputs ----

@dataclass
class Inputs:
    site_name: str
    latitude: float                      # decimal degrees, south is negative
    longitude: float                     # decimal degrees, west is negative
    diesel_litres_per_day: float         # current generator fuel use
    diesel_price_per_litre: float        # delivered price incl. freight, USD
    daily_load_kwh: Optional[float] = None   # if None, estimated from diesel use
    critical_load_kw: float = 5.0        # clinic, comms: used for backup hours
    renewable_target: float = 0.90       # 0-1, share of energy from solar
    battery_chemistry: Literal["lead_acid", "lithium"] = "lithium"
    demand_growth_per_year: float = 0.03 # 0-1, e.g. 0.03 = 3% a year
    project_years: int = 15


# --------------------------------------------------------------- outputs ----

@dataclass
class Sizing:
    pv_kw: float
    battery_kwh: float
    capex_usd: float
    renewable_share_year1: float         # 0-1
    diesel_litres_avoided_year1: float


@dataclass
class LifecycleYear:
    year: int                            # 1 = first year of operation
    share_funded_day_one: float          # 0-1, no battery replacement
    share_funded_year_15: float          # 0-1, batteries replaced on schedule
    battery_capacity_kwh: float          # usable capacity that year (no replacement)
    demand_kwh_per_day: float


@dataclass
class Finance:
    om_fund_per_year_usd: float          # yearly set-aside for O&M + replacement
    cost_per_kwh_hybrid_usd: float
    cost_per_kwh_diesel_usd: float
    payback_years: float


@dataclass
class FuelShockMonth:
    month: str                           # "2026-01"
    diesel_price_per_litre: float
    cost_diesel_only_usd: float
    cost_hybrid_usd: float


@dataclass
class Headroom:
    surplus_kwh_by_month: List[float]    # 12 values, Jan-Dec
    suggested_new_loads: List[str]       # e.g. "Community freezer (~8 kWh/day)"
    electricity_share_before: float      # 0-1, of local final energy use
    electricity_share_after: float       # 0-1


@dataclass
class PlanStage:
    year: int                            # year of operation the investment is made (start of year)
    pv_added_kw: float                   # kWp added in this stage (first stage: the initial build)
    battery_installed_kwh: float         # new battery installed, kWh nominal (0 if none)
    capex_usd: float                     # USD paid for this stage, in that year's real terms


@dataclass
class Results:
    inputs: Inputs
    sizing: Sizing
    lifecycle: List[LifecycleYear]
    finance: Finance
    fuel_shock: List[FuelShockMonth]
    backup_hours: float                  # hours critical load stays powered, no fuel
    headroom: Headroom
    warnings: List[str] = field(default_factory=list)  # data gaps, assumptions
    # Optional (added 4 Oct 2026; old callers unaffected): every investment in the recommended plan,
    # in year order. The first stage is the initial build (= `sizing`); later ones are battery
    # replacements or upgrades (staged expansion, rolling plan).
    plan_stages: List[PlanStage] = field(default_factory=list)
