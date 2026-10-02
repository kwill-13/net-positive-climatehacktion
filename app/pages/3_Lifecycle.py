import pandas as pd
import streamlit as st
from components.layout import init, card, require_results
from utils.formatting import money

init("Lifecycle", "Will the system still work in year 15?")
r = require_results()
df = pd.DataFrame([vars(y) for y in r.lifecycle]).set_index("year")
st.subheader("Renewable share over time")
st.line_chart((df[["share_funded_day_one", "share_funded_year_15"]] * 100).rename(
    columns={"share_funded_day_one": "Funded for Day One", "share_funded_year_15": "Funded for Year 15"}),
    x_label="Year", y_label="Renewable share (%)")
a, b = st.columns(2)
a.line_chart(df[["battery_capacity_kwh"]].rename(columns={"battery_capacity_kwh": "Usable battery (kWh, no replacement)"}))
b.line_chart(df[["demand_kwh_per_day"]].rename(columns={"demand_kwh_per_day": "Demand (kWh/day)"}))
st.subheader("O&M plan")
card("Annual O&M + replacement fund", money(r.finance.om_fund_per_year_usd))
