import re
from pathlib import Path

import streamlit as st
from components.layout import init, placeholder_notes, run_validation_case, usable_fraction
from utils.formatting import battery, short_strategy
from sunsafe import config

init("How we know it works", "Is the engine behind the plan trustworthy? We checked it against "
     "Tokelau, which went from diesel to ~100% solar in 2012.", step=2)
s = st.session_state
REPO = "https://github.com/kwill-13/net-positive-climatehacktion/blob/main"
ROOT = Path(__file__).resolve().parents[2]

# ------------------------------------------------------- Tokelau validation ---
st.subheader("1. Tokelau: the model vs the real systems")
st.markdown(
    "Tokelau's three atolls each got a solar + lead-acid battery mini-grid in 2012, demand then grew "
    "about 9% a year, and the systems were upgraded with new solar and lithium batteries in 2020. "
    "SunSafe was **not tuned** to these numbers; we report the gaps.")
# The validation case (scripts/run_tokelau.py inputs) through the current engine, all four strategies.
# Cached: a few seconds on the first visit, instant after. Same numbers as the script's section 4.
REAL_2012 = (330, 3379)                                          # Fakaofo, kWp / kWh nominal [IRENA 2013]
REAL_2020 = dict(pv_kw=210, battery_kwh=2000, after_years=8)     # +210 kWp, ~2 MWh Li-ion [RNZ 2020]
with st.spinner("Running the validation case through the engine (first visit only)..."):
    val = run_validation_case()
if val is None:
    st.error(f"The validation case could not run: {s.model_error}")
else:
    vr, vu = val["results"], usable_fraction(val)
    first, *later = vr.plan_stages
    pv_r, nom_r = REAL_2012
    usable_r = nom_r * 0.5                                       # lead-acid designed for 50% depth of discharge
    big = next(x for x in val["strategies"] if x["letter"] == "A")
    rec = next(x for x in val["strategies"] if x["recommended"])
    if later:
        u = later[0]
        up_model = (f"Year {u.year} (after {u.year - 1} yrs): +{u.pv_added_kw:,.0f} kWp, new "
                    f"{battery(u.battery_installed_kwh, vu)}: PV {u.pv_added_kw / REAL_2020['pv_kw']:.2f}x, battery "
                    f"{u.battery_installed_kwh / REAL_2020['battery_kwh']:.2f}x")
        gap = (u.year - 1) - REAL_2020["after_years"]
        up_meaning = ("Same timing as the real upgrade" if gap == 0 else
                      f"{abs(gap)} yr{'s' if abs(gap) > 1 else ''} {'earlier' if gap < 0 else 'later'} than the real "
                      "upgrade: the cheapest plan builds smaller and upgrades sooner") + "; similar size added"
    else:
        up_model, up_meaning = "No upgrade in the plan", "The real system was upgraded after ~8 years"
    rows = [
        ("First build", f"{pv_r} kWp / {battery(nom_r, 0.5)} (2012, IRENA 2013)",
         f"{first.pv_added_kw:,.0f} kWp / {battery(first.battery_installed_kwh, vu)}: PV "
         f"{first.pv_added_kw / pv_r:.2f}x, battery {first.battery_installed_kwh / nom_r:.2f}x",
         "PV close; battery smaller because the plan adds a new battery at each upgrade instead of oversizing"),
        ("First upgrade", "+210 kWp and ~2 MWh Li-ion after ~8 years (2020, RNZ)", up_model, up_meaning),
    ]
    for u in later[1:]:
        rows.append((f"Later upgrade", "No later upgrade on record",
                     f"Year {u.year}: +{u.pv_added_kw:,.0f} kWp, new {battery(u.battery_installed_kwh, vu)}",
                     "Planned; nothing real to compare yet"))
    rows += [
        ("When the real system falls below 95%", "Upgraded after ~8 years (2020)",
         "The real 2012 system, modelled: below 95% in year 9", "Matches the real need to upgrade within a year"),
        ("Measured solar share, Nov 2012-May 2013", "Atafu 92.5%, Nukunonu 93.5%",
         "Atafu 96.4-97.1%, Nukunonu 94.8-96.1%",
         "Model is 1-4 points optimistic (outages, shading, generator charging not modelled)"),
        ("15-year cost (NPV, 8%)", "Not reported",
         # "USD", not "$": two $ signs in one cell render as a LaTeX formula
         f"{short_strategy(val['rec_name'])}: USD {rec['npv'] / 1e6:,.2f}M vs USD {big['npv'] / 1e6:,.2f}M building big",
         f"{1 - rec['npv'] / big['npv']:.0%} cheaper than sizing for year 15 on day one"),
    ]
    st.table({"Check": [r[0] for r in rows], "Real system": [r[1] for r in rows],
              "SunSafe": [r[2] for r in rows], "What it means": [r[3] for r in rows]})
