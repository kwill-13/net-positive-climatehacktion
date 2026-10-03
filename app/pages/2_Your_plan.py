import streamlit as st
import streamlit.components.v1 as components
from components import charts
from components.layout import (PACIFIC_NOTE, PAGE_CHECKS, card, describe_stage, in_pacific, init,
                               require_plan, stretch)
from exports.proposal import build_onepager, build_proposal
from utils.formatting import money, pct

init("Your plan", "What to build now, when to upgrade, and what it costs.", step=1)
plan = require_plan()
r = plan["results"]
i, z, f = r.inputs, r.sizing, r.finance
n, target = i.project_years, i.renewable_target
upgrades = r.plan_stages[1:]
tokelau = any(a in i.site_name.lower() for a in ("fakaofo", "nukunonu", "atafu"))

if not in_pacific(i.latitude, i.longitude):
    st.markdown(f'<div class="notice">{PACIFIC_NOTE}</div>', unsafe_allow_html=True)
st.markdown(f"**{i.site_name}** · {i.diesel_litres_per_day:,.0f} L/day diesel at ${i.diesel_price_per_litre:.2f}/L · "
            f"target {pct(target)} every year · {n} years · demand growth {plan['growth_label']} · "
            f"{i.battery_chemistry.replace('_', '-')} battery")
# Plain text wraps in a narrow window; a page_link label does not, so the sentence sits above a short link.
if not tokelau:
    st.markdown("ℹ️ Planning estimate. Engine checked against Tokelau's measured performance.")
else:
    st.markdown("ℹ️ Tokelau validation site: compare this plan with the real 2012 system.")
st.page_link(PAGE_CHECKS, label="How we know it works", icon="➡️")
if not plan["any_feasible"]:
    st.error(f"No plan kept {pct(target)} renewable in every year; showing the closest one. "
             "Try a lower target or a shorter project.")

# ------------------------------------------------------------ a. decisions ---
c = st.columns(3)
with c[0]:
    card("Build now", f"{z.pv_kw:,.0f} kWp + {z.battery_kwh:,.0f} kWh",
         sub=f"Capex {money(z.capex_usd)} · {pct(z.renewable_share_year1)} solar in year 1")
with c[1]:
    if upgrades:
        items = "".join(f"<li>{describe_stage(s_, i.battery_chemistry)}</li>" for s_ in upgrades)
        card("Upgrades", f"{len(upgrades)} planned", html_body=f"<ul>{items}</ul>")
    else:
        card("Upgrades", "None needed", sub=f"The first build holds the target through year {n}.")
with c[2]:
    first = f" (year {upgrades[0].year})" if upgrades else ""
    later = (f" Later upgrades (year {', '.join(str(u.year) for u in upgrades[1:])}) need their own funding."
             if len(upgrades) > 1 else "")
    card("Set aside per year", money(f.om_fund_per_year_usd),
         sub=f"Solar + battery O&M, plus saving toward the first upgrade{first}.{later}")
st.caption(f"Recommended: {plan['rec_name']}. The lowest {n}-year cost plan that meets the target in every year.")


def show(builder, where=st):
    chart, caption = builder(plan)
    chart = charts.fit_width(chart)
    with where.container():
        stretch(st.altair_chart, chart)
        st.caption(caption)


# ------------------------------------------------------- the plan, in charts ---
show(charts.investment_timeline)
show(charts.renewable_share)
show(charts.night_coverage)
show(charts.fund_balance)      # full width: side-by-side columns squeeze charts in a narrow window
show(charts.cost_bars)

# ------------------------------------------------------------------ risks ---
show(charts.fuel_shock)
card("Backup with no fuel", f"{r.backup_hours:,.0f} hours",
     sub=f"Critical load ({i.critical_load_kw:g} kW: clinic, radio) on a full battery.")

with st.expander("Alternatives we considered"):
    show(charts.strategy_npv)
    show(charts.price_breakeven)

# --------------------------------------------------------------- exports ---
st.subheader("Share the plan")
a, b = st.columns(2)
proposal, onepager = build_proposal(r, plan), build_onepager(r, plan)
stretch(a.download_button, "Funding proposal", proposal, "sunsafe_funding_proposal.html", mime="text/html")
stretch(b.download_button, "Community one-pager", onepager, "sunsafe_community_onepager.md")
st.caption("Funding proposal: an HTML file with the charts above; it opens in any browser (charts load from "
           "the Vega CDN, so it needs internet), and Print > Save as PDF makes a PDF. Community one-pager: a "
           "plain-text (Markdown) summary.")
with st.expander("Preview proposal"):
    components.html(proposal, height=900, scrolling=True)
with st.expander(f"Model notes ({len(r.warnings)})"):
    for w in r.warnings:
        st.markdown(f"- {w}")
