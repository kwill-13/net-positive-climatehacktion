import streamlit as st
from components.layout import init

init("SunSafe")
st.header("Plan the transition from diesel to solar — and keep it working for 15 years.")
st.write("SunSafe helps Pacific energy planners model solar + battery systems, understand lifecycle costs, "
         "plan for battery replacement and diesel-price risk, and identify opportunities for further electrification.")
c = st.columns(3)
c[0].markdown("**INPUTS** — what we tell SunSafe\n\nSite · Diesel · Goals · Assumptions")
c[1].markdown("**SUNSAFE MODEL** — what it calculates\n\nEnergy model → Lifecycle model")
c[2].markdown("**OUTPUTS** — what it tells us\n\nSystem · Year-15 · O&M · Fuel shock · Backup · Headroom · Funding case")
st.page_link("pages/1_Site_Setup.py", label="Start a new site assessment", icon="➡️")
