"""
Validation: size Fakaofo (Tokelau) and compare with the real 2012 installation.

Run from the repo root:  python scripts/run_tokelau.py

The model is NOT tuned to these numbers. This only reports how far apart they are.
Reference figures (per atoll):
  Source A: 265-365 kWp PV, 1.1-1.6 MWh nominal lead-acid.
  Source B: ~8 MWh lead-acid across three atolls, i.e. ~2.7 MWh per atoll.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sunsafe import config  # noqa: E402
from sunsafe.energy.backup import backup_hours  # noqa: E402
from sunsafe.energy.sizing import size_system  # noqa: E402
from sunsafe.energy.solar import fetch_weather, pv_output_per_kw  # noqa: E402
from sunsafe.load_profiles import village_profile  # noqa: E402

LAT, LON = -9.38, -171.24          # Fakaofo
CHEMISTRY = "lead_acid"
TARGET = 0.95
DAILY_LOADS_KWH = [600, 720]
DIESEL_PRICE = 1.10                # USD/litre, placeholder; only affects the cost trade-off

REAL_PV_KW = (265, 365)
SOURCE_A_BATT_KWH = (1100, 1600)
SOURCE_B_BATT_KWH = 8000 / 3


def _vs(value, lo, hi=None):
    """Describe value relative to a range (or a single number)."""
    if hi is None:
        return f"{value / lo:.2f}x"
    if value < lo:
        return f"{value / lo:.2f}x of low end"
    if value > hi:
        return f"{value / hi:.2f}x of high end"
    return "within range"


def main():
    weather = fetch_weather(LAT, LON)
    pv_per_kw = pv_output_per_kw(weather)
    print(f"Fakaofo ({LAT}, {LON}) | weather source: {weather.attrs.get('source')} | "
          f"PV yield {pv_per_kw.sum():.0f} kWh/kWp/yr | {CHEMISTRY}, target {TARGET:.0%}\n")

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


if __name__ == "__main__":
    main()
