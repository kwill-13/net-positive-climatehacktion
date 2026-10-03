"""
How the system and its load change with age.

Simple compounding rates from config.py (PV derate, lead-acid fade and Tokelau demand growth
sourced; lithium fade still a TODO placeholder):
battery capacity fade, PV output derate and demand growth. Year 1 = first year of
operation, when nothing has faded or grown yet.
"""

from typing import Optional

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


def demand(year: int, base_load_kw: np.ndarray,
           growth: float = config.DEMAND_GROWTH_PER_YEAR) -> np.ndarray:
    """
    Hourly load in year `year`, scaled by compounding growth (same shape every year).

    Args:
        year: year of operation, 1 = first year (unchanged).
        base_load_kw: year-1 hourly demand, kW.
        growth: demand growth per year, 0-1.

    Returns:
        np.ndarray, kW, base_load_kw x (1 + growth)^(year - 1).
    """
    _check_year(year)
    return np.asarray(base_load_kw, dtype=float) * (1.0 + growth) ** (year - 1)
