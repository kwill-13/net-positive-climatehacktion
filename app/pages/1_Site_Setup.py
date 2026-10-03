import time
import pandas as pd
import streamlit as st
from components.layout import init, run_analysis

init("Site Setup", "What are we telling SunSafe? Fill in the four input groups, then run the analysis.", step=0)
s = st.session_state
tag = lambda t: st.markdown(f'<span class="tag inp">{t}</span>', unsafe_allow_html=True)
PRESETS = {"Fakaofo (validation site)": ("Fakaofo", -9.38, -171.24),
           "Nukunonu (approx. coordinates)": ("Nukunonu", -9.17, -171.85),
           "Atafu (approx. coordinates)": ("Atafu", -8.54, -172.50)}


def apply_preset():
    if s.preset in PRESETS:
        s.site_name, s.lat, s.lon = PRESETS[s.preset]
        s.price, s.known_load, s.load_kwh, s.chem, s.target = 2.70, True, 600.0, "lead_acid", 95


st.selectbox("Load a demo preset (Tokelau delivered diesel price, 600 kWh/day)", ["—"] + list(PRESETS),
             key="preset", on_change=apply_preset)
L, R = st.columns(2, gap="large")
with L:
    with st.container(border=True):
        tag("Input · Site")
        s.site_name = st.text_input("Location name", s.site_name)
        a, b = st.columns(2)
        s.lat = a.number_input("Latitude (south negative)", value=float(s.lat), format="%.4f")
        s.lon = b.number_input("Longitude (west negative)", value=float(s.lon), format="%.4f")
        st.map(pd.DataFrame({"lat": [s.lat], "lon": [s.lon]}), zoom=4, height=240)
        st.caption("Integration point: swap for a click-to-select map that writes lat/lon to session_state.")
    with st.container(border=True):
        tag("Input · Current diesel")
        s.diesel_lpd = st.number_input("Diesel consumption (L/day)", value=float(s.diesel_lpd), min_value=0.0)
        s.price = st.number_input("Delivered diesel price (USD/L)", value=float(s.price), min_value=0.0,
                              help="Default 2.70 = Tokelau delivered price (derived; see SOURCES.md). Apia retail 2026 was USD 1.17-1.93/L; below about USD 2.34/L diesel-only is cheaper per kWh.")
        s.known_load = st.checkbox("I know the daily electricity load", s.known_load)
        if s.known_load:
            s.load_kwh = st.number_input("Daily load (kWh/day)", value=float(s.load_kwh), min_value=1.0)
        else:
            st.caption("Otherwise the model estimates load from diesel use.")
with R:
    with st.container(border=True):
        tag("Input · Your goals")
        s.target = st.slider("Renewable target (%)", 50, 100, int(s.target))
        chems = {"lithium": "Lithium-ion", "lead_acid": "Lead-acid"}
        s.chem = st.selectbox("Battery type", list(chems), format_func=chems.get, index=list(chems).index(s.chem))
        s.years = st.number_input("Project horizon (years)", 5, 25, int(s.years))
    with st.container(border=True):
        tag("Input · Assumptions")
        s.growth = st.number_input("Demand growth (%/year)", value=float(s.growth), step=0.5)
        s.critical_kw = st.number_input("Critical load: clinic, comms (kW)", value=float(s.critical_kw), min_value=0.1)
    with st.container(border=True):
        tag("Open data")
        st.write("Solar: NASA POWER (synthetic fallback if unavailable, the model notes say so). Fuel-price path: sourced Apia series. Other placeholders are listed in the model notes after analysis.")

if st.button("Run SunSafe Analysis", type="primary", use_container_width=True):
    with st.status("Running SunSafe analysis (a new site fetches NASA solar data, about 15 s)...", expanded=True) as status:
        s.results = run_analysis()
        for step in ["Loading site information", "Loading solar resource", "Simulating electricity demand",
                     "Sizing solar + battery", "Simulating lifecycle", "Calculating financial case",
                     "Assessing electrification headroom"]:
            st.write(f"✓ {step}")
        status.update(label="Analysis complete", state="complete")
    st.success("Done. Open **System Design** in the sidebar to see the result.")
