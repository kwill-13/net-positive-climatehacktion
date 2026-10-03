import streamlit as st
from components.layout import init, card, require_results, show_recommendation
from utils.formatting import money, pct
from sunsafe import config

init("System Design", "What should we build?", step=1)
r = require_results()
z, last, n = r.sizing, r.lifecycle[-1], r.inputs.project_years
show_recommendation(r)
c = st.columns(4)
with c[0]: card("Solar", f"{z.pv_kw:,.0f} kW")
with c[1]: card("Battery", f"{z.battery_kwh:,.0f} kWh")
with c[2]: card("Estimated cost", money(z.capex_usd))
with c[3]: card("Renewable share (yr 1)", pct(z.renewable_share_year1))
c = st.columns(3)
with c[0]: card("Backup hours (critical load)", f"{r.backup_hours:,.0f} h")
with c[1]: card("Diesel avoided (yr 1)", f"{z.diesel_litres_avoided_year1:,.0f} L")
with c[2]: card(f"Renewable share (yr {last.year})", pct(last.share_funded_year_15))
st.caption(f"Year 1 can sit above the target because the design is sized to keep meeting it in every year, through year {n}.")

st.subheader("Model validation")
# Reference: Tokelau's 2012 systems, per atoll [IRENA 2013, Table 2; SOURCES.md items 1-2].
# Battery nominal = C20 Ah x 48 V. The real lead-acid banks are designed for 50% depth of discharge,
# so usable = 50% of nominal; ITP's "1.1-1.6 MWh" (Source A) matches that usable figure.
REAL = {"fakaofo": (330, 3379), "atafu": (297, 2765), "nukunonu": (264, 2458)}   # kWp, kWh nominal
REAL_USABLE_FRACTION = 0.5
i = r.inputs
atoll = next((a for a in REAL if a in i.site_name.lower()), None)
if atoll:
    pv_real, nom_real = REAL[atoll]
    usable_model = z.battery_kwh * (1 - config.BATTERY[i.battery_chemistry]["min_soc"])
    usable_real = nom_real * REAL_USABLE_FRACTION
    ratio = lambda m, ref: f"{m / ref:.2f}x"
    st.table({"": ["Solar (kWp)", "Battery, nominal (kWh)", "Battery, usable (kWh)"],
              "SunSafe recommended": [f"{z.pv_kw:,.0f}", f"{z.battery_kwh:,.0f}", f"{usable_model:,.0f}"],
              f"Real 2012 install, {atoll.title()}": [f"{pv_real:,}", f"{nom_real:,}", f"{usable_real:,.0f}"],
              "Model / real": [ratio(z.pv_kw, pv_real), ratio(z.battery_kwh, nom_real),
                               ratio(usable_model, usable_real)]})
    # Like-for-like check: the reference systems were built for lead-acid, ~100% solar, ~600 kWh/day.
    daily = i.daily_load_kwh if i.daily_load_kwh is not None else i.diesel_litres_per_day * 3.0
    diffs = []
    if i.battery_chemistry != "lead_acid":
        diffs.append("battery type (the real system used lead-acid)")
    if abs(i.renewable_target - 0.95) > 1e-9:
        diffs.append(f"renewable target ({i.renewable_target:.0%}; validation uses 95%)")
    if not 540 <= daily <= 660:
        diffs.append(f"daily load ({daily:,.0f} kWh/day; validation uses ~600, the 2008 measured level)")
    if diffs:
        st.warning("Not a like-for-like comparison: your inputs differ from the validation case in "
                   + "; ".join(diffs) + ". Load the atoll preset on Site Setup to compare like with like.")
    st.caption("Comparison only; the model was not tuned to these numbers. Real sizes: IRENA (2013) Table 2. "
               "The real system was designed for about 90% solar with diesel backup and 2008-level demand "
               "(553-699 kWh/day); demand reached about 850-940 kWh/day by 2013. See SOURCES.md."
               + (" Nukunonu shares Fakaofo's NASA weather grid cell; Atafu is the independent check."
                  if atoll in ("fakaofo", "nukunonu") else ""))
else:
    st.info("No reference installation for this site, so this design is not validated against a real system. "
            "SunSafe's sizing method is validated on Tokelau's 2012 systems (load a Tokelau preset on Site Setup "
            "to see it); for a new site, check the inputs (demand, diesel price, costs) and treat the result as "
            "a planning estimate, not an engineering design.")
