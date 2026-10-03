import pandas as pd
import streamlit as st
from components.layout import init, card, require_results, show_recommendation, horizon
from utils.formatting import money

init("Lifecycle", f"Will the system still work in year {horizon()}?", step=2)
r = require_results()
n = r.inputs.project_years
df = pd.DataFrame([vars(y) for y in r.lifecycle]).set_index("year")
show_recommendation(r)
st.subheader("Renewable share over time")
st.line_chart((df[["share_funded_day_one", "share_funded_year_15"]] * 100).rename(
    columns={"share_funded_day_one": "Funded for Day One (never replaced)",
             "share_funded_year_15": f"Funded for Year {n} (planned replacement)"}),
    x_label="Year", y_label="Renewable share (%)", color=["#c0504d", "#1f6f66"])
if (df.share_funded_day_one - df.share_funded_year_15).abs().max() < 1e-9:
    st.caption("The recommended strategy has no battery replacement, so the two lines are identical.")
a, b = st.columns(2)
a.line_chart(df[["battery_capacity_kwh"]].rename(columns={"battery_capacity_kwh": "Usable battery (kWh, no replacement)"}))
b.line_chart(df[["demand_kwh_per_day"]].rename(columns={"demand_kwh_per_day": "Demand (kWh/day)"}))
st.subheader("O&M plan")
card("Annual O&M + replacement fund", money(r.finance.om_fund_per_year_usd))
