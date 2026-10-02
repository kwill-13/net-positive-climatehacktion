"""
All model assumptions in one place.

Every number here is an assumption. Each has a comment with its unit and,
where it is still a placeholder, a TODO to source it before the demo.
Chemistry keys match `Inputs.battery_chemistry` in interface.py: "lithium", "lead_acid".
"""

from pathlib import Path

# ------------------------------------------------------------------ paths ----

REPO_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = REPO_ROOT / "data" / "cache"      # NASA POWER responses (gitignored)

# --------------------------------------------------------- solar resource ----

NASA_POWER_HOURLY_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"
NASA_POWER_PARAMETERS = "ALLSKY_SFC_SW_DWN,T2M"  # GHI (W/m2), air temp at 2 m (degC)
NASA_POWER_COMMUNITY = "RE"                      # renewable-energy community
NASA_POWER_TIME_STANDARD = "LST"                 # local solar time, so noon = solar noon
NASA_POWER_TIMEOUT_S = 60                        # seconds per request
WEATHER_YEAR = 2023                              # default reference year

HOURS_PER_YEAR = 8760                            # Feb 29 is always dropped

# ------------------------------------------------------------ PV electrics ---

PV_DERATE = 0.80                 # 0-1, wiring, inverter, soiling, mismatch losses combined
PV_TEMP_COEFF_PER_C = 0.004      # 1/degC, power loss per degC of cell temp above 25 degC
PV_CELL_TEMP_RISE_PER_W_M2 = 0.03  # degC per W/m2 of GHI (cell_temp = air + 0.03 * GHI)
PV_STC_IRRADIANCE_W_M2 = 1000.0  # W/m2, standard test condition irradiance
PV_STC_CELL_TEMP_C = 25.0        # degC, standard test condition cell temperature

# ---------------------------------------------------------------- battery ----
# min_soc: lowest allowed state of charge (0-1 of nominal capacity) to protect life.
# round_trip_eff: AC-to-AC; split equally into charge and discharge (sqrt each way).
# life_years: calendar replacement interval used for annualising capital cost.

BATTERY = {
    "lithium": {
        "min_soc": 0.2,          # 0-1, typical LFP depth-of-discharge limit (80% DoD)
        "round_trip_eff": 0.90,  # 0-1
        "life_years": 12,        # years. TODO: source (LFP in tropical climate, ~1 cycle/day)
    },
    "lead_acid": {
        "min_soc": 0.5,          # 0-1, 50% DoD is the usual limit for acceptable life
        "round_trip_eff": 0.80,  # 0-1
        "life_years": 6,         # years. TODO: source (Tokelau replaced its lead-acid bank ~2020)
    },
}

# Capacity lost per year, compounding: capacity_y = nominal x (1 - fade)^(y - 1).
# PLACEHOLDERS for design-year sizing; the lifecycle teammate owns the real fade model.
BATTERY_ANNUAL_FADE = {
    "lithium": 0.025,            # 0-1 per year. TODO: source
    "lead_acid": 0.06,           # 0-1 per year. TODO: source
}

# ------------------------------------------------------------------ demand ----

DEMAND_GROWTH_PER_YEAR = 0.03    # 0-1 per year, compounding; same default as Inputs.demand_growth_per_year

# ----------------------------------------------------------------- diesel ----

DIESEL_KWH_PER_LITRE = 3.0       # kWh electric per litre; typical small island gensets 2.8-3.5

# ---------------------------------------------------------------- costs ------
# Installed costs, USD. ALL PLACEHOLDERS until sourced.

PV_COST_USD_PER_KW = 2500.0           # USD/kWp installed. TODO: source (Pacific remote-island projects)
BATTERY_COST_USD_PER_KWH = {
    "lithium": 600.0,                 # USD/kWh nominal installed. TODO: source
    "lead_acid": 350.0,               # USD/kWh nominal installed. TODO: source
}

DISCOUNT_RATE = 0.08             # 0-1 per year, real, used in capital recovery factor
PV_LIFE_YEARS = 20               # years, PV array + inverters (simplification)

# ----------------------------------------------------------------- sizing ----
# Search bounds, relative to the site's load.

SIZING_PV_MIN_X_AVG_LOAD = 0.5        # PV kW from 0.5 x average load (kW) ...
SIZING_PV_MAX_X_AVG_LOAD = 15.0       # ... up to 15 x average load (kW). Brief said 6x, but at
                                      # ~4 kWh/kWp/day 6x only just covers daily load before battery
                                      # losses, so >90% targets were infeasible. Tokelau's real
                                      # arrays are ~10-15x average load.
SIZING_BATTERY_MAX_DAYS = 3.0         # battery kWh from 0 up to 3 days of daily load
SIZING_COARSE_STEPS_PV = 20           # coarse grid points for PV
SIZING_COARSE_STEPS_BATTERY = 13      # coarse grid points for battery
SIZING_REFINE_STEPS = 9               # points per axis in the refinement pass
