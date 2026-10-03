"""
Validation: size Fakaofo (Tokelau) and compare with the real 2012 installation.

Run from the repo root:  python scripts/run_tokelau.py

The model is NOT tuned to these numbers. This only reports how far apart they are.

Sections:
  1. Year-1 cost-optimal sizing at the base target.
  2. Sensitivity table: renewable target x design year (size for faded battery + grown load).
  3. 15-year forward run of the year-1 optimal system vs the real installed system.
Fade and growth come from sunsafe/lifecycle/degradation.py (placeholder rates in config.py).
Reference figures (per atoll):
  Source A: 265-365 kWp PV, 1.1-1.6 MWh nominal lead-acid.
  Source B: ~8 MWh lead-acid across three atolls, i.e. ~2.7 MWh per atoll.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sunsafe import config  # noqa: E402
from sunsafe.energy.backup import backup_hours  # noqa: E402
from sunsafe.energy.simulate import simulate  # noqa: E402
from sunsafe.energy.sizing import size_system  # noqa: E402
from sunsafe.energy.solar import fetch_weather, pv_output_per_kw  # noqa: E402
from sunsafe.lifecycle.degradation import battery_capacity, demand  # noqa: E402
from sunsafe.load_profiles import village_profile  # noqa: E402

LAT, LON = -9.38, -171.24          # Fakaofo
CHEMISTRY = "lead_acid"
TARGET = 0.95
DAILY_LOADS_KWH = [600, 720]
DIESEL_PRICE = 1.10                # USD/litre, placeholder; only affects the cost trade-off

REAL_PV_KW = (265, 365)
SOURCE_A_BATT_KWH = (1100, 1600)
SOURCE_B_BATT_KWH = 8000 / 3
REAL_SYSTEM = (300.0, 1350.0)      # kWp, kWh nominal lead-acid: mid-range of Source A

SENS_TARGETS = [0.95, 0.99, 1.0]
SENS_DESIGN_YEARS = [1, 8, 15]
FORWARD_YEARS = 15


def _vs(value, lo, hi=None):
    """Describe value relative to a range (or a single number)."""
    if hi is None:
        return f"{value / lo:.2f}x"
    if value < lo:
        return f"{value / lo:.2f}x of low end"
    if value > hi:
        return f"{value / hi:.2f}x of high end"
    return "within range"


def _ratio(value, lo, hi=None):
    """Model / real as 'a-bx' for a range (model/hi to model/lo), or 'ax' for one number."""
    if hi is None:
        return f"{value / lo:.2f}x"
    return f"{value / hi:.2f}-{value / lo:.2f}x"


def sensitivity_table(pv_per_kw):
    """Section 2: sizing for each (target, design year), per daily load."""
    print("=" * 100)
    print(f"2. SENSITIVITY: target x design year ({CHEMISTRY}; battery kWh = nominal as installed;")
    print("   ratio = model / real, so 1.00x inside the range means a match)")
    print("=" * 100)
    for daily in DAILY_LOADS_KWH:
        load = village_profile(daily)
        print(f"\nDaily load {daily} kWh/day (year 1)")
        print(f"{'target':>6} {'year':>4} | {'PV kWp':>7} {'vs 265-365':>11} | "
              f"{'batt kWh':>8} {'vs 1.1-1.6 MWh':>14} {'vs 2.7 MWh':>10} | "
              f"{'share':>7} {'meets':>5}")
        for target in SENS_TARGETS:
            for year in SENS_DESIGN_YEARS:
                o = size_system(load, pv_per_kw, target, CHEMISTRY, DIESEL_PRICE, design_year=year)
                print(f"{target:>6.2f} {year:>4} | {o.pv_kw:>7.0f} {_ratio(o.pv_kw, *REAL_PV_KW):>11} | "
                      f"{o.battery_kwh:>8.0f} {_ratio(o.battery_kwh, *SOURCE_A_BATT_KWH):>14} "
                      f"{_ratio(o.battery_kwh, SOURCE_B_BATT_KWH):>10} | "
                      f"{o.renewable_share:>7.2%} {str(o.meets_target):>5}")
    print("\nmeets=False rows: no option in the search range reached the target; the row is the")
    print("highest-share option, which sits at the search upper bounds (PV 15x avg load, battery")
    print("3 days of effective storage), so those sizes reflect the bounds, not a design.\n")


def forward_run(pv_per_kw):
    """Section 3: run the year-1 optimum and the real system forward, no battery replacement."""
    print("=" * 100)
    print(f"3. FORWARD RUN, {FORWARD_YEARS} years, no battery replacement ({CHEMISTRY}). "
          f"Real system = {REAL_SYSTEM[0]:.0f} kWp / {REAL_SYSTEM[1]:.0f} kWh")
    print("=" * 100)
    for daily in DAILY_LOADS_KWH:
        load = village_profile(daily)
        opt = size_system(load, pv_per_kw, TARGET, CHEMISTRY, DIESEL_PRICE)
        systems = {"optimal": (opt.pv_kw, opt.battery_kwh), "real": REAL_SYSTEM}
        print(f"\nDaily load {daily} kWh/day (year 1). Year-1 optimum at {TARGET:.0%}: "
              f"{opt.pv_kw:.0f} kWp / {opt.battery_kwh:.0f} kWh")
        print(f"{'year':>4} {'load kWh/d':>10} | {'opt batt kWh':>12} {'opt share':>9} | "
              f"{'real batt kWh':>13} {'real share':>10}")
        for year in range(1, FORWARD_YEARS + 1):
            load_y = demand(year, load)
            row = []
            for pv_kw, batt_kwh in systems.values():
                batt_y = battery_capacity(year, batt_kwh, CHEMISTRY)
                share = simulate(pv_kw, batt_y, load_y, pv_per_kw, CHEMISTRY).renewable_share
                row.append((batt_y, share))
            (ob, os_), (rb, rs) = row
            print(f"{year:>4} {load_y.sum() / 365:>10.0f} | {ob:>12.0f} {os_:>9.1%} | "
                  f"{rb:>13.0f} {rs:>10.1%}")
    print()


def main():
    weather = fetch_weather(LAT, LON)
    pv_per_kw = pv_output_per_kw(weather)
    print(f"Fakaofo ({LAT}, {LON}) | weather source: {weather.attrs.get('source')} | "
          f"PV yield {pv_per_kw.sum():.0f} kWh/kWp/yr | {CHEMISTRY}, target {TARGET:.0%}\n")
    print("=" * 100)
    print("1. YEAR-1 COST-OPTIMAL SIZING")
    print("=" * 100)

    min_soc = config.BATTERY[CHEMISTRY]["min_soc"]
    for daily in DAILY_LOADS_KWH:
        opt = size_system(village_profile(daily), pv_per_kw, TARGET, CHEMISTRY, DIESEL_PRICE)
        s = opt.sim
        print(f"--- Daily load {daily} kWh/day ---")
        print(f"  Model:  PV {opt.pv_kw:6.0f} kWp | battery {opt.battery_kwh:6.0f} kWh nominal "
              f"({opt.battery_kwh * (1 - min_soc):.0f} kWh usable) | "
              f"renewable {opt.renewable_share:.1%} | meets target: {opt.meets_target}")
        print(f"          curtailed {s.curtailed_kwh / s.pv_kwh:.0%} of PV | "
              f"diesel {opt.diesel_litres:,.0f} L/yr | capex ${opt.capex_usd:,.0f} (placeholder costs) | "
              f"backup @5 kW {backup_hours(opt.battery_kwh, CHEMISTRY, 5.0):.0f} h")
        print(f"  Real PV {REAL_PV_KW[0]}-{REAL_PV_KW[1]} kWp:            "
              f"model is {_vs(opt.pv_kw, *REAL_PV_KW)}")
        print(f"  Source A battery {SOURCE_A_BATT_KWH[0]}-{SOURCE_A_BATT_KWH[1]} kWh:  "
              f"model is {_vs(opt.battery_kwh, *SOURCE_A_BATT_KWH)}")
        print(f"  Source B battery ~{SOURCE_B_BATT_KWH:.0f} kWh (8 MWh / 3): "
              f"model is {_vs(opt.battery_kwh, SOURCE_B_BATT_KWH)}\n")

    sensitivity_table(pv_per_kw)
    forward_run(pv_per_kw)


if __name__ == "__main__":
    main()
