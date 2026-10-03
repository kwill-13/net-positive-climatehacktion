import altair as alt
import pandas as pd
import streamlit as st
from components.layout import (AMBER, GREY, PACIFIC_NOTE, PAGE_CHECKS, PURPLE, RED, TEAL, card,
                               beats_diesel, describe_stage, in_pacific, init, require_plan,
                               stretch)
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
if not tokelau:
    st.page_link(PAGE_CHECKS, label="Planning estimate. Engine checked against Tokelau's measured performance",
                 icon="ℹ️")
else:
    st.page_link(PAGE_CHECKS, label="Tokelau validation site: compare with the real 2012 system", icon="ℹ️")
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

# ---------------------------------------------------------- b. hero chart ---
st.subheader(f"Will it still work in year {n}?")
yrs = pd.DataFrame(plan["years"])
label_plan = "With the plan's upgrades" if upgrades else "The plan"
share = pd.concat([
    pd.DataFrame({"Year": yrs.year, "Renewable share (%)": yrs.share_plan * 100, "Case": label_plan}),
    pd.DataFrame({"Year": yrs.year, "Renewable share (%)": yrs.share_without * 100,
                  "Case": "Without reinvestment (first build only)"}),
])
lo = min(share["Renewable share (%)"].min(), target * 100) - 3
xs = alt.X("Year:Q", axis=alt.Axis(tickMinStep=1, format="d"), scale=alt.Scale(domain=[1, n]))
lines = alt.Chart(share).mark_line(point=True).encode(
    x=xs, y=alt.Y("Renewable share (%):Q", scale=alt.Scale(domain=[max(lo, 0), 100.5])),
    color=alt.Color("Case:N", scale=alt.Scale(domain=[label_plan, "Without reinvestment (first build only)"],
                                              range=[TEAL, RED]), legend=alt.Legend(orient="bottom", title=None)),
    tooltip=["Year", "Case", alt.Tooltip("Renewable share (%):Q", format=".1f")])
tline = alt.Chart(pd.DataFrame({"y": [target * 100]})).mark_rule(strokeDash=[6, 4], color="#555").encode(y="y:Q")
tlabel = alt.Chart(pd.DataFrame({"y": [target * 100], "x": [1], "t": [f"Target {pct(target)}"]})).mark_text(
    align="left", dy=-7, color="#555").encode(x="x:Q", y="y:Q", text="t:N")


def upgrade_marks():
    if not upgrades:
        return []
    u = pd.DataFrame({"Year": [s_.year for s_ in upgrades], "t": [f"Upgrade yr {s_.year}" for s_ in upgrades]})
    rules = alt.Chart(u).mark_rule(color=PURPLE, strokeDash=[2, 3]).encode(x="Year:Q")
    text = alt.Chart(u).mark_text(align="left", dx=3, baseline="top", color=PURPLE).encode(
        x="Year:Q", y=alt.value(4), text="t:N")
    return [rules, text]


stretch(st.altair_chart, alt.layer(lines, tline, tlabel, *upgrade_marks()).properties(height=340))
st.caption(f"Decision: fund the upgrades on schedule. Without them, the share falls to "
           f"{pct(yrs.share_without.iloc[-1])} by year {n}; with them it stays at or above "
           f"{pct(yrs.share_plan.min())}."
           + (" Year 1 sits above the target because the build is sized to last until the first upgrade."
              if yrs.share_plan.iloc[0] > target + 0.01 else ""))

# ------------------------------------------------------- c. why this plan ---
st.subheader("Why this plan")
strat = pd.DataFrame(plan["strategies"])
strat["Strategy"] = strat.label + strat.feasible.map({True: "", False: " (misses target)"})
strat["NPV ($M)"] = strat.npv / 1e6
strat["Pick"] = strat.recommended.map({True: "Recommended", False: "Other"})
bars = alt.Chart(strat).mark_bar().encode(
    y=alt.Y("Strategy:N", sort=list(strat.Strategy), title=None),
    x=alt.X("NPV ($M):Q", title=f"{n}-year cost, present value (USD M, 8%)"),
    color=alt.Color("Pick:N", scale=alt.Scale(domain=["Recommended", "Other"], range=[TEAL, "#cfcac0"]), legend=None),
    tooltip=["Strategy", "name", alt.Tooltip("NPV ($M):Q", format=".2f")])
