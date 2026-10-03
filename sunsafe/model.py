"""
Real `run_sunsafe`: same signature and Results as the contract in interface.py.

Pipeline:
  1. Load profile and NASA POWER solar for the site.
  2. Strategy comparison (sunsafe/lifecycle/strategy.py): "build big" vs "moderate +
     planned battery replacement"; the recommended design is the lowest 15-year NPV that
     meets the renewable target EVERY year.
  3. Every Results field is filled from that recommended design. Nothing comes from
     run_sunsafe_fake any more; `warnings` lists the placeholder assumptions still in use.
"""

from typing import List

from sunsafe import config
from sunsafe.energy import headroom as hr
from sunsafe.energy.backup import backup_hours
from sunsafe.energy.diesel import litres_from_kwh
from sunsafe.energy.simulate import battery_params, simulate
from sunsafe.energy.solar import fetch_weather, pv_output_per_kw
from sunsafe.interface import Finance, Headroom, Inputs, LifecycleYear, Results, Sizing
from sunsafe.lifecycle import finance as fin
from sunsafe.lifecycle.projection import run_years
from sunsafe.lifecycle.strategy import StrategyComparison, compare_strategies
from sunsafe.load_profiles import estimate_daily_load_kwh, village_profile

PLACEHOLDER_WARNINGS = [
    "Load profile is a generic placeholder shape (evening peak), not measured.",
    "Capital costs (PV, battery) and O&M costs are PLACEHOLDERS in config.py, not yet sourced.",
    "Battery fade, PV derate, battery life and battery price decline are PLACEHOLDER rates.",
    "Fuel-shock 2026 price path is a PLACEHOLDER (+35% from April on the site's price).",
    "Headroom: candidate new loads and non-electric energy use are PLACEHOLDERS.",
    f"Generator efficiency assumed {config.DIESEL_KWH_PER_LITRE} kWh/litre at all loads.",
    "Generator capex/O&M and battery salvage value are not included in costs.",
]


def run_sunsafe(inputs: Inputs) -> Results:
    """
    Run the SunSafe model for one site.

    Args:
        inputs: site and design inputs (see interface.Inputs for units).

    Returns:
        Results for the recommended design (see module docstring).
    """
    results, _ = run_sunsafe_detailed(inputs)
    return results


