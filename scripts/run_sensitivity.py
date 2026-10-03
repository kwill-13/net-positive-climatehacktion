"""
Sensitivity analysis for Fakaofo (Tokelau), 15 years. Analysis only: no defaults change.

Run from the repo root:  python scripts/run_sensitivity.py
Prints markdown tables (copied into docs/sensitivity.md).

Case: Fakaofo, 600 kWh/day, lead-acid, 95% renewable every year, USD 1.87/L, 8% discount
(the run_tokelau.py validation case), strategies A-D.

  1. Demand growth: constant 9%, constant 5%, 9% for 5 years then 3%.
  2. Solar + battery O&M: config values vs Tokelau-measured (NZD 12,000/yr per atoll,
     IT Power 2013 p.31), split PV/battery pro rata to capex.
  3. Island-paid cost "if donors fund the first build": hybrid USD/kWh excluding first-build
     capex vs diesel-only, at USD 1.37 / 1.87 / 2.48 per litre.
Sections 2 and 3 use the default growth (constant 9%/yr).
"""

import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sunsafe import config  # noqa: E402
from sunsafe.interface import Inputs  # noqa: E402
from sunsafe.lifecycle import finance as fin  # noqa: E402
from sunsafe.lifecycle.degradation import GrowthSchedule  # noqa: E402
from sunsafe.model import run_sunsafe_detailed  # noqa: E402

LAT, LON = -9.38, -171.24                 # Fakaofo
DAILY_KWH = 600
CHEMISTRY = "lead_acid"
TARGET = 0.95
YEARS = 15
PRICE = config.TOKELAU_DIESEL_PRICE_USD_PER_L

GROWTH_CASES = [("constant 9%/yr", 0.09), ("constant 5%/yr", 0.05),
                ("9%/yr for 5 yrs, then 3%/yr", GrowthSchedule(0.09, 5, 0.03))]

# Tokelau-measured solar O&M: NZD 12,000/yr per atoll, excluding replacements [ITP13 p.31].
TOKELAU_OM_NZD_PER_ATOLL = 12_000
# Split PV/battery pro rata to capex, using Fakaofo's real 2012 system [IRENA13 Table 2] at the
# config unit costs, then expressed per kWp and per kWh so it scales with each plan's size.
REAL_PV_KW, REAL_BATT_KWH = 330.0, 3379.0

ISLAND_PRICES = [1.37, PRICE, 2.48]       # USD/L; 2.48 = default-case breakeven (run_tokelau.py)


def tokelau_om_rates():
    """(USD/kWp/yr, USD/kWh/yr, USD/yr total) from the measured per-atoll figure."""
    total = TOKELAU_OM_NZD_PER_ATOLL * config.NZD_TO_USD_2012
    pv_capex = REAL_PV_KW * config.PV_COST_USD_PER_KW
    batt_capex = REAL_BATT_KWH * config.BATTERY_COST_USD_PER_KWH[CHEMISTRY]
    pv_share = pv_capex / (pv_capex + batt_capex)
    return total * pv_share / REAL_PV_KW, total * (1 - pv_share) / REAL_BATT_KWH, total


@contextmanager
def om_rates(pv_rate, batt_rate):
    """Temporarily use other O&M rates (this script only; config is restored afterwards)."""
    old = config.OM_PV_USD_PER_KW_YEAR, config.OM_BATTERY_USD_PER_KWH_YEAR
    config.OM_PV_USD_PER_KW_YEAR, config.OM_BATTERY_USD_PER_KWH_YEAR = pv_rate, batt_rate
    try:
        yield
    finally:
        config.OM_PV_USD_PER_KW_YEAR, config.OM_BATTERY_USD_PER_KWH_YEAR = old


def compare(growth=config.DEMAND_GROWTH_PER_YEAR):
    inputs = Inputs(site_name="Fakaofo", latitude=LAT, longitude=LON, diesel_litres_per_day=200,
                    diesel_price_per_litre=PRICE, daily_load_kwh=DAILY_KWH,
                    renewable_target=TARGET, battery_chemistry=CHEMISTRY, project_years=YEARS)
    _, comp = run_sunsafe_detailed(inputs, growth=growth)
    return comp


def best_of(comp, letter):
    """Lowest-NPV candidate of a strategy family that meets the target every year (or None)."""
    ok = [c for c in comp.candidates if c.name.startswith(letter) and c.meets_target_every_year]
    return min(ok, key=lambda c: c.npv_usd) if ok else None


def stages_text(plan):
    first, *later = plan.stages
    text = f"build {first.pv_added_kw:,.0f} kWp / {first.battery_installed_kwh:,.0f} kWh"
    for st in later:
        text += (f"; yr {st.year}: +{st.pv_added_kw:,.0f} kWp, "
                 f"{'new ' if st.pv_added_kw > 0 else 'replace '}{st.battery_installed_kwh:,.0f} kWh")
    return text


def npv_parts(plan, price, include_first_build=True, rate=config.PROJECT_DISCOUNT_RATE):
    """Hybrid and diesel-only NPV for a fixed plan at a diesel price (all stages counted)."""
    capex = plan.capex_usd if include_first_build else 0.0
    om = [fin.annual_om_usd(*_installed(plan, y)) for y in range(1, YEARS + 1)]
    gens = [y.gen_kwh for y in plan.years]
    loads = [y.load_kwh for y in plan.years]
    hybrid = fin.lifetime_npv_usd(capex, om, gens, price, plan.replacement_year,
                                  plan.replacement_usd, rate, plan.extra_investments)
    diesel = fin.lifetime_npv_usd(0.0, 0.0, loads, price, rate=rate)
    return hybrid, diesel, loads