labels = bars.mark_text(align="left", dx=4, color="#2b2b2b").encode(text=alt.Text("NPV ($M):Q", format="$.2f"))
stretch(st.altair_chart, (bars + labels).properties(height=200))
rec_label = next(x["label"] for x in plan["strategies"] if x["recommended"])
saving = plan["saving_vs_a"]
st.caption(f"Decision: which strategy to fund. **{rec_label}** costs the least over {n} years"
           + (f", {saving:.0%} less than building big for year {n} on day one." if saving and saving > 0.0005
              else "." if saving is None else "; building big is already the cheapest.")
           + " Each bar is the cheapest version of that strategy (all costs: build, O&M, upgrades, generator fuel).")

# ------------------------------------------------ d. why these upgrade years ---
st.subheader("Why these upgrade years")
cap = pd.concat([
    pd.DataFrame({"Year": yrs.year, "kWh": yrs.usable_plan, "Series": "Usable battery, with the plan (kWh)"}),
    pd.DataFrame({"Year": yrs.year, "kWh": yrs.usable_without, "Series": "Usable battery, never replaced (kWh)"}),
    pd.DataFrame({"Year": yrs.year, "kWh": yrs.demand, "Series": "Daily demand (kWh/day)"}),
])
cap_lines = alt.Chart(cap).mark_line(point=True).encode(
    x=xs, y=alt.Y("kWh:Q", title="kWh"),
    color=alt.Color("Series:N", scale=alt.Scale(
        domain=["Usable battery, with the plan (kWh)", "Usable battery, never replaced (kWh)", "Daily demand (kWh/day)"],
        range=[TEAL, RED, AMBER]), legend=alt.Legend(orient="bottom", title=None, columns=2)),
    tooltip=["Year", "Series", alt.Tooltip("kWh:Q", format=",.0f")])
stretch(st.altair_chart, alt.layer(cap_lines, *upgrade_marks()).properties(height=300))
st.caption("Decision: when to schedule and budget each upgrade. The battery fades every year while demand "
           "grows; an upgrade is due when the stored energy can no longer cover enough of the night to "
           "hold the target.")

# ----------------------------------------------- e. costs and who pays ---
st.subheader("What it costs, and who pays")
costs = pd.DataFrame({"Diesel price (USD/L)": plan["prices"], "Diesel only": plan["cost_diesel"],
                      "Full hybrid cost": plan["cost_full"],
                      "Island-paid (if donors fund the first build)": plan["cost_island"]})
costs = costs.melt("Diesel price (USD/L)", var_name="Cost", value_name="USD per kWh")
names = ["Diesel only", "Full hybrid cost", "Island-paid (if donors fund the first build)"]
clines = alt.Chart(costs).mark_line().encode(
    x=alt.X("Diesel price (USD/L):Q", scale=alt.Scale(domain=[1, 3.5])),
    y=alt.Y("USD per kWh:Q"),
    color=alt.Color("Cost:N", scale=alt.Scale(domain=names, range=[GREY, TEAL, PURPLE]),
                    legend=alt.Legend(orient="bottom", title=None)),
    strokeDash=alt.StrokeDash("Cost:N", scale=alt.Scale(domain=names, range=[[4, 3], [1, 0], [1, 0]]), legend=None),
    tooltip=["Cost", "Diesel price (USD/L)", alt.Tooltip("USD per kWh:Q", format="$.3f")])
marks = [{"x": i.diesel_price_per_litre, "t": f"Your price ${i.diesel_price_per_litre:.2f}", "c": "#555"}]
for key, txt in (("breakeven_full", "Full-cost breakeven"), ("breakeven_island", "Island-paid breakeven")):
    if plan[key] is not None:
        marks.append({"x": plan[key], "t": f"{txt} ${plan[key]:.2f}", "c": TEAL if key == "breakeven_full" else PURPLE})