st.caption("Validation case: Fakaofo, 600 kWh/day, lead-acid, 95% renewable every year, USD 1.87/L, constant "
           "9%/yr growth, 15 years (same as `python scripts/run_tokelau.py`). The \"falls below 95%\" and measured solar "
           "share checks use the real system, so they do not depend on the plan. Sizes: IRENA (2013) Table 2; measured solar share: IT Power (2013); 2020 upgrade: RNZ (2020). "
           "See SOURCES.md.")

# Live comparison when the current plan is for a Tokelau atoll.
REAL = {"fakaofo": (330, 3379), "atafu": (297, 2765), "nukunonu": (264, 2458)}   # kWp, kWh nominal
REAL_USABLE_FRACTION = 0.5   # lead-acid banks designed for 50% depth of discharge
plan = s.plan
if plan:
    r = plan["results"]
    i, z = r.inputs, r.sizing
    atoll = next((a for a in REAL if a in i.site_name.lower()), None)
    if atoll:
        pv_real, nom_real = REAL[atoll]
        usable_model = z.battery_kwh * (1 - config.BATTERY[i.battery_chemistry]["min_soc"])
        usable_real = nom_real * REAL_USABLE_FRACTION
        ratio = lambda m, ref: f"{m / ref:.2f}x"
        st.markdown(f"**Your current plan vs {atoll.title()}'s real 2012 install**")
        st.table({"": ["Solar (kWp)", "Battery, nominal (kWh)", "Battery, usable (kWh)"],
                  "Your plan, first build": [f"{z.pv_kw:,.0f}", f"{z.battery_kwh:,.0f}", f"{usable_model:,.0f}"],
                  f"Real 2012, {atoll.title()}": [f"{pv_real:,}", f"{nom_real:,}", f"{usable_real:,.0f}"],
                  "Plan / real": [ratio(z.pv_kw, pv_real), ratio(z.battery_kwh, nom_real),
                                  ratio(usable_model, usable_real)]})
        daily = i.daily_load_kwh if i.daily_load_kwh is not None else i.diesel_litres_per_day * config.DIESEL_KWH_PER_LITRE
        diffs = []
        if i.battery_chemistry != "lead_acid":
            diffs.append("battery type (the real system used lead-acid)")
        if abs(i.renewable_target - 0.95) > 1e-9:
            diffs.append(f"renewable target ({i.renewable_target:.0%}; validation uses 95%)")
        if not 540 <= daily <= 660:
            diffs.append(f"daily demand ({daily:,.0f} kWh/day; validation uses ~600)")
        if diffs:
            st.warning("Not like-for-like: your inputs differ from the validation case in " + "; ".join(diffs) + ".")
        st.caption("Your plan uses your growth setting and all four strategies, so it can differ from the "
                   "validation case above.")
    else:
        st.info("Your current plan is a planning estimate for a site without a reference system. "
                "The engine is checked against Tokelau's measured performance above.")

# --------------------------------------------------------------- sensitivity ---
st.subheader("2. What changes the answer")
sens = (ROOT / "docs" / "sensitivity.md")
if sens.exists():
    text = sens.read_text()
    findings = re.search(r"## Findings\n(.*?)\n## ", text, re.S)
    st.markdown("Fakaofo, 15 years: growth, O&M and who pays (from `docs/sensitivity.md`).")
    if findings:
        st.markdown(findings.group(1))
    with st.expander("Full sensitivity tables"):
        body = text.split("## Findings", 1)[-1]
        st.markdown(body[body.find("## 1."):] if "## 1." in body else body)
else:
    st.info("docs/sensitivity.md not found.")

# ------------------------------------------------------------------- sources ---
st.subheader("3. Sources")
st.markdown(f"""
- **Solar resource:** NASA POWER hourly irradiance and temperature for the chosen coordinates.
- **Tokelau systems and performance:** IRENA (2013) *Tokelau* case study (system sizes); IT Power (2013)
  project review (measured solar share; solar O&M NZD 12,000/yr per atoll); RNZ (2020) on the lithium upgrade.
- **Demand growth 9%/yr:** Tokelau 2008-2013 measured demand.
- **Diesel price:** Apia 2026 monthly retail prices, with Tokelau freight from IT Power (2013).
- **Costs:** battery costs back-calculated from Tokelau's 2012 and 2020 projects; PV capex is a placeholder
  within a sourced range (USD 2,500-4,000/kW); solar O&M from ADB (Nauru).
- Every figure with its page and status: [SOURCES.md]({REPO}/SOURCES.md). Model inputs with source
  tags: [sunsafe/config.py]({REPO}/sunsafe/config.py).
""")

# -------------------------------------------------------------- placeholders ---
st.subheader("4. Still placeholders")
st.markdown("These assumptions are not yet sourced. Treat results that depend on them as estimates.")
for note in placeholder_notes():
    st.markdown(f"- {note}")
st.markdown("- The O&M fund saves only toward the first upgrade; later upgrades need their own funding.")
