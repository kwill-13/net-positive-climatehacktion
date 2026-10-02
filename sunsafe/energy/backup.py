"""Backup autonomy: how long the battery alone can keep critical loads running."""

from sunsafe.energy.simulate import battery_params


def backup_hours(battery_kwh: float, chemistry: str, critical_load_kw: float) -> float:
    """
    Hours a full battery can carry the critical load with no solar and no diesel.

    usable energy = battery_kwh x (1 - min_soc) x discharge efficiency
    hours         = usable energy / critical_load_kw

    Assumes the battery starts full, the critical load is constant, and the rest of the
    village is switched off. Conservative in that any solar during the outage is ignored.

    Args:
        battery_kwh: nominal capacity, kWh (pass a faded value for later years).
        chemistry: "lithium" or "lead_acid" (sets min SOC and discharge efficiency).
        critical_load_kw: constant critical demand (clinic, comms), kW. Must be > 0.

    Returns:
        Hours of backup.
    """
    if critical_load_kw <= 0:
        raise ValueError("critical_load_kw must be > 0")
    p = battery_params(chemistry)
    usable_kwh = battery_kwh * (1.0 - p["min_soc"]) * p["eta_discharge"]
    return usable_kwh / critical_load_kw