mrules = alt.Chart(pd.DataFrame(marks)).mark_rule(strokeDash=[2, 3]).encode(
    x="x:Q", color=alt.Color("c:N", scale=None))
mtexts = [alt.Chart(pd.DataFrame([m])).mark_text(align="left", dx=3, baseline="top", color=m["c"]).encode(
    x="x:Q", y=alt.value(4 + 16 * k), text="t:N") for k, m in enumerate(marks)]
stretch(st.altair_chart, alt.layer(clines, mrules, *mtexts).properties(height=340))
ap = plan["at_price"]
be_f, be_i = plan["breakeven_full"], plan["breakeven_island"]

be_f_txt = beats_diesel(be_f, plan["cost_full"], plan["cost_diesel"])
be_i_txt = beats_diesel(be_i, plan["cost_island"], plan["cost_diesel"])
st.caption(f"Decision: who should pay for the first build. At ${i.diesel_price_per_litre:.2f}/L: diesel only "
           f"${ap['diesel']:.2f}/kWh, full hybrid ${ap['full']:.2f}/kWh, island-paid ${ap['island']:.2f}/kWh "
           f"if donors fund the first build ({money(z.capex_usd)}). The hybrid beats diesel {be_f_txt} "
           f"on full cost, and {be_i_txt} for the island. Island-paid = O&M + later upgrades + "
           f"generator fuel and O&M; the plan is fixed, only the diesel price varies.")

# ------------------------------------------------------------------ f. risks ---
st.subheader("Risks: fuel shocks and outages")
a, b = st.columns([3, 1])
with a:
    fs = pd.DataFrame([vars(m) for m in r.fuel_shock])
    fsl = fs.melt("month", ["cost_diesel_only_usd", "cost_hybrid_usd"], var_name="Case", value_name="USD per month")
    fsl["Case"] = fsl.Case.map({"cost_diesel_only_usd": "Diesel only", "cost_hybrid_usd": "With the plan"})
    fbars = alt.Chart(fsl).mark_bar().encode(
        x=alt.X("month:N", title="Month (2026)"), xOffset="Case:N", y=alt.Y("USD per month:Q"),
        color=alt.Color("Case:N", scale=alt.Scale(domain=["Diesel only", "With the plan"], range=[GREY, TEAL]),
                        legend=alt.Legend(orient="bottom", title=None)),
        tooltip=["month", "Case", alt.Tooltip("USD per month:Q", format="$,.0f")])
    stretch(st.altair_chart, fbars.properties(height=260))
    peak = fs.loc[fs.diesel_price_per_litre.idxmax()]
    st.caption(f"Decision: how much fuel-price risk the plan removes. Replaying 2026's diesel price swings "
               f"(peak ${peak.diesel_price_per_litre:.2f}/L in {peak.month}), the monthly bill with the plan is "
               f"{money(peak.cost_hybrid_usd)} vs {money(peak.cost_diesel_only_usd)} on diesel only.")
with b:
    card("Backup with no fuel", f"{r.backup_hours:,.0f} h",
         sub=f"Critical load ({i.critical_load_kw:g} kW: clinic, radio) on a full battery.")

# --------------------------------------------------------------- g. exports ---
st.subheader("Share the plan")
a, b = st.columns(2)
proposal, onepager = build_proposal(r, plan), build_onepager(r, plan)
stretch(a.download_button, "Download funding proposal (.md)", proposal, "sunsafe_funding_proposal.md")
stretch(b.download_button, "Download community one-pager (.md)", onepager, "sunsafe_community_onepager.md")
with st.expander("Preview the funding proposal"):
    st.markdown(proposal)
with st.expander(f"Model notes and assumptions ({len(r.warnings)})"):
    for w in r.warnings:
        st.markdown(f"- {w}")
