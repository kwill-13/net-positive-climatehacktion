import pydeck as pdk
import streamlit as st
from components.layout import (PACIFIC_NOTE, PAGE_PLAN, PRESETS, apply_preset, growth_label,
                               growth_tuple, handle_map_click, in_pacific, init, run_plan,
                               stretch, wrap_lon)
from sunsafe import config

init("Your island", "Where is the mini-grid, and what does it run on today? Then build a plan that "
     "still meets your target in the final year.", step=0)
s = st.session_state
tag = lambda t: st.markdown(f'<span class="tag inp">{t}</span>', unsafe_allow_html=True)


def _on_preset():
    if s.preset in PRESETS:
        apply_preset(PRESETS[s.preset])


st.selectbox("Start from a Pacific island preset (Tokelau atolls use the validation inputs; "
             "the others have illustrative diesel use)", ["—"] + list(PRESETS), key="preset",
             on_change=_on_preset)

# ------------------------------------------------------------------- map ---
# Click targets: a faint 1-degree grid over the Pacific, plus the presets. Longitudes are drawn
# 0-360 so the map does not split at the date line (see wrap_lon in layout).
_wrap = wrap_lon


@st.cache_data(show_spinner=False)
def _grid():
    return [{"lat": float(la), "lon": float(lo)} for la in range(-30, 26) for lo in range(130, 241)]


def _map():
    here = [{"lat": float(s.lat), "lon": _wrap(float(s.lon)), "name": s.site_name}]
    presets = [{"lat": p["lat"], "lon": _wrap(p["lon"]), "name": p["name"], "label": k}
               for k, p in PRESETS.items()]
    layers = [
        pdk.Layer("ScatterplotLayer", id="grid", data=_grid(), get_position="[lon, lat]",
                  get_fill_color=[31, 111, 102, 18], get_radius=40000, radius_min_pixels=3, pickable=True),
        pdk.Layer("ScatterplotLayer", id="presets", data=presets, get_position="[lon, lat]",
                  get_fill_color=[123, 111, 176, 220], get_radius=30000, radius_min_pixels=6, pickable=True),
        pdk.Layer("ScatterplotLayer", id="here", data=here, get_position="[lon, lat]",
                  get_fill_color=[192, 80, 77, 255], get_radius=30000, radius_min_pixels=8),
    ]
    view = pdk.ViewState(latitude=float(s.lat), longitude=_wrap(float(s.lon)), zoom=2.6)
    return pdk.Deck(layers=layers, initial_view_state=view, map_style="light",
                    tooltip={"text": "{name}"})


L, R = st.columns(2, gap="large")
with L:
    with st.container(border=True):
        tag("Location")
        event = st.pydeck_chart(_map(), on_select="rerun", selection_mode="single-object", key="map",
                                height=300)
        if handle_map_click(event):
            st.rerun()
        st.caption("Click a purple preset or anywhere on the faint 1° grid, then fine-tune the "
                   "coordinates below. Any coordinates work; solar data comes from NASA POWER.")
        s.site_name = st.text_input("Island or site name", s.site_name)
        a, b = st.columns(2)
        s.lat = a.number_input("Latitude (south negative)", value=float(s.lat), min_value=-90.0,
                               max_value=90.0, format="%.4f")
        s.lon = b.number_input("Longitude (west negative)", value=float(s.lon), min_value=-180.0,
                               max_value=180.0, format="%.4f")
        if not in_pacific(s.lat, s.lon):
            st.markdown(f'<div class="notice">{PACIFIC_NOTE}</div>', unsafe_allow_html=True)
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
with R:
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

if stretch(st.button, "Build my plan", type="primary"):
    with st.spinner(f"Building your plan: testing four strategies over {int(s.years)} years "
                    "(a new site also fetches NASA solar data, about 15 s)..."):
        s.plan = run_plan()
    if s.plan is not None:
        st.switch_page(PAGE_PLAN)
    else:
        st.error(f"The model could not run these inputs: {s.model_error}")
