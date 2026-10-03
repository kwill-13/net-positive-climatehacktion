"""
Validation: size Fakaofo (Tokelau) and compare with the real 2012 installation.

Run from the repo root:  python scripts/run_tokelau.py

The model is NOT tuned to these numbers. This only reports how far apart they are.

Sections:
  1. Year-1 cost-optimal sizing at the base target.
  2. Sensitivity table: renewable target x design year (size for faded battery + grown load).
  3. 15-year forward run of the year-1 optimal system vs the real installed system.
  4. Strategy A (build big) vs B (moderate + planned replacement), and the recommended
     system's two lifecycle curves (with vs without its planned replacement).
  5. The real system's 15-year decline at battery fade 0.04 / 0.06 / 0.08, and the first
     year it drops below the target at each.
  6. Diesel price x discount rate: hybrid vs diesel-only USD/kWh, payback, breakeven price.
  7. Payback for all three atolls vs Tokelau's reported ~9-year simple payback.
Fade, PV derate and growth come from sunsafe/lifecycle/degradation.py (placeholders in config.py).
Reference figures (per atoll):
  Source A: 265-365 kWp PV, 1.1-1.6 MWh nominal lead-acid.
  Source B: ~8 MWh lead-acid across three atolls, i.e. ~2.7 MWh per atoll.
"""

import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sunsafe import config  # noqa: E402
from sunsafe.energy.backup import backup_hours  # noqa: E402
from sunsafe.energy.sizing import size_system  # noqa: E402
from sunsafe.energy.solar import fetch_weather, pv_output_per_kw  # noqa: E402
from sunsafe.interface import Inputs  # noqa: E402
from sunsafe.lifecycle import finance as fin  # noqa: E402
from sunsafe.lifecycle.projection import run_years  # noqa: E402
from sunsafe.model import run_sunsafe_detailed  # noqa: E402
from sunsafe.load_profiles import village_profile  # noqa: E402

LAT, LON = -9.38, -171.24          # Fakaofo
CHEMISTRY = "lead_acid"
TARGET = 0.95
DAILY_LOADS_KWH = [600, 720]
DIESEL_PRICE = config.TOKELAU_DIESEL_PRICE_USD_PER_L   # USD/litre, sourced (see config.py)

REAL_PV_KW = (265, 365)
SOURCE_A_BATT_KWH = (1100, 1600)
SOURCE_B_BATT_KWH = 8000 / 3
REAL_SYSTEM = (300.0, 1350.0)      # kWp, kWh nominal lead-acid: mid-range of Source A

SENS_TARGETS = [0.95, 0.99, 1.0]
SENS_DESIGN_YEARS = [1, 8, 15]
FORWARD_YEARS = 15
FADE_RATES = [0.04, 0.06, 0.08]

PRICES_USD_PER_L = [1.10, 1.50, 2.00, 2.50, 2.70, 3.00, 3.50]
DISCOUNT_RATES = [config.DISCOUNT_RATE, config.DISCOUNT_RATE_LOW]

# The three atolls, ~200 L/day diesel each [SPC16] x 3 kWh/L = ~600 kWh/day each.
ATOLLS = [("Fakaofo", LAT, LON), ("Nukunonu", -9.17, -171.83), ("Atafu", -8.54, -172.50)]
ATOLL_DAILY_KWH = 600
# Tokelau 2012 project: NZD ~7M for all three atolls, reported ~9-year simple payback
# (CleanTechnica 2013; URL not yet supplied). Converted at config.NZD_TO_USD_2012.
TOKELAU_2012_CAPEX_NZD = 7.0e6
TOKELAU_REPORTED_PAYBACK_YEARS = 9


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
        opt_years, real_years = (run_years(pv, b, load, pv_per_kw, CHEMISTRY, FORWARD_YEARS)
                                 for pv, b in systems.values())
        for o, r in zip(opt_years, real_years):
            print(f"{o.year:>4} {o.demand_kwh_per_day:>10.0f} | {o.battery_kwh:>12.0f} "
                  f"{o.renewable_share:>9.1%} | {r.battery_kwh:>13.0f} {r.renewable_share:>10.1%}")
    print("(includes PV derate; battery never replaced)\n")


def _header(title):
    print("=" * 100)
    print(title)
    print("=" * 100)


@lru_cache(maxsize=None)
def _detailed(site, lat, lon, daily):
    """run_sunsafe_detailed for a Tokelau site at the default price (cached: ~12 s each)."""
    inputs = Inputs(site_name=site, latitude=lat, longitude=lon,
                    diesel_litres_per_day=daily / config.DIESEL_KWH_PER_LITRE,
                    diesel_price_per_litre=DIESEL_PRICE, daily_load_kwh=daily,
                    renewable_target=TARGET, battery_chemistry=CHEMISTRY,
                    project_years=FORWARD_YEARS)
    return run_sunsafe_detailed(inputs)


