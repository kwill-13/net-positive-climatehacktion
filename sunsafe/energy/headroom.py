"""
Surplus solar and what it could power: new electric loads and the electricity share
of the community's total energy use.
"""

from typing import List, Tuple

import numpy as np

from sunsafe import config
from sunsafe.hours import DAYS_IN_MONTH, monthly_sum


def surplus_by_month(curtailed_kw: np.ndarray) -> List[float]:
    """
    Curtailed (unused) solar per calendar month.

    Args:
        curtailed_kw: hourly curtailed PV, kW (8760), e.g. SimResult.curtailed for year 1.

    Returns:
        12 values, kWh per month, Jan-Dec.
    """
    return [float(v) for v in monthly_sum(curtailed_kw)]


def suggest_new_loads(surplus_kwh_by_month: List[float],
                      candidates=config.CANDIDATE_NEW_LOADS) -> List[Tuple[str, float]]:
    """
    Candidate loads that fit within the surplus of the leanest month, taken in config order.

    Uses kWh/day of the month with the least surplus per day, so the loads fit all year.
    Ignores timing (surplus is midday; a freezer runs all day): a first screen, not dispatch.

    Args:
        surplus_kwh_by_month: 12 values, kWh/month.
        candidates: list of (description, kWh/day).

    Returns:
        List of (description, kWh/day) that fit together.
    """
    per_day = np.asarray(surplus_kwh_by_month, dtype=float) / DAYS_IN_MONTH
    room = float(per_day.min())
    chosen = []
    for name, kwh in candidates:
        if kwh <= room:
            chosen.append((name, kwh))
            room -= kwh
    return chosen


def non_electric_kwh_per_day(site_name: str, daily_electric_kwh: float) -> float:
    """
    Placeholder non-electric energy use (cooking fuel + outboard petrol), kWh/day equivalent.

    Looks up config.SITE_NON_ELECTRIC_KWH_PER_DAY by lowercase substring of site_name,
    else uses NON_ELECTRIC_TO_ELECTRIC_RATIO x daily electric load.

    Returns:
        kWh/day.
    """
    name = site_name.lower()
    for key, kwh in config.SITE_NON_ELECTRIC_KWH_PER_DAY.items():
        if key in name:
            return kwh
    return config.NON_ELECTRIC_TO_ELECTRIC_RATIO * daily_electric_kwh


def electricity_share(daily_electric_kwh: float, non_electric_kwh: float,
                      added_electric_kwh: float = 0.0) -> float:
    """
    Electricity's share of total final energy use, 0-1.

    New electric loads are assumed to displace the same kWh of non-electric fuel (1:1,
    conservative: electric cooking and motors are usually more efficient), so total
    energy stays the same and only the split changes.

    Args:
        daily_electric_kwh: electricity use today, kWh/day.
        non_electric_kwh: non-electric energy use today, kWh/day.
        added_electric_kwh: new electric loads switched from fuel, kWh/day.

    Returns:
        0-1.
    """
    total = daily_electric_kwh + non_electric_kwh
    moved = min(added_electric_kwh, non_electric_kwh)
    return (daily_electric_kwh + moved) / total if total > 0 else 0.0
