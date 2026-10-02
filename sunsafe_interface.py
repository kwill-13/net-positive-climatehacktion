"""
SunSafe model <-> app interface.

This file is the contract between the model (energy + lifecycle) and the app.
- The app only ever calls `run_sunsafe(inputs)` and reads the fields of `Results`.
- The model team replaces `run_sunsafe_fake` with the real implementation,
  keeping every field name, type and unit exactly as defined here.
- If a field needs to change, agree it at a check-in and update this file first.
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
class Results:
    inputs: Inputs
    sizing: Sizing
    lifecycle: List[LifecycleYear]
    finance: Finance
    fuel_shock: List[FuelShockMonth]
    backup_hours: float                  # hours critical load stays powered, no fuel
    headroom: Headroom
    warnings: List[str] = field(default_factory=list)  # data gaps, assumptions


# ---------------------------------------------------- fake implementation ----

def run_sunsafe_fake(inputs: Inputs) -> Results:
    """Realistic made-up numbers so the app can be built before the model exists."""
    load = inputs.daily_load_kwh or inputs.diesel_litres_per_day * 3.0
    pv_kw = round(load / 4.2 * 1.5, 1)
    battery_kwh = round(load * 1.5, 1)

    lifecycle = []
    for y in range(1, inputs.project_years + 1):
        fade = max(0.4, 1 - 0.06 * (y - 1))
        lifecycle.append(LifecycleYear(
            year=y,
            share_funded_day_one=round(max(0.55, 0.97 - 0.035 * max(0, y - 5)), 3),
            share_funded_year_15=0.95,
            battery_capacity_kwh=round(battery_kwh * fade, 1),
            demand_kwh_per_day=round(load * (1 + inputs.demand_growth_per_year) ** (y - 1), 1),
        ))

    prices = [1.10, 1.10, 1.25, 1.80, 1.75, 1.60]
    fuel_shock = [
        FuelShockMonth(
            month=f"2026-0{i + 1}",
            diesel_price_per_litre=p,
            cost_diesel_only_usd=round(inputs.diesel_litres_per_day * 30 * p),
            cost_hybrid_usd=round(inputs.diesel_litres_per_day * 30 * p * 0.1 + 1500),
        )
        for i, p in enumerate(prices)
    ]

    return Results(
        inputs=inputs,
        sizing=Sizing(
            pv_kw=pv_kw,
            battery_kwh=battery_kwh,
            capex_usd=round(pv_kw * 2500 + battery_kwh * 600),
            renewable_share_year1=0.95,
            diesel_litres_avoided_year1=round(inputs.diesel_litres_per_day * 365 * 0.9),
        ),
        lifecycle=lifecycle,
        finance=Finance(
            om_fund_per_year_usd=round(battery_kwh * 45),
            cost_per_kwh_hybrid_usd=0.32,
            cost_per_kwh_diesel_usd=0.55,
            payback_years=8.5,
        ),
        fuel_shock=fuel_shock,
        backup_hours=round(battery_kwh * 0.8 / inputs.critical_load_kw, 1),
        headroom=Headroom(
            surplus_kwh_by_month=[round(load * s) for s in
                                  [9, 8, 7, 6, 5, 4, 4, 5, 6, 8, 9, 10]],
            suggested_new_loads=["Community freezer (~8 kWh/day)",
                                 "Electric cooking at the school (~12 kWh/day)",
                                 "Charging for electric outboard motors (~15 kWh/day)"],
            electricity_share_before=0.25,
            electricity_share_after=0.38,
        ),
        warnings=["FAKE DATA: replace with the real model before the demo."],
    )


# The app imports this name. Swap the right-hand side when the real model is ready.
run_sunsafe = run_sunsafe_fake


if __name__ == "__main__":
    demo = Inputs(site_name="Fakaofo (test)", latitude=-9.38, longitude=-171.24,
                  diesel_litres_per_day=200, diesel_price_per_litre=1.10)
    r = run_sunsafe(demo)
    print(r.sizing)
    print(r.finance)
    print(f"Backup hours: {r.backup_hours}")
