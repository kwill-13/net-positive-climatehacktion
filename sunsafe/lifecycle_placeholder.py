"""
TEMPORARY placeholder for battery fade and demand growth.

Minimal compounding-rate helpers so sizing and the Tokelau script can look at later
years. The lifecycle teammate owns the real version; when it lands, switch callers
over and delete this module. Rates are PLACEHOLDERS in config.py.
"""

import numpy as np

from sunsafe import config


def capacity_factor(chemistry: str, year: int) -> float:
    """
    Remaining battery capacity as a fraction of nominal, no replacement.

    Args:
        chemistry: "lithium" or "lead_acid".
        year: year of operation, 1 = first year (no fade yet).

    Returns:
        0-1, (1 - annual_fade)^(year - 1).
    """
    if year < 1:
        raise ValueError("year must be >= 1")
    return (1.0 - config.BATTERY_ANNUAL_FADE[chemistry]) ** (year - 1)


def faded_capacity_kwh(battery_kwh: float, chemistry: str, year: int) -> float:
    """
    Nominal capacity remaining in a given year, kWh.

    Args:
        battery_kwh: nominal capacity when new, kWh.
        chemistry: "lithium" or "lead_acid".
        year: year of operation, 1 = first year.

    Returns:
        kWh.
    """
    return battery_kwh * capacity_factor(chemistry, year)


def grown_load(load_kw: np.ndarray, year: int,
               growth: float = config.DEMAND_GROWTH_PER_YEAR) -> np.ndarray:
    """
    Hourly load scaled by compounding demand growth (same shape every year).

    Args:
        load_kw: year-1 hourly demand, kW.
        year: year of operation, 1 = first year (unchanged).
        growth: demand growth per year, 0-1.

    Returns:
        np.ndarray, kW, load_kw x (1 + growth)^(year - 1).
    """
    if year < 1:
        raise ValueError("year must be >= 1")
    return np.asarray(load_kw, dtype=float) * (1.0 + growth) ** (year - 1)
