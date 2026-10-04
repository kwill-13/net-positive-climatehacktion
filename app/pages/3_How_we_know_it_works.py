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
st.table({
    "Check": ["Sizing: Fakaofo first build",
              "Timing: when the real system falls below 95%",
              "Upgrade size",
              "Measured solar share, Nov 2012-May 2013"],
    "Real system": ["330 kWp / 3,379 kWh nominal (IRENA 2013)",
                    "Upgraded after ~8 years (2020)",
                    "+210 kWp and ~2 MWh lithium (2020)",
                    "Atafu 92.5%, Nukunonu 93.5%"],
    "SunSafe": ["363 kWp / 1,612 kWh: PV 1.10x, battery 0.48x",
                "Drops below 95% in year 9 (600 kWh/day, 9%/yr growth)",
                "Year 9: +332 kWp and a new 2,858 kWh battery",
                "Atafu 96.4-97.1%, Nukunonu 94.8-96.1%"],
    "What it means": ["PV close; battery smaller because the plan upgrades later instead of oversizing",
                      "Upgrade timing matches reality within a year",
                      "Same order of magnitude and the same staged pattern",
                      "Model is 1-4 points optimistic (outages, shading, generator charging not modelled)"],
})
st.caption("Validation case: Fakaofo, 600 kWh/day, lead-acid, 95% target, USD 1.87/L, constant 9%/yr growth, "
           "strategies A-C (`python scripts/run_tokelau.py`). Sizes: IRENA (2013) Table 2; measured solar share "
           "and 2020 upgrade: IT Power (2013), RNZ (2020). See SOURCES.md.")

# Same validation inputs through the current engine (strategies A-D), cached: a few seconds on the first visit.
# Published column = scripts/run_tokelau.py section 4 (A-C only), fixed so the published numbers stay as reported.
with st.spinner("Running the validation inputs through the current engine (first visit only)..."):
    val = run_validation_case()
if val:
    vr, vu = val["results"], usable_fraction(val)
    later = vr.plan_stages[1:]
    best = {x["letter"]: x for x in val["strategies"]}
    rec_npv = next(x["npv"] for x in val["strategies"] if x["recommended"])
    upgrades = "; ".join(f"yr {u.year}: +{u.pv_added_kw:,.0f} kWp, new {battery(u.battery_installed_kwh, vu)}"
                         for u in later) or "none"
    st.markdown("**Same inputs, current engine.** The table above is the published A-C validation; the right-hand "
                "column runs the same inputs through today's engine with all four strategies.")
    st.table({
        "": ["Recommended", "First build", "Upgrades", "15-year cost (NPV, 8%)"],
        "Published (strategies A-C)": ["C: expand in year 9", f"363 kWp + {battery(1612, 0.5)}",
                                       f"yr 9: +332 kWp, new {battery(2858, 0.5)}", "$2.80M"],
        "Current engine (strategies A-D)": [short_strategy(val["rec_name"]),
                                            f"{vr.sizing.pv_kw:,.0f} kWp + {battery(vr.sizing.battery_kwh, vu)}",
                                            upgrades, f"${rec_npv / 1e6:,.2f}M"],
    })
    c_npv = best.get("C", {}).get("npv")
    st.caption("Why they differ: the published check compares three strategies (A build big, B replace once, "
               "C expand once); the current engine adds D, expanding in stages, which finds a cheaper plan for "
               "these inputs"
               + (f" (best C here: ${c_npv / 1e6:,.2f}M, matching the published figure)." if c_npv else ".")
               + " The sizing and timing checks above use the published A-C result.")

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
        body = body[body.find("## 1."):] if "## 1." in body else body
        # 1.37 is not the app's low scenario (1.22, 2013 landed): say where it comes from.
        st.markdown(body.replace("| 1.37 |", "| 1.37 (pre-shock 2026 Apia price x1.25 freight) |"))
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
