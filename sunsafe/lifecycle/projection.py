"""
Run a fixed design forward year by year: battery fades, PV derates, demand grows.

Calls simulate() once per year. Each year starts with a full battery (a simplification:
one year's end state barely matters at an hourly 8760-step resolution).
"""

from dataclasses import dataclass
from typing import Iterable, List, Optional

import numpy as np

from sunsafe import config
from sunsafe.energy.simulate import simulate
from sunsafe.lifecycle.degradation import battery_capacity, demand, pv_derate


@dataclass
class YearResult:
    year: int                    # year of operation, 1 = first
    battery_year: int            # year of the current battery's life, 1 = new
    battery_kwh: float           # nominal capacity that year (faded), kWh
    demand_kwh_per_day: float    # kWh/day average
    load_kwh: float              # kWh/yr demand
    renewable_share: float       # 0-1
    gen_kwh: float               # kWh/yr from diesel
    diesel_litres: float         # litres/yr
    curtailed_kwh: float         # kWh/yr PV thrown away


def run_years(pv_kw: float, battery_kwh: float, load_kw: np.ndarray, pv_per_kw: np.ndarray,
              chemistry: str, years: int = 15,
              replace_battery_in: Optional[Iterable[int]] = None,
              growth: float = config.DEMAND_GROWTH_PER_YEAR,
              fade: Optional[float] = None) -> List[YearResult]:
    """
    Simulate a fixed PV + battery design for `years` years.

    Args:
        pv_kw: installed PV, kWp.
        battery_kwh: nominal battery capacity when new, kWh.
        load_kw: year-1 hourly demand, kW, shape (8760,).
        pv_per_kw: year-1 hourly PV output per kWp, kW/kWp, shape (8760,).
        chemistry: "lithium" or "lead_acid".
        years: number of years to run.
        replace_battery_in: years of operation in which a new battery (same nominal kWh)
            is installed at the start of the year, e.g. [9]. None = never replaced.
        growth: demand growth per year, 0-1.
        fade: battery capacity loss per year, 0-1; defaults to config for the chemistry.

    Returns:
        List of YearResult, one per year, in order.
    """
    replacements = set(replace_battery_in or [])
    installed = 1
    out = []
    for year in range(1, years + 1):
        if year in replacements:
            installed = year
        battery_year = year - installed + 1
        cap = battery_capacity(battery_year, battery_kwh, chemistry, fade)
        load_y = demand(year, load_kw, growth)
        r = simulate(pv_kw, cap, load_y, pv_per_kw * pv_derate(year), chemistry)
        out.append(YearResult(
            year=year, battery_year=battery_year, battery_kwh=cap,
            demand_kwh_per_day=r.load_kwh / (len(load_y) / 24), load_kwh=r.load_kwh,
            renewable_share=r.renewable_share, gen_kwh=r.gen_kwh,
            diesel_litres=r.diesel_litres, curtailed_kwh=r.curtailed_kwh,
        ))
    return out