def _installed(plan, year):
    """(PV kWp, battery kWh nominal) in place in a year, from the plan's stages."""
    pv = batt = 0.0
    for st in plan.stages:
        if st.year <= year:
            pv += st.pv_added_kw
            batt = st.battery_installed_kwh
    return pv, batt


def per_kwh(plan, price, include_first_build=True):
    hybrid, diesel, loads = npv_parts(plan, price, include_first_build)
    return (fin.levelised_cost_per_kwh(hybrid, loads), fin.levelised_cost_per_kwh(diesel, loads))


def breakeven(plan, include_first_build=True):
    """Diesel price where hybrid = diesel-only per kWh (both are linear in price)."""
    h1, d1 = per_kwh(plan, 1.0, include_first_build)
    h2, d2 = per_kwh(plan, 2.0, include_first_build)
    gap1, slope = h1 - d1, (h2 - d2) - (h1 - d1)
    return 1.0 - gap1 / slope if slope < 0 else float("inf")


def section_growth():
    print("## 1. Demand growth\n")
    print("| Growth | Recommended | Stages (upgrade years) | NPV A | NPV best B | NPV best C | "
          "NPV best D | Saving vs A |")
    print("|---|---|---|---:|---:|---:|---:|---:|")
    for label, growth in GROWTH_CASES:
        comp = compare(growth)
        rec, a = comp.recommended, best_of(comp, "A")
        npvs = [best_of(comp, k) for k in "ABCD"]
        cells = [f"{p.npv_usd / 1e6:.2f}M" if p else "n/a" for p in npvs]
        saving = 1 - rec.npv_usd / a.npv_usd if a else float("nan")
        print(f"| {label} | {rec.name} | {stages_text(rec)} | " + " | ".join(cells)
              + f" | {saving:.0%} |")
    print("\nBest B/C/D = lowest-NPV variant of that strategy that meets the target every year. "
          "NPV in USD, 8% real.\n")


def section_om():
    pv_rate, batt_rate, total = tokelau_om_rates()
    print("## 2. Solar + battery O&M\n")
    print(f"Tokelau-measured: NZD {TOKELAU_OM_NZD_PER_ATOLL:,}/yr per atoll x "
          f"{config.NZD_TO_USD_2012} = USD {total:,.0f}/yr, split pro rata to capex of Fakaofo's "
          f"real system ({REAL_PV_KW:.0f} kWp / {REAL_BATT_KWH:,.0f} kWh) = USD {pv_rate:.1f}/kWp/yr "
          f"+ USD {batt_rate:.2f}/kWh/yr.\n")
    print("| O&M case | Rates (PV / battery) | Recommended | O&M yr 1 | Hybrid USD/kWh | "
          "Diesel-only USD/kWh | Breakeven diesel USD/L |")
    print("|---|---|---|---:|---:|---:|---:|")
    cases = [("Current config", config.OM_PV_USD_PER_KW_YEAR, config.OM_BATTERY_USD_PER_KWH_YEAR),
             ("Tokelau-measured", pv_rate, batt_rate)]
    for label, p_rate, b_rate in cases:
        with om_rates(p_rate, b_rate):
            rec = compare().recommended
            h, d = per_kwh(rec, PRICE)
            be = breakeven(rec)
            om1 = rec.om_by_year[0]
        print(f"| {label} | {p_rate:.1f} /kWp, {b_rate:.2f} /kWh | {rec.name} | {om1:,.0f} | "
              f"{h:.3f} | {d:.3f} | {be:.2f} |")
    print(f"\nAt USD {PRICE:.2f}/L, constant 9%/yr growth. Plan re-chosen under each O&M case.\n")


def section_island_paid():
    rec = compare().recommended
    print('## 3. Island-paid cost: "if donors fund the first build"\n')
    print(f"Plan: {rec.name}; {stages_text(rec)}; first build capex USD {rec.capex_usd:,.0f} "
          f"(excluded from island-paid).\n")
    print("| Diesel USD/L | Island-paid hybrid USD/kWh | Full hybrid USD/kWh | "
          "Diesel-only USD/kWh |")
    print("|---:|---:|---:|---:|")
    for p in ISLAND_PRICES:
        island, diesel = per_kwh(rec, p, include_first_build=False)
        full, _ = per_kwh(rec, p)
        print(f"| {p:.2f} | {island:.3f} | {full:.3f} | {diesel:.3f} |")
    print(f"\nIsland-paid = O&M + later stages (upgrades) + generator fuel and O&M, NPV / "
          f"discounted kWh at 8%. Breakeven diesel price: island-paid USD "
          f"{breakeven(rec, False):.2f}/L, full cost USD {breakeven(rec):.2f}/L. "
          f"Plan fixed at the USD {PRICE:.2f}/L recommendation, current O&M.\n")


def main():
    print(f"# Fakaofo sensitivity, {YEARS} years ({DAILY_KWH} kWh/day, {CHEMISTRY}, "
          f"{TARGET:.0%} every year, USD {PRICE:.2f}/L, 8% real)\n")
    section_growth()
    section_om()
    section_island_paid()


if __name__ == "__main__":
    main()