def run_sunsafe_detailed(inputs: Inputs):
    """
    Same as run_sunsafe, but also returns the StrategyComparison (all candidates and the
    year-1 cost-optimal design) for reports.

    Returns:
        (Results, StrategyComparison)
    """
    warnings: List[str] = []
    chem = inputs.battery_chemistry
    price = inputs.diesel_price_per_litre
    years = inputs.project_years
    growth = inputs.demand_growth_per_year

    # ---- site: load and solar
    daily_kwh = inputs.daily_load_kwh
    if daily_kwh is None:
        daily_kwh = estimate_daily_load_kwh(inputs.diesel_litres_per_day)
        warnings.append(f"Daily load estimated from diesel use: {daily_kwh:.0f} kWh/day "
                        f"at {config.DIESEL_KWH_PER_LITRE} kWh/litre.")
    load_kw = village_profile(daily_kwh)

    weather = fetch_weather(inputs.latitude, inputs.longitude)
    if weather.attrs.get("source") != "nasa_power":
        warnings.append("NASA POWER unavailable: solar based on a SYNTHETIC tropical profile.")
    pv_per_kw = pv_output_per_kw(weather)

    # ---- choose the design
    comp: StrategyComparison = compare_strategies(load_kw, pv_per_kw, inputs.renewable_target,
                                                  chem, price, years, growth)
    rec = comp.recommended
    if not comp.any_feasible:
        warnings.append(f"No design kept {inputs.renewable_target:.0%} renewable in every year; "
                        f"showing the best found (lowest year {rec.min_share:.1%}).")
    year1 = simulate(rec.pv_kw, rec.battery_kwh, load_kw, pv_per_kw, chem)

    # ---- sizing
    litres_diesel_only_y1 = litres_from_kwh(year1.load_kwh)
    litres_avoided_y1 = litres_diesel_only_y1 - year1.diesel_litres
    sizing = Sizing(
        pv_kw=round(rec.pv_kw, 1),
        battery_kwh=round(rec.battery_kwh, 1),
        capex_usd=round(rec.capex_usd),
        renewable_share_year1=round(year1.renewable_share, 4),
        diesel_litres_avoided_year1=round(litres_avoided_y1),
    )

    # ---- lifecycle: same design with its planned replacement vs never replaced
    no_repl = (rec.years if rec.replacement_year is None else
               run_years(rec.pv_kw, rec.battery_kwh, load_kw, pv_per_kw, chem, years,
                         replace_battery_in=None, growth=growth))
    usable = 1.0 - battery_params(chem)["min_soc"]
    lifecycle = [
        LifecycleYear(
            year=planned.year,
            share_funded_day_one=round(never.renewable_share, 4),
            share_funded_year_15=round(planned.renewable_share, 4),
            battery_capacity_kwh=round(never.battery_kwh * usable, 1),   # usable, per contract
            demand_kwh_per_day=round(planned.demand_kwh_per_day, 1),
        )
        for planned, never in zip(rec.years, no_repl)
    ]

    # ---- finance
    sinking = (fin.sinking_fund_deposit(rec.replacement_usd, rec.replacement_year - 1)
               if rec.replacement_year else 0.0)
    kwh_by_year = [y.load_kwh for y in rec.years]
    npv_diesel_only = sum(litres_from_kwh(k) * price * fin.discount(y)
                          for y, k in enumerate(kwh_by_year, start=1))
    payback = fin.simple_payback_years(rec.capex_usd, litres_avoided_y1 * price,
                                       rec.annual_om_usd)
    if payback == float("inf"):
        warnings.append("Diesel savings do not cover O&M: the system never pays back.")
    finance = Finance(
        om_fund_per_year_usd=round(rec.annual_om_usd + sinking),
        cost_per_kwh_hybrid_usd=round(fin.levelised_cost_per_kwh(rec.npv_usd, kwh_by_year), 3),
        cost_per_kwh_diesel_usd=round(fin.levelised_cost_per_kwh(npv_diesel_only, kwh_by_year), 3),
        payback_years=round(payback, 1),
    )

    # ---- fuel shock (year-1 operation)
    fuel_shock = fin.fuel_shock(load_kw, year1.gen, price, rec.annual_om_usd)

    # ---- headroom (year-1 surplus)
    surplus = hr.surplus_by_month(year1.curtailed)
    new_loads = hr.suggest_new_loads(surplus)
    non_elec = hr.non_electric_kwh_per_day(inputs.site_name, daily_kwh)
    added = sum(kwh for _, kwh in new_loads)
    headroom = Headroom(
        surplus_kwh_by_month=[round(v) for v in surplus],
        suggested_new_loads=[f"{name} (~{kwh:g} kWh/day)" for name, kwh in new_loads],
        electricity_share_before=round(hr.electricity_share(daily_kwh, non_elec), 3),
        electricity_share_after=round(hr.electricity_share(daily_kwh, non_elec, added), 3),
    )

    results = Results(
        inputs=inputs,
        sizing=sizing,
        lifecycle=lifecycle,
        finance=finance,
        fuel_shock=fuel_shock,
        backup_hours=round(backup_hours(rec.battery_kwh, chem, inputs.critical_load_kw), 1),
        headroom=headroom,
        warnings=warnings + [f"Recommended: {rec.name}."] + PLACEHOLDER_WARNINGS,
    )
    return results, comp


if __name__ == "__main__":
    demo = Inputs(site_name="Fakaofo (test)", latitude=-9.38, longitude=-171.24,
                  diesel_litres_per_day=200, diesel_price_per_litre=1.10)
    r = run_sunsafe(demo)
    print(r.sizing)
    print(r.finance)
    print(f"Backup hours: {r.backup_hours}")
    for m in r.fuel_shock:
        print(m)
    print(r.headroom)
    for y in r.lifecycle:
        print(y)
    for w in r.warnings:
        print("WARNING:", w)
