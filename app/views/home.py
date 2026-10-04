import streamlit as st
from components.layout import PAGE_CHECKS, PAGE_ISLAND, PAGE_PLAN, card_grid, go_button, init

init("SunSafe")
st.markdown('<div class="ss-hero"><h3>Plan a Pacific island mini-grid that still works in its final year.</h3>'
            '<p>SunSafe helps Pacific island energy officers move from diesel to solar + battery. It plans what to '
            'build now, when to upgrade as demand grows and batteries age, and what it costs, including who '
            'pays.</p></div>', unsafe_allow_html=True)
a, _ = st.columns([1, 2])
with a:
    go_button("Start planning", PAGE_ISLAND, key="hero_start", primary=True)

card_grid([
    '<div class="card inp"><span class="tag inp">1 · Your island</span><br><b>Where and how much diesel</b><br>'
    'Location · Diesel use and price · Target · Growth</div>',
    '<div class="card out"><span class="tag out">2 · Your plan</span><br><b>Build now, upgrade later</b><br>'
    'Upgrade years · Year-by-year share · Cost per kWh · Who pays</div>',
    '<div class="card"><span class="tag">3 · How we know it works</span><br><b>Checked against Tokelau</b><br>'
    'Real systems · Sensitivity · Sources</div>',
])
a, b, _ = st.columns([1, 1, 1])
with a:
    go_button("See the current plan", PAGE_PLAN, key="home_plan")
with b:
    go_button("How we know it works", PAGE_CHECKS, key="home_checks")