def _econ(design, price, rate=config.DISCOUNT_RATE):
    """Economics of a Strategy (fixed design) at a diesel price and discount rate."""
    return fin.economics(design.capex_usd, design.annual_om_usd,
                         [y.load_kwh for y in design.years], [y.gen_kwh for y in design.years],
                         price, design.replacement_year, design.replacement_usd, rate)


def strategy_comparison(pv_per_kw):
    """Section 4: A vs B over the project, and the recommended system's lifecycle curves."""
    _header(f"4. STRATEGY: build big vs moderate + planned replacement ({CHEMISTRY}, target "
            f"{TARGET:.0%} EVERY year, {FORWARD_YEARS} yrs, NPV at "
            f"{config.PROJECT_DISCOUNT_RATE:.0%})")
    for daily in DAILY_LOADS_KWH:
        res, comp = _detailed("Fakaofo", LAT, LON, daily)
        rec = comp.recommended
        print(f"\nDaily load {daily} kWh/day (year 1)")
        print(f"  {'strategy':<24} {'PV kWp':>7} {'batt kWh':>8} {'replace':>7} "
              f"{'15-yr NPV $':>12} {'O&M fund $/yr':>13} {'min share':>9} {'ok':>5}")
        for c in comp.candidates:
            sink = (fin.sinking_fund_deposit(c.replacement_usd, c.replacement_year - 1)
                    if c.replacement_year else 0.0)
            mark = "  <- recommended" if c is rec else ""
            print(f"  {c.name:<24} {c.pv_kw:>7.0f} {c.battery_kwh:>8.0f} "
                  f"{(c.replacement_year or '-'):>7} {c.npv_usd:>12,.0f} "
                  f"{c.annual_om_usd + sink:>13,.0f} {c.min_share:>9.1%} "
                  f"{str(c.meets_target_every_year):>5}{mark}")
        y1 = comp.year1_optimal
        print(f"  (report only) year-1 cost-optimal: {y1.pv_kw:.0f} kWp / {y1.battery_kwh:.0f} kWh")
        f = res.finance
        print(f"  Recommended: capex ${res.sizing.capex_usd:,.0f} | hybrid ${f.cost_per_kwh_hybrid_usd}"
              f"/kWh vs diesel ${f.cost_per_kwh_diesel_usd}/kWh | payback {f.payback_years} yrs")
        print(f"\n  Lifecycle curves for the recommended system ({rec.name}):")
        print(f"  {'year':>4} {'demand kWh/d':>12} | {'with planned replacement':>24} | "
              f"{'never replaced':>14} {'usable batt kWh':>15}")
        for ly in res.lifecycle:
            print(f"  {ly.year:>4} {ly.demand_kwh_per_day:>12.0f} | {ly.share_funded_year_15:>24.1%} | "
                  f"{ly.share_funded_day_one:>14.1%} {ly.battery_capacity_kwh:>15.0f}")
    print()


def fade_sensitivity(pv_per_kw):
    """Section 5: the real system's 15-year decline at several battery fade rates."""
    pv, batt = REAL_SYSTEM
    _header(f"5. FADE SENSITIVITY: real system {pv:.0f} kWp / {batt:.0f} kWh {CHEMISTRY}, never "
            f"replaced (config default fade {config.BATTERY_ANNUAL_FADE[CHEMISTRY]})")
    for daily in DAILY_LOADS_KWH:
        load = village_profile(daily)
        runs = {fade: run_years(pv, batt, load, pv_per_kw, CHEMISTRY, FORWARD_YEARS, fade=fade)
                for fade in FADE_RATES}
        print(f"\nDaily load {daily} kWh/day (year 1): renewable share by year")
        print(f"{'year':>4} | " + " ".join(f"{f'fade {fade:.2f}':>10}" for fade in FADE_RATES))
        for i in range(FORWARD_YEARS):
            print(f"{i + 1:>4} | " + " ".join(f"{runs[fade][i].renewable_share:>10.1%}"
                                              for fade in FADE_RATES))
        print(f"First year below {TARGET:.0%}:")
        for fade, years in runs.items():
            below = next((y.year for y in years if y.renewable_share < TARGET - 1e-9), None)
            print(f"  fade {fade:.2f}: " + (f"year {below}" if below else
                                             f"never within {FORWARD_YEARS} years"))
    print()


