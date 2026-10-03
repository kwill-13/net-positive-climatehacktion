"""
All model assumptions in one place.

Every number here is an assumption. Each has a comment with its unit and its source,
or a TODO where it is still a placeholder. Values marked "sourced" come from the list below.
Chemistry keys match `Inputs.battery_chemistry` in interface.py: "lithium", "lead_acid".

SOURCES
  [SPC16]   SPC 2016, "Zoom: Tokelau leads world in renewable energy" (fuel use and cost)
            https://www.spc.int/updates/blog/2016/11/zoom-tokelau-leads-world-in-renewable-energy
  [MAT]     Matauala, Climate change (Tokelau fuel cost)
            https://www.matauala.org.nz/climate-change
  [ADB-NRU] ADB, Nauru project economic analysis (generator O&M, solar O&M)
            https://www.adb.org/sites/default/files/linked-documents/49450-009-ea.pdf
  [NREL-DEG] Jordan & Kurtz, NREL, "Photovoltaic Degradation Rates - An Analytical Review"
            https://docs.nlr.gov/docs/fy12osti/51664.pdf
  [RNZ20]   RNZ 2020, "New solar system for Tokelau" (lead-acid replaced by Li-ion; NZD 9M)
            https://www.rnz.co.nz/international/pacific-news/410925/new-solar-system-for-tokelau
  [NREL-ATB] NREL Annual Technology Baseline 2024, utility-scale battery storage
            https://atb.nlr.gov/electricity/2024/utility-scale_battery_storage
  [ADB-TON] ADB, Tonga Renewable Energy Project economic analysis (6% discount rate)
            https://www.adb.org/sites/default/files/linked-documents/49450-012-ea.pdf
  [APIA]    Apia monthly diesel retail prices 2026 (Samoa News Hub, Samoa Global News,
            Samoa Observer, Talamua)
            https://samoanewshub.com/2026/01/01/fuel-prices-increase-across-samoa-for-january-2026/
            https://samoaglobalnews.com/samoa-fuel-prices-rise-across-all-products-from-april-1/
            https://www.samoaobserver.ws/category/samoa/120219
            https://talamua.com/?p=61207
            https://talamua.com/?p=62013
            https://talamua.com/?p=62357
  [FX-WST]  WST/USD 0.3635 on 3 Oct 2026
            https://www.currency.me.uk/convert/wst/usd
  [POISED]  CIF / ADB POISED case study, Maldives outer islands (0.28-0.37 L/kWh)
            https://www.cif.org/sites/cif_enc/files/knowledge-documents/66436_191219_maldives_case_study_v7s.pdf
  [WB-BESS] World Bank, regional BESS policy and program for the Pacific Island Countries
            (Li-ion life 10-15 yrs)
            https://www.wbgkggtf.org/sites/kggtf/files/2023-02/COCF_Final%20Report_Development%20of%20regional%20Battery%20Energy%20Storage%20System%20(BESS)%20Policy%20and%20Program%20for%20the%20Pacific%20Island%20Countries%20(PICs).pdf
  [BNEF25]  BNEF / Ember 2025 storage prices (USD 117/kWh turnkey; -31% in 2025), via Energy-Storage.News
            https://www.energy-storage.news/battery-storage-system-prices-continue-to-fall-sharply-bnef-and-ember-reports-find/
  [HOMER]   HOMER Energy, diesel O&M costs (~USD 0.02/kWh, low case)
            https://homerenergy.com/docs/knowledgebase/article/diesel-om-costs/
  [ITP13]   IT Power (2013), Tokelau Renewable Energy Project Review (Financial + Technical), for
            NZ MFAT. Cite by page; the PDF is marked "Confidential - client only", so do not commit it.
            https://www.pcreee.org/publication/tokelau-renewable-energy-project-review
  [IRENA13] IRENA (2013), Pacific Lighthouses: Tokelau (per-atoll PV/battery, 2008 demand)
            https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2013/Sep/Tokelau.pdf
  [OFX]     OFX yearly average exchange rates (NZD/USD 2012 = 0.810)
            https://www.ofx.com/en-nz/forex-news/historical-exchange-rates/yearly-average-rates/
  [CT13]    CleanTechnica 2013, Tokelau 100% solar: NZ advance NZD 7M (total project NZD 8.5M
            per [MAT]), ~9-year simple payback (validation only; see SOURCES.md)
            https://cleantechnica.com/2013/10/06/an-island-tokelau-powered-100-by-solar-energy/
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
        "life_years": 12,        # years. Sourced: WB-BESS 10-15 yrs; NREL-ATB 15 yrs
    },
    "lead_acid": {
        "min_soc": 0.5,          # 0-1, 50% DoD is the usual limit for acceptable life
        "round_trip_eff": 0.80,  # 0-1
        "life_years": 8,         # years. Sourced: Tokelau's 2012 lead-acid bank was replaced
                                 # with Li-ion in 2020 [RNZ20]; ITP's tariff model also uses 8 yrs [ITP13 p.27]
    },
}

# Capacity lost per year, compounding: capacity_y = nominal x (1 - fade)^(y - 1).
# Used by sunsafe/lifecycle/degradation.py. PLACEHOLDERS until sourced.
BATTERY_ANNUAL_FADE = {
    "lithium": 0.025,            # 0-1 per year. TODO: source
    # 0-1 per year. Derived: Exide Classic OPzS design life 20 yrs at 20 degC to 80% C10 (~1.1%/yr); Tokelau
    # battery rooms 31-34 degC [ITP13 pp.58,88,117] age faster; the banks were replaced after ~8 yrs [RNZ20],
    # and reaching 80% by year 8 implies ~2.8%/yr. 0.06 (the previous placeholder) kept as a pessimistic case.
    "lead_acid": 0.03,
}

# ------------------------------------------------------------------ demand ----

DEMAND_GROWTH_PER_YEAR = 0.09    # 0-1 per year, compounding. Sourced for Tokelau: 2008->2013 demand grew
                                 # ~8-11%/yr (553-601 -> 837-899 kWh/day) [IRENA13 Table 1][ITP13 pp.14-19];
                                 # ITP 2019 reported "9% per year historically" [SOURCES.md item 7].
                                 # Inputs.demand_growth_per_year (interface default 0.03) overrides this in
                                 # run_sunsafe; the app and Tokelau script pass this value.

PV_ANNUAL_DERATE = 0.005         # 0-1 per year, compounding. Sourced: median ~0.5%/yr [NREL-DEG]

# ----------------------------------------------------------------- diesel ----

DIESEL_KWH_PER_LITRE = 3.0       # kWh electric per litre. Sourced: Maldives outer islands
                                 # 0.28-0.37 L/kWh = 2.7-3.6 kWh/L [POISED]; ITP assumed 3 kWh/L for Tokelau
                                 # [ITP13 p.28]

# Delivered diesel price for Tokelau (default), USD/litre. Derived from sources (SOURCES.md item 5, P1):
#   mean Apia retail diesel Mar-Oct 2026 = 4.115 WST/L [APIA] x 0.3635 USD/WST [FX-WST] = USD 1.50/L,
#   x 1.25 freight and handling to Tokelau (2013: landed NZD 1.50 vs Samoa wholesale NZD 1.20
#   [ITP13 pp.28-29]) = USD 1.87/L. Using Apia retail (not wholesale) as the base makes this slightly high.
#   tests/test_config.py checks this derivation against FUEL_SHOCK_APIA_WST_PER_L.
TOKELAU_DIESEL_PRICE_USD_PER_L = 1.87
TOKELAU_DIESEL_FREIGHT_MARKUP = 1.50 / 1.20   # landed / Samoa wholesale, 2013 [ITP13 pp.28-29]
# Scenarios for reports:
#   low  = 2013 landed price used by ITP, NZD 1.50/L x 0.81 = USD 1.22/L [ITP13][OFX]
#   high = USD 2.70/L, the earlier derivation: NZD 0.8-1M+/yr fuel spend [MAT][CT13] / ~200 L/day per
#          atoll. It overstates diesel because that spend covers ALL fuel imports (petrol, kerosene, LPG).
TOKELAU_DIESEL_PRICE_LOW_USD_PER_L = 1.22
TOKELAU_DIESEL_PRICE_HIGH_USD_PER_L = 2.70
# Apia retail 2026 for reference: USD 1.17 (Jan), 1.93 (Jun peak), 1.61 (Oct) [APIA].
NZD_TO_USD_2012 = 0.80           # USD per NZD, 2012. Sourced: 2012 average 0.810 [OFX]; 0.82 on
                                 # 23 Oct 2012 [IRENA13]

# Generator O&M per kWh generated, applied to diesel-only AND hybrid generator output.
# Sourced: USD 0.04/kWh [ADB-NRU]; HOMER default ~0.02 is the low case [HOMER].
GEN_OM_USD_PER_KWH = 0.04
GEN_OM_USD_PER_KWH_LOW = 0.02

# ---------------------------------------------------------------- costs ------
# Installed costs, USD.

# USD/kWp installed (PV + inverters + BOS + install). Range sourced, point estimate still uncertain:
#   low  ~2,500: Tokelau 2020 upgrade back-calculation [RNZ20] (2,500-3,300 depending on Li-ion price)
#   high ~4,000: Tokelau 2012, (USD 6.95M [IRENA13] - ~USD 3.0-3.2M batteries [ITP13]) / 891 kWp = 4,200-4,400
PV_COST_USD_PER_KW = 2500.0
PV_COST_USD_PER_KW_HIGH = 4000.0      # high case for reports (SOURCES.md P2)
BATTERY_COST_USD_PER_KWH = {
    # USD/kWh nominal installed. Sourced: Tokelau 2020 back-calculation [RNZ20]: NZD 9M = USD 5.7M
    # for 3 x 210 kW PV + 3 x 2 MWh Li-ion => ~USD 690/kWh if PV is USD 2,500/kW. Global turnkey
    # is USD 117/kWh [BNEF25], so remote Pacific carries a large premium.
    "lithium": 600.0,
    # USD/kWh nominal. Sourced: ITP battery replacement NZD 3.75-4.0M [ITP13 pp.27,32] for 8,602 kWh
    # nominal (C20) [IRENA13 Table 2] = NZD 436-465/kWh = USD ~353-377/kWh (2013) at [OFX] 0.81.
    "lead_acid": 350.0,
}

DISCOUNT_RATE = 0.08             # 0-1 per year, real. Sourced: ADB uses 6-9% in Pacific analyses
                                 # (9% [ADB-NRU], 6% [ADB-TON]); scripts/run_tokelau.py also reports 6%
DISCOUNT_RATE_LOW = 0.06         # sensitivity case
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

# ------------------------------------------------------ lifecycle strategy ---

PROJECT_DISCOUNT_RATE = DISCOUNT_RATE  # 0-1 per year, for 15-year NPV and the O&M sinking fund
# 0-1 per year, real; replacement price = today x (1-d)^t. Sourced, deliberately conservative:
# BNEF reports -31% in 2025 alone [BNEF25].
BATTERY_PRICE_DECLINE_PER_YEAR = 0.04
# Strategy B: battery replaced at the start of year N+1, for each N here (filtered to N+1 <= project years).
STRATEGY_REPLACEMENT_AFTER_YEARS = range(5, 13)

# ---------------------------------------------------------------- O&M -------

# USD per kWp per year. Sourced: ADB Nauru solar O&M USD 48/MWh [ADB-NRU] x ~1,490 kWh/kWp/yr
# site yield (Fakaofo, NASA POWER) = ~USD 70/kW/yr.
OM_PV_USD_PER_KW_YEAR = 70.0
# USD per kWh nominal per year. Sourced: kept at 10; NREL ATB uses 2.5% of capex/yr but that
# includes augmentation [NREL-ATB], which this model handles as fade + replacement instead.
OM_BATTERY_USD_PER_KWH_YEAR = 10.0
# Generator O&M: GEN_OM_USD_PER_KWH (diesel section). Generator capex is not counted (same genset
# stays in both the hybrid and the diesel-only case).

# -------------------------------------------------------------- fuel shock ---
# Sourced: Apia monthly diesel retail prices 2026, WST/litre [APIA] (Samoa Global News,
# Samoa Observer, Talamua). Applied as MULTIPLIERS relative to March to the site's own price,
# so the currency cancels out. For reference: 2.99-5.31 WST/L = USD 1.09-1.93/L at
# WST_TO_USD [FX-WST].
FUEL_SHOCK_APIA_WST_PER_L = [
    ("2026-03", 2.99),
    ("2026-04", 3.09),
    ("2026-05", 4.50),
    ("2026-06", 5.31),
    ("2026-07", 4.48),           # stated: "dropping from $5.31 in June to $4.48 per litre for July" [APIA]
    ("2026-08", 3.89),
    ("2026-09", 4.22),
    ("2026-10", 4.44),
]
_FUEL_SHOCK_BASE = FUEL_SHOCK_APIA_WST_PER_L[0][1]          # March 2026 = 1.00
WST_TO_USD = 0.3635              # USD per WST, 3 Oct 2026 [FX-WST]. Reference only: not used in
                                 # any calculation (fuel shock uses ratios)
FUEL_SHOCK_2026 = [(m, p / _FUEL_SHOCK_BASE) for m, p in FUEL_SHOCK_APIA_WST_PER_L]

# --------------------------------------------------------------- headroom ----
# Candidate new electric loads that could use surplus solar: (description, kWh/day). TODO: source.
CANDIDATE_NEW_LOADS = [
    ("Community freezer", 25.0),          # sourced: Nukunonu community freezer ~25 kWh/day [ITP13 p.100]
    ("Electric cooking at the school", 12.0),
    ("Charging for electric outboard motors", 15.0),
]
# Non-electric energy use (cooking fuel + outboard petrol), kWh/day thermal-equivalent.
# Per-site values keyed by a lowercase substring of Inputs.site_name; otherwise
# NON_ELECTRIC_TO_ELECTRIC_RATIO x daily electric load. ALL PLACEHOLDERS. TODO: source.
SITE_NON_ELECTRIC_KWH_PER_DAY = {
    "fakaofo": 1800.0,                # TODO: placeholder (3 x 600 kWh/day electric)
}
NON_ELECTRIC_TO_ELECTRIC_RATIO = 3.0  # TODO: placeholder (electricity ~25% of final energy)
