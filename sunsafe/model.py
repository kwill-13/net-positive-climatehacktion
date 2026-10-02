"""
Real `run_sunsafe`: same signature and Results as the contract in interface.py.

Real parts:  sizing, backup_hours (energy model).
Still fake:  lifecycle, finance, fuel_shock, headroom (taken from run_sunsafe_fake).
The app switches to this function by importing `sunsafe.model.run_sunsafe`.
"""

from sunsafe import config
from sunsafe.energy.backup import backup_hours
from sunsafe.energy.diesel import litres_from_kwh
from sunsafe.energy.sizing import size_system
from sunsafe.energy.solar import fetch_weather, pv_output_per_kw
from sunsafe.interface import Inputs, Results, Sizing, run_sunsafe_fake
from sunsafe.load_profiles import estimate_daily_load_kwh, village_profile

FAKE_PARTS = ["lifecycle", "finance", "fuel_shock", "headroom"]


def run_sunsafe(inputs: Inputs) -> Results:
    """
    Run the SunSafe model for one site.

    Args:
        inputs: site and design inputs (see interface.Inputs for units).

    Returns:
        Results. `sizing` and `backup_hours` come from the energy model; the parts listed
        in FAKE_PARTS are still placeholder numbers, and `warnings` says so.
    """
    warnings = []

    daily_kwh = inputs.daily_load_kwh
    if daily_kwh is None:
        daily_kwh = estimate_daily_load_kwh(inputs.diesel_litres_per_day)
        warnings.append(f"Daily load estimated from diesel use: {daily_kwh:.0f} kWh/day "
                        f"at {config.DIESEL_KWH_PER_LITRE} kWh/litre.")
    load_kw = village_profile(daily_kwh)
    warnings.append("Load profile is a generic placeholder shape (evening peak), not measured.")

    weather = fetch_weather(inputs.latitude, inputs.longitude)
    if weather.attrs.get("source") != "nasa_power":
        warnings.append("NASA POWER unavailable: solar based on a SYNTHETIC tropical profile.")
    pv_per_kw = pv_output_per_kw(weather)

    opt = size_system(load_kw, pv_per_kw, inputs.renewable_target,
                      inputs.battery_chemistry, inputs.diesel_price_per_litre)
    if not opt.meets_target:
        warnings.append(f"Renewable target {inputs.renewable_target:.0%} not reachable in the "
                        f"search range; best found is {opt.renewable_share:.1%}.")

    # Diesel-only baseline from the same load the model sized for (consistent with sizing).
    litres_diesel_only = litres_from_kwh(opt.sim.load_kwh)
    sizing = Sizing(
        pv_kw=round(opt.pv_kw, 1),
        battery_kwh=round(opt.battery_kwh, 1),
        capex_usd=round(opt.capex_usd),
        renewable_share_year1=round(opt.renewable_share, 4),
        diesel_litres_avoided_year1=round(litres_diesel_only - opt.diesel_litres),
    )
    warnings.append("Capital costs (PV, battery) are PLACEHOLDERS in config.py, not yet sourced.")

    fake = run_sunsafe_fake(inputs)
    warnings.append("FAKE DATA still used for: " + ", ".join(FAKE_PARTS) + ".")

    return Results(
        inputs=inputs,
        sizing=sizing,
        lifecycle=fake.lifecycle,
        finance=fake.finance,
        fuel_shock=fake.fuel_shock,
        backup_hours=round(backup_hours(opt.battery_kwh, inputs.battery_chemistry,
                                        inputs.critical_load_kw), 1),
        headroom=fake.headroom,
        warnings=warnings,
    )


if __name__ == "__main__":
    demo = Inputs(site_name="Fakaofo (test)", latitude=-9.38, longitude=-171.24,
                  diesel_litres_per_day=200, diesel_price_per_litre=1.10)
    r = run_sunsafe(demo)
    print(r.sizing)
    print(f"Backup hours: {r.backup_hours}")
    for w in r.warnings:
        print("WARNING:", w)
