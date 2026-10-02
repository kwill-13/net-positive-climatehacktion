"""
Village electricity demand.

PLACEHOLDER: `village_profile` is a generic shape. A teammate will supply better
profiles in the same format: np.ndarray of 8760 hourly kW values.
"""

import numpy as np

from sunsafe import config

# Relative demand for each hour of the day (00:00-23:00 local time), before scaling.
# Flat baseline (fridges, freezers, clinic, comms, street lights), a small morning bump,
# a daytime plateau (school, offices, workshops) and an evening peak (lights, TV, cooking).
# PLACEHOLDER shape, not measured data.
_DAILY_SHAPE = np.array([
    0.55, 0.50, 0.48, 0.47, 0.47, 0.52,   # 00-05 night baseline
    0.70, 0.85, 0.90, 0.95, 1.00, 1.00,   # 06-11 morning + working hours
    1.00, 0.95, 0.95, 0.90, 0.95, 1.10,   # 12-17 afternoon
    1.45, 1.60, 1.50, 1.25, 0.90, 0.70,   # 18-23 evening peak
])


def estimate_daily_load_kwh(diesel_litres_per_day: float,
                            kwh_per_litre: float = config.DIESEL_KWH_PER_LITRE) -> float:
    """
    Estimate daily electricity demand from current generator fuel use.

    Args:
        diesel_litres_per_day: litres/day burned by the existing generators.
        kwh_per_litre: generator efficiency, kWh electric per litre.

    Returns:
        Daily load, kWh/day.
    """
    return diesel_litres_per_day * kwh_per_litre


def village_profile(daily_kwh: float) -> np.ndarray:
    """
    PLACEHOLDER hourly load profile: same 24-hour shape every day, evening peak.

    Args:
        daily_kwh: energy demand per day, kWh/day.

    Returns:
        np.ndarray, shape (8760,), load in kW for each hour. Each day sums to daily_kwh.
    """
    day = _DAILY_SHAPE / _DAILY_SHAPE.sum() * daily_kwh
    return np.tile(day, config.HOURS_PER_YEAR // 24)
