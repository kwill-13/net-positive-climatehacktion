import streamlit as st
from components.layout import init

init("SunSafe")
st.markdown("### Plan the transition from diesel to solar — and keep it working for 15 years.")
st.write("SunSafe helps Pacific energy planners model solar + battery systems, understand lifecycle costs, "
         "plan for battery replacement and diesel-price risk, and identify opportunities for further electrification.")
c = st.columns([1, 1, 1])
c[0].markdown('<div class="card inp"><span class="tag inp">Inputs</span><br><b>What we tell SunSafe</b><br>'
              'Site · Diesel use · Goals · Assumptions</div>', unsafe_allow_html=True)
c[1].markdown('<div class="card"><span class="tag">SunSafe model</span><br><b>What it calculates</b><br>'
              'Energy model → Lifecycle model</div>', unsafe_allow_html=True)
c[2].markdown('<div class="card out"><span class="tag out">Outputs</span><br><b>What it tells us</b><br>'
              'System · Year-15 · O&amp;M · Fuel shock · Backup · Headroom · Funding case</div>', unsafe_allow_html=True)
st.page_link("pages/1_Site_Setup.py", label="Start a new site assessment", icon="➡️")
