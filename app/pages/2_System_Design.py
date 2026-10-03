import streamlit as st
from components.layout import init, card, require_results
from utils.formatting import money, pct

init("System Design", "What should we build?", step=1)
r = require_results()
z = r.sizing
c = st.columns(4)
with c[0]: card("Solar", f"{z.pv_kw:,.0f} kW")
with c[1]: card("Battery", f"{z.battery_kwh:,.0f} kWh")
with c[2]: card("Estimated cost", money(z.capex_usd))
with c[3]: card("Renewable share (yr 1)", pct(z.renewable_share_year1))
c = st.columns(2)
with c[0]: card("Backup hours (critical load)", f"{r.backup_hours:,.0f} h")
with c[1]: card("Diesel avoided (yr 1)", f"{z.diesel_litres_avoided_year1:,.0f} L")
st.subheader("Model validation")
st.warning("Not yet connected. Predicted vs reference (Tokelau / REopt) comparison will appear here.")
