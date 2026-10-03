"""
How the system and its load change with age.

Simple compounding rates from config.py (PV derate, lead-acid fade and Tokelau demand growth
sourced; lithium fade still a TODO placeholder):
battery capacity fade, PV output derate and demand growth. Year 1 = first year of
operation, when nothing has faded or grown yet.
"""

from dataclasses import dataclass
from typing import Optional, Union

import numpy as np

from sunsafe import config


def _check_year(year: int) -> None:
    if year < 1:
        raise ValueError("year must be >= 1 (1 = first year of operation)")


def capacity_factor(chemistry: str, year: int, fade: Optional[float] = None) -> float:
    """
    Battery capacity remaining as a fraction of nominal, in the battery's `year` of life.

    Args:
        chemistry: "lithium" or "lead_acid".
        year: year of the battery's life, 1 = new.
        fade: capacity lost per year, 0-1; defaults to config.BATTERY_ANNUAL_FADE[chemistry].

    Returns:
        0-1, (1 - fade)^(year - 1).
    """
    _check_year(year)
    if fade is None:
        fade = config.BATTERY_ANNUAL_FADE[chemistry]
    return (1.0 - fade) ** (year - 1)


def battery_capacity(year: int, nominal_kwh: float, chemistry: str,
                     fade: Optional[float] = None) -> float:
    """
    Nominal battery capacity remaining in the battery's `year` of life, no replacement.

    Args:
        year: year of the battery's life, 1 = new.
        nominal_kwh: capacity when new, kWh.
        chemistry: "lithium" or "lead_acid".
        fade: capacity lost per year, 0-1; defaults to config.

    Returns:
        kWh (still "nominal": usable is this x (1 - min_soc)).
    """
    return nominal_kwh * capacity_factor(chemistry, year, fade)


def pv_derate(year: int) -> float:
    """
    PV output in year `year` as a fraction of year-1 output.

    Args:
        year: year of operation, 1 = first year.

    Returns:
        0-1, (1 - config.PV_ANNUAL_DERATE)^(year - 1).
    """
    _check_year(year)
    return (1.0 - config.PV_ANNUAL_DERATE) ** (year - 1)


@dataclass(frozen=True)
class GrowthSchedule:
    """
    Demand growth that changes over time: `fast_rate` for the first `fast_years` year-on-year
    steps, then `steady_rate`. E.g. GrowthSchedule(0.09, 5, 0.03) = 9%/yr for years 2-6, then 3%.
    fast_years = 0 is the same as constant growth at steady_rate.
    """
    fast_rate: float      # 0-1 per year
    fast_years: int       # number of year-on-year steps at fast_rate, >= 0
    steady_rate: float    # 0-1 per year afterwards

    def rate(self, step: int) -> float:
        """Growth rate from year `step` to year `step + 1` (step 1 = year 1 -> 2)."""
        return self.fast_rate if step <= self.fast_years else self.steady_rate


Growth = Union[float, GrowthSchedule]   # a constant rate (0-1 per year) or a schedule


def growth_factor(year: int, growth: Growth) -> float:
    """
    Demand in year `year` relative to year 1.

    Args:
        year: year of operation, 1 = first year.
        growth: constant rate 0-1, or a GrowthSchedule.

    Returns:
        (1 + g)^(year - 1) for a constant rate; the product of each year's rate for a schedule.
    """
    _check_year(year)
    if isinstance(growth, GrowthSchedule):
        f = 1.0
        for step in range(1, year):
            f *= 1.0 + growth.rate(step)
        return f
    return (1.0 + growth) ** (year - 1)


def demand(year: int, base_load_kw: np.ndarray,
           growth: Growth = config.DEMAND_GROWTH_PER_YEAR) -> np.ndarray:
    """
    Hourly load in year `year`, scaled by compounding growth (same shape every year).

    Args:
        year: year of operation, 1 = first year (unchanged).
        base_load_kw: year-1 hourly demand, kW.
        growth: demand growth, either a constant rate per year (0-1) or a GrowthSchedule.

    Returns:
        np.ndarray, kW, base_load_kw x growth_factor(year, growth).
    """
    _check_year(year)
    return np.asarray(base_load_kw, dtype=float) * growth_factor(year, growth)
