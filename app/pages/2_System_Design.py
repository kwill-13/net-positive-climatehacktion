import streamlit as st
from components.layout import init, card, require_results, show_recommendation
from utils.formatting import money, pct

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
REF_PV, REF_BATT = (265, 365), (1100, 1600)
pos = lambda v, rng: "Within range" if rng[0] <= v <= rng[1] else ("Below range" if v < rng[0] else "Above range")
if "fakaofo" in r.inputs.site_name.lower():
    st.table({"": ["Solar (kWp)", "Battery (kWh)"],
              "SunSafe recommended": [f"{z.pv_kw:,.0f}", f"{z.battery_kwh:,.0f}"],
              "Real 2012 install (reference)": ["265–365", "1,100–1,600 (Source A); ~2,700 (Source B)"],
              "Position": [pos(z.pv_kw, REF_PV), pos(z.battery_kwh, REF_BATT)]})
    st.caption("Comparison only; the model was not tuned to these numbers. Meaningful for the Fakaofo validation "
               "inputs (600 kWh/day, lead-acid, 95%). Cite the reference sources before presenting.")
else:
    st.info("Validation compares against the real Fakaofo (Tokelau) installation. Load the Fakaofo preset on Site Setup to see it.")
