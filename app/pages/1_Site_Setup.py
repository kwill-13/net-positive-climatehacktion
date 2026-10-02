import time
import pandas as pd
import streamlit as st
from components.layout import init, run_analysis

init("Site Setup", "What are we telling SunSafe?")
s = st.session_state
L, R = st.columns(2)
with L:
    st.subheader("Site")
    s.site_name = st.text_input("Location name", s.site_name)
    a, b = st.columns(2)
    s.lat = a.number_input("Latitude (south negative)", value=float(s.lat), format="%.4f")
    s.lon = b.number_input("Longitude (west negative)", value=float(s.lon), format="%.4f")
    st.map(pd.DataFrame({"lat": [s.lat], "lon": [s.lon]}), zoom=4)
    st.caption("Integration point: swap for a click-to-select map that writes lat/lon to session_state.")
    st.subheader("Current diesel")
    s.diesel_lpd = st.number_input("Diesel consumption (L/day)", value=float(s.diesel_lpd), min_value=0.0)
    s.price = st.number_input("Delivered diesel price (USD/L)", value=float(s.price), min_value=0.0)
    s.known_load = st.checkbox("I know the daily electricity load", s.known_load)
    if s.known_load:
        s.load_kwh = st.number_input("Daily load (kWh/day)", value=float(s.load_kwh), min_value=1.0)
    else:
        st.caption("Otherwise the model estimates load from diesel use.")
with R:
    st.subheader("Your goals")
    s.target = st.slider("Renewable target (%)", 50, 100, int(s.target))
    chems = {"lithium": "Lithium-ion", "lead_acid": "Lead-acid"}
    s.chem = st.selectbox("Battery type", list(chems), format_func=chems.get, index=list(chems).index(s.chem))
    s.years = st.number_input("Project horizon (years)", 5, 25, int(s.years))
    st.subheader("Assumptions")
    s.growth = st.number_input("Demand growth (%/year)", value=float(s.growth), step=0.5)
    s.critical_kw = st.number_input("Critical load: clinic, comms (kW)", value=float(s.critical_kw), min_value=0.1)
    st.subheader("Open data")
    st.info("Solar data and fuel prices: connected by the model team (see warnings after analysis).")

if st.button("Run SunSafe Analysis", type="primary"):
    with st.status("Running SunSafe analysis...", expanded=True) as status:
        for step in ["Loading site information", "Loading solar resource", "Simulating electricity demand",
                     "Sizing solar + battery", "Simulating lifecycle", "Calculating financial case",
                     "Assessing electrification headroom"]:
            time.sleep(0.15)
            st.write(f"✓ {step}")
        s.results = run_analysis()
        status.update(label="Analysis complete", state="complete")
    st.success("Next: open **System Design** in the sidebar.")
