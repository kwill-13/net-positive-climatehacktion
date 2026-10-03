"""
Strategy table for the Pacific site presets (config.SITE_PRESETS).

Run from the repo root:  python scripts/run_pacific_presets.py

For each preset and project length (15, 20, 25 years), with demand growth 9%/yr for 5 years
then 3%/yr, prints the recommended strategy (A-D), its investment stages, NPV, number of
upgrades and the model runtime.

INPUTS ARE ILLUSTRATIVE except the Tokelau validation site: real coordinates (NASA POWER
weather), but made-up diesel use and the Tokelau delivered price. Not site assessments.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sunsafe import config  # noqa: E402
from sunsafe.interface import Inputs  # noqa: E402
from sunsafe.lifecycle.degradation import GrowthSchedule  # noqa: E402
from sunsafe.model import run_sunsafe_detailed  # noqa: E402

GROWTH = GrowthSchedule(fast_rate=0.09, fast_years=5, steady_rate=0.03)
HORIZONS = (15, 20, 25)
# Fakaofo stands in for the three Tokelau atolls; the rest are the illustrative presets.
SITES = [p for p in config.SITE_PRESETS if p["illustrative"] or p["name"].startswith("Fakaofo")]


def main() -> None:
    print("SunSafe strategy table: Pacific presets")
    print(f"Growth {GROWTH.fast_rate:.0%}/yr for {GROWTH.fast_years} yrs, then {GROWTH.steady_rate:.0%}/yr. "
          f"Discount {config.PROJECT_DISCOUNT_RATE:.0%}. Target and price per row.")
    print("ILLUSTRATIVE INPUTS: diesel use and price are made up (except the Fakaofo validation case).\n")
    for p in SITES:
        tag = "ILLUSTRATIVE" if p["illustrative"] else "validation inputs"
        load = (f"{p['daily_load_kwh']:.0f} kWh/day" if p["daily_load_kwh"] else
                f"load from diesel")
        print(f"== {p['name']} ({p['lat']:.2f}, {p['lon']:.2f}; {p['note']}) [{tag}]")
        print(f"   {p['diesel_litres_per_day']} L/day, {load}, USD {p['diesel_price']:.2f}/L, "
              f"{p['chemistry']}, target {p['target']:.0%}")
        print(f"   {'yrs':>3}  {'recommended':<12} {'NPV USD':>11} {'upg':>3} {'time':>6}  stages (year: +kWp, new battery kWh, capex USD)")
        for years in HORIZONS:
            inputs = Inputs(site_name=p["name"], latitude=p["lat"], longitude=p["lon"],
                            diesel_litres_per_day=p["diesel_litres_per_day"],
                            diesel_price_per_litre=p["diesel_price"],
                            daily_load_kwh=p["daily_load_kwh"], renewable_target=p["target"],
                            battery_chemistry=p["chemistry"], project_years=years)
            t0 = time.perf_counter()
            results, comp = run_sunsafe_detailed(inputs, growth=GROWTH)
            dt = time.perf_counter() - t0
            rec = comp.recommended
            short = rec.name.split(" (")[0].replace("rolling plan, ", "D ").split(":")[0]
            if rec.name.startswith("D"):
                short = "D " + rec.name.split(", ")[1].split(" ")[0]          # e.g. "D 8-yr"
                if "merged" in rec.name:
                    short += " m"
            elif rec.name.startswith(("B", "C")):
                short = rec.name.split(" (")[0].replace(": expand in year", " yr").replace(": replace in year", " yr")
            stages = "; ".join(f"y{s.year}: +{s.pv_added_kw:,.0f}, {s.battery_installed_kwh:,.0f}, "
                               f"{s.capex_usd/1e3:,.0f}k" for s in results.plan_stages)
            flag = "" if comp.any_feasible else "  (target NOT met every year)"
            print(f"   {years:>3}  {short:<12} {rec.npv_usd:>11,.0f} {len(results.plan_stages) - 1:>3} "
                  f"{dt:>5.1f}s  {stages}{flag}")
        print()
    print("Strategies: A build big; B same-size battery replacement; C build for year N, upgrade in N+1;")
    print("D rolling plan with K-yr stages ('m' = short last stage merged into the previous one).")
    print("upg = investments after the first build. NPV = capex + O&M + battery/upgrade + generator fuel and O&M, 8% real.")


if __name__ == "__main__":
    main()
