import streamlit as st
from components.layout import init, card, require_results, show_recommendation
from utils.formatting import money, pct

init("System Design", "What should we build?", step=1)
r = require_results()
z, last, n = r.sizing, r.lifecycle[-1], r.inputs.project_years
show_recommendation(r)
c = st.columns(4)
with c[0]: card("Solar", f"{z.pv_kw:,.0f} kW")
with c[1]: card("Battery", f"{z.battery_kwh:,.0f} kWh")
with c[2]: card("Estimated cost", money(z.capex_usd))
with c[3]: card("Renewable share (yr 1)", pct(z.renewable_share_year1))
c = st.columns(3)
with c[0]: card("Backup hours (critical load)", f"{r.backup_hours:,.0f} h")
with c[1]: card("Diesel avoided (yr 1)", f"{z.diesel_litres_avoided_year1:,.0f} L")
with c[2]: card(f"Renewable share (yr {last.year})", pct(last.share_funded_year_15))
st.caption(f"Year 1 can sit above the target because the design is sized to keep meeting it in every year, through year {n}.")

st.subheader("Model validation")
# Reference: Tokelau's 2012 installation, three island systems (SOURCES.md items 1-2).
# Source A gives ONE range covering all three atolls, so it applies to each of them.
REF_PV, REF_BATT = (265, 365), (1100, 1600)
TOKELAU_ATOLLS = ("fakaofo", "nukunonu", "atafu")
pos = lambda v, rng: "Within range" if rng[0] <= v <= rng[1] else ("Below range" if v < rng[0] else "Above range")
i = r.inputs
atoll = next((a for a in TOKELAU_ATOLLS if a in i.site_name.lower()), None)
if atoll:
    st.table({"": ["Solar (kWp)", "Battery (kWh)"],
              "SunSafe recommended": [f"{z.pv_kw:,.0f}", f"{z.battery_kwh:,.0f}"],
              "Real 2012 install, per atoll (reference)": ["265–365", "1,100–1,600 (Source A); ~2,700 (Source B)"],
              "Position": [pos(z.pv_kw, REF_PV), pos(z.battery_kwh, REF_BATT)]})
    # Like-for-like check: the reference systems were built for lead-acid, ~100% solar, ~600 kWh/day.
    daily = i.daily_load_kwh if i.daily_load_kwh is not None else i.diesel_litres_per_day * 3.0
    diffs = []
    if i.battery_chemistry != "lead_acid":
        diffs.append("battery type (the real system used lead-acid)")
    if abs(i.renewable_target - 0.95) > 1e-9:
        diffs.append(f"renewable target ({i.renewable_target:.0%}; validation uses 95%)")
    if not 540 <= daily <= 660:
        diffs.append(f"daily load ({daily:,.0f} kWh/day; validation uses ~600)")
    if diffs:
        st.warning("Not a like-for-like comparison: your inputs differ from the validation case in "
                   + "; ".join(diffs) + ". Load the atoll preset on Site Setup to compare like with like.")
    st.caption(f"Comparison only; the model was not tuned to these numbers. The reference range covers all three "
               f"Tokelau systems (Fakaofo, Nukunonu, Atafu), not {atoll.title()} alone, and the two battery sources "
               "disagree by about 2x (see SOURCES.md)."
               + (" Nukunonu shares Fakaofo's NASA weather grid cell, so its result is almost identical; "
                  "Atafu is the independent check." if atoll in ("fakaofo", "nukunonu") else ""))
else:
    st.info("No reference installation for this site, so this design is not validated against a real system. "
            "SunSafe's sizing method is validated on Tokelau's 2012 systems (load a Tokelau preset on Site Setup "
            "to see it); for a new site, check the inputs (demand, diesel price, costs) and treat the result as "
            "a planning estimate, not an engineering design.")
