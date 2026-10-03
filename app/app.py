import streamlit as st
from components.layout import PAGE_CHECKS, PAGE_ISLAND, PAGE_PLAN, init

init("SunSafe")
st.markdown("### Plan a Pacific island mini-grid that still works in its final year.")
st.write("SunSafe helps Pacific island energy officers move from diesel to solar + battery. It plans what to "
         "build now, when to upgrade as demand grows and batteries age, and what it costs, including who pays.")
c = st.columns(3)
c[0].markdown('<div class="card inp"><span class="tag inp">1 · Your island</span><br><b>Where and how much diesel</b><br>'
              'Location · Diesel use and price · Target · Growth</div>', unsafe_allow_html=True)
c[1].markdown('<div class="card out"><span class="tag out">2 · Your plan</span><br><b>Build now, upgrade later</b><br>'
              'Upgrade years · Year-by-year share · Cost per kWh · Who pays</div>', unsafe_allow_html=True)
c[2].markdown('<div class="card"><span class="tag">3 · How we know it works</span><br><b>Checked against Tokelau</b><br>'
              'Real systems · Sensitivity · Sources</div>', unsafe_allow_html=True)
st.page_link(PAGE_ISLAND, label="Start with your island", icon="➡️")
st.page_link(PAGE_PLAN, label="See the current plan")
st.page_link(PAGE_CHECKS, label="How we know it works")
