import pandas as pd
import streamlit as st
from components.layout import init, require_results
from utils.formatting import MONTHS, pct

init("What else can this clean electricity power?", "What additional activities can clean power support?")
h = require_results().headroom
st.subheader("Surplus solar by month (kWh)")
st.bar_chart(pd.Series(h.surplus_kwh_by_month, index=MONTHS, name="Surplus kWh"))
c = st.columns(2)
c[0].metric("Electricity share of local energy use: before", pct(h.electricity_share_before))
c[1].metric("After", pct(h.electricity_share_after))
st.subheader("Suggested new loads")
for load in h.suggested_new_loads:
    st.markdown(f"- {load}")