def price_sensitivity():
    """Section 6: fixed recommended design, priced at several diesel prices and rates."""
    _header(f"6. DIESEL PRICE x DISCOUNT RATE (design fixed at the recommendation for "
            f"USD {DIESEL_PRICE:.2f}/L; generator O&M USD {config.GEN_OM_USD_PER_KWH}/kWh)")
    for daily in DAILY_LOADS_KWH:
        _, comp = _detailed("Fakaofo", LAT, LON, daily)
        rec = comp.recommended
        print(f"\nDaily load {daily} kWh/day: {rec.name}, {rec.pv_kw:.0f} kWp / "
              f"{rec.battery_kwh:.0f} kWh, capex ${rec.capex_usd:,.0f}")
        heads = [f"{k} @{r:.0%}" for r in DISCOUNT_RATES for k in ("hybrid", "diesel")]
        print(f"  {'USD/L':>6} | " + " ".join(f"{h:>11}" for h in heads)
              + f" | {'payback yrs':>11}")
        for p in PRICES_USD_PER_L:
            es = [_econ(rec, p, r) for r in DISCOUNT_RATES]
            vals = [v for e in es for v in (e.cost_per_kwh_hybrid_usd, e.cost_per_kwh_diesel_usd)]
            pb = es[0].payback_years
            print(f"  {p:>6.2f} | " + " ".join(f"{v:>11.3f}" for v in vals)
                  + f" | {('never' if pb == float('inf') else f'{pb:.1f}'):>11}")
        for r in DISCOUNT_RATES:
            # Both levelised costs are linear in diesel price, so solve the crossing exactly.
            lo, hi = _econ(rec, 1.0, r), _econ(rec, 2.0, r)
            gap_lo = lo.cost_per_kwh_hybrid_usd - lo.cost_per_kwh_diesel_usd
            gap_hi = hi.cost_per_kwh_hybrid_usd - hi.cost_per_kwh_diesel_usd
            slope = gap_hi - gap_lo
            be = 1.0 - gap_lo / slope if slope < 0 else float("inf")
            print(f"  Breakeven diesel price at {r:.0%}: USD {be:.2f}/L "
                  f"(hybrid cheaper per kWh above this)")
    print()


def atoll_payback():
    """Section 7: model payback for all three atolls vs the reported ~9 years."""
    real_capex_usd = TOKELAU_2012_CAPEX_NZD * config.NZD_TO_USD_2012
    _header(f"7. THREE ATOLLS: simple payback at USD {DIESEL_PRICE:.2f}/L, {ATOLL_DAILY_KWH} "
            f"kWh/day each, vs reported ~{TOKELAU_REPORTED_PAYBACK_YEARS} yrs "
            f"(NZD {TOKELAU_2012_CAPEX_NZD / 1e6:.0f}M = USD {real_capex_usd / 1e6:.1f}M)")
    pv_r, batt_r = REAL_SYSTEM
    print(f"{'atoll':<10} | {'recommended design':>20} {'capex $':>11} {'payback':>8} | "
          f"{'real 300/1350, saving $/yr':>26} {'payback @ real capex':>21}")
    totals = {"rec_capex": 0.0, "rec_net": 0.0, "real_net": 0.0}
    for name, lat, lon in ATOLLS:
        _, comp = _detailed(name, lat, lon, ATOLL_DAILY_KWH)
        rec = comp.recommended
        e_rec = _econ(rec, DIESEL_PRICE)
        pv_per_kw = pv_output_per_kw(fetch_weather(lat, lon))
        real_years = run_years(pv_r, batt_r, village_profile(ATOLL_DAILY_KWH), pv_per_kw,
                               CHEMISTRY, FORWARD_YEARS)
        om_real = fin.annual_om_usd(pv_r, batt_r)
        e_real = fin.economics(real_capex_usd / 3, om_real, [y.load_kwh for y in real_years],
                               [y.gen_kwh for y in real_years], DIESEL_PRICE)
        totals["rec_capex"] += rec.capex_usd
        totals["rec_net"] += e_rec.annual_saving_year1_usd - rec.annual_om_usd
        totals["real_net"] += e_real.annual_saving_year1_usd - om_real
        print(f"{name:<10} | {f'{rec.pv_kw:.0f} kWp / {rec.battery_kwh:.0f} kWh':>20} "
              f"{rec.capex_usd:>11,.0f} {e_rec.payback_years:>7.1f}y | "
              f"{e_real.annual_saving_year1_usd:>26,.0f} {e_real.payback_years:>20.1f}y")
    print(f"{'ALL THREE':<10} | {'':>20} {totals['rec_capex']:>11,.0f} "
          f"{totals['rec_capex'] / totals['rec_net']:>7.1f}y | {'':>26} "
          f"{real_capex_usd / totals['real_net']:>20.1f}y")
    print(f"Reported: ~{TOKELAU_REPORTED_PAYBACK_YEARS} years. 'Payback @ real capex' uses the actual "
          f"project cost and the model's year-1 fuel + generator O&M saving minus solar O&M.")
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
    strategy_comparison(pv_per_kw)
    fade_sensitivity(pv_per_kw)
    price_sensitivity()
    atoll_payback()


if __name__ == "__main__":
    main()
