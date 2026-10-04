import streamlit as st
from streamlit_folium import st_folium
from components.layout import (PACIFIC_NOTE, PAGE_PLAN, PRESETS, apply_preset, fmt_coords, growth_label,
                               growth_tuple, handle_map_result, in_pacific, init, island_map, matching_preset,
                               run_plan,
                               selected_marker, stretch)
from sunsafe import config

init("Your island", "Where is the mini-grid, and what does it run on today? Then build a plan that "
     "still meets your target in the final year.", step=0)
s = st.session_state
tag = lambda t: st.markdown(f'<span class="tag inp">{t}</span>', unsafe_allow_html=True)


def _on_preset():
    if s.preset in PRESETS:
        apply_preset(PRESETS[s.preset])


def _coords_typed():
    s.lat, s.lon = float(s.lat_in), float(s.lon_in)


s.preset = matching_preset()              # the dropdown shows the preset the inputs match, else "—"
st.selectbox("Pacific island preset", ["—"] + list(PRESETS), key="preset", on_change=_on_preset)
st.caption("Validation = a Tokelau atoll with the inputs used to check the model against the real system. "
           "Illustrative = real coordinates with made-up diesel use (200-600 L/day); replace with your island's data.")


L, R = st.columns([11, 10], gap="large")
with L:
    with st.container(border=True):
        tag("Map")
        # Built every run: st_folium changes the map object it draws, so a cached one stops reporting clicks.
        result = st_folium(island_map(), key="island_map", height=560, use_container_width=True,
                           returned_objects=["last_clicked", "last_object_clicked"],
                           feature_group_to_add=selected_marker())
        if handle_map_result(result):    # only the form changes; the model runs on Build my plan
            st.rerun()
        st.markdown(f'<div class="ss-coords">Selected: <b>{fmt_coords(float(s.lat), float(s.lon))}</b></div>',
                    unsafe_allow_html=True)
        st.caption("Click a grey preset marker to load it, or anywhere on the map to set the coordinates, then fine-tune "
                   "them on the right. Any coordinates work; solar data comes from NASA POWER.")
        if not in_pacific(s.lat, s.lon):
            st.markdown(f'<div class="notice">{PACIFIC_NOTE}</div>', unsafe_allow_html=True)
with R:
    with st.container(border=True):
        tag("Location")
        s.site_name = st.text_input("Island or site name", s.site_name)
        # Keyed inputs + a callback: the callback runs before the page redraws, so the map (drawn above)
        # moves its marker at once; map clicks and presets set these keys too (layout.set_coords).
        a, b = st.columns(2)
        for k, v in (("lat_in", s.lat), ("lon_in", s.lon)):
            if k not in s:
                s[k] = float(v)
        a.number_input("Latitude (south negative)", key="lat_in", min_value=-90.0, max_value=90.0, format="%.4f",
                       on_change=_coords_typed)
        b.number_input("Longitude (west negative)", key="lon_in", min_value=-180.0, max_value=180.0, format="%.4f",
                       on_change=_coords_typed)
    with st.container(border=True):
        tag("Diesel today")
        s.diesel_lpd = st.number_input("Diesel used by the power station (litres/day)",
                                       value=float(s.diesel_lpd), min_value=1.0, step=10.0)
        s.price = st.number_input(
            "Delivered diesel price (USD/litre)", value=float(s.price), min_value=0.10, step=0.05,
            help=(f"Default {config.TOKELAU_DIESEL_PRICE_USD_PER_L:.2f} = Apia 2026 average x freight to "
                  f"an outer atoll (Tokelau; SOURCES.md P1). Scenarios: low "
                  f"{config.TOKELAU_DIESEL_PRICE_LOW_USD_PER_L:.2f}, high "
                  f"{config.TOKELAU_DIESEL_PRICE_HIGH_USD_PER_L:.2f}. Use your island's landed price."))
    with st.container(border=True):
        tag("Your goals")
        s.target = st.slider("Renewable target, every year (%)", 50, 100, int(s.target))
        chems = {"lithium": "Lithium-ion", "lead_acid": "Lead-acid"}
        s.chem = st.selectbox("Battery type", list(chems), format_func=chems.get,
                              index=list(chems).index(s.chem))
        s.years = st.slider("Project length (years)", 10, 25, int(min(max(s.years, 10), 25)))
    with st.container(border=True):
        tag("Demand growth")
        a, b, c = st.columns(3)
        s.g_fast = a.number_input("Early growth (%/yr)", value=float(s.g_fast), min_value=0.0,
                                  max_value=30.0, step=0.5)
        s.g_years = b.number_input("for (years)", value=int(s.g_years), min_value=0, max_value=25, step=1)
        s.g_steady = c.number_input("then (%/yr)", value=float(s.g_steady), min_value=0.0,
                                    max_value=30.0, step=0.5)
        st.caption(f"Now: **{growth_label(growth_tuple())}**. Default 9% for 5 years then 3%: Tokelau's "
                   "demand grew ~9%/yr after solar arrived (SOURCES.md). Set years to 0 for a constant rate.")
    with st.expander("Advanced"):
        s.known_load = st.checkbox("I know the daily electricity demand", s.known_load)
        if s.known_load:
            s.load_kwh = st.number_input("Daily demand today (kWh/day)", value=float(s.load_kwh), min_value=1.0)
        else:
            st.caption(f"Estimated from diesel use at {config.DIESEL_KWH_PER_LITRE} kWh per litre.")
        s.critical_kw = st.number_input("Critical load: clinic, radio, water (kW)", value=float(s.critical_kw),
                                        min_value=0.1)

st.write("")
if stretch(st.button, "Build my plan", type="primary", key="build"):
    with st.spinner(f"Building your plan: testing four strategies over {int(s.years)} years "
                    "(a new site also fetches NASA solar data, about 15 s)..."):
        s.plan = run_plan()
    if s.plan is not None:
        s.just_built = True               # the plan page shows a short confirmation
        st.switch_page(PAGE_PLAN)
    else:
        st.error(f"The model could not run these inputs: {s.model_error}")
