import pandas as pd
import streamlit as st
from components.layout import init, require_results
from utils.formatting import money, tco2, years

init("Financials", "What does it cost, and what if diesel prices spike?")
r = require_results()
f, z = r.finance, r.sizing
c = st.columns(4)
c[0].metric("Capital cost", money(z.capex_usd))
c[1].metric("O&M + replacement fund / yr", money(f.om_fund_per_year_usd))
c[2].metric("Cost per kWh: hybrid", f"${f.cost_per_kwh_hybrid_usd:.2f}")
c[3].metric("Cost per kWh: diesel", f"${f.cost_per_kwh_diesel_usd:.2f}")
c = st.columns(3)
c[0].metric("Payback", years(f.payback_years))
c[1].metric("Diesel avoided (yr 1)", f"{z.diesel_litres_avoided_year1:,.0f} L")
c[2].metric("Emissions avoided (yr 1)", f"{tco2(z.diesel_litres_avoided_year1):,.0f} tCO₂e")
st.subheader("Fuel-shock replay")
df = pd.DataFrame([vars(m) for m in r.fuel_shock]).set_index("month")
st.line_chart(df[["diesel_price_per_litre"]].rename(columns={"diesel_price_per_litre": "Diesel price (USD/L)"}))
st.bar_chart(df[["cost_diesel_only_usd", "cost_hybrid_usd"]].rename(
    columns={"cost_diesel_only_usd": "Diesel-only", "cost_hybrid_usd": "Solar + battery hybrid"}))
