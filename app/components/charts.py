"""Plan charts (Altair), shared by the "Your plan" page and the funding-proposal export.

Each builder takes the plan bundle from layout.run_plan() and returns (chart, caption). The chart
title states the finding with numbers from the run; the caption names the decision it supports.
Conventions: year axes run 1..project_years, lines are labelled at their end (no legends), and
colours are fixed: plan green, without reinvestment grey, diesel amber.
"""
import textwrap

import altair as alt
import pandas as pd

PLAN = "#2e7d32"        # the plan (green)
PLAN_LIGHT = "#81c784"  # island-paid / solar output (light green)
WITHOUT = "#9a9a9a"     # without reinvestment (grey)
DIESEL = "#d08c1b"      # diesel (amber)
INK = "#2b2b2b"
MUTED = "#666666"


# ------------------------------------------------------------------ helpers ---

def _title(text, sub=None):
    # Wrapped by hand (Vega titles don't wrap) for a ~440 px chart: an 800 px window with the sidebar open.
    # limit=0 stops Vega shortening a line with "...".
    lines = textwrap.wrap(text, 46)
    kw = dict(text=lines, anchor="start", fontSize=15, fontWeight="bold", color=INK, offset=10, limit=0)
    if sub:
        kw.update(subtitle=textwrap.wrap(sub, 64), subtitleColor=MUTED, subtitleFontSize=12)
    return alt.TitleParams(**kw)


def fit_width(chart):
    """Width fits the container; height stays the plot's own height, so long titles add space instead of
    squeezing the plot (Streamlit's default autosize counts titles and labels inside `height`)."""
    return chart.properties(autosize=alt.AutoSizeParams(type="fit-x", contains="padding"),
                            padding={"left": 8, "right": 4, "top": 4, "bottom": 4})   # room for y-axis titles


FONT = '"Source Sans", "Source Sans Pro", "Source Sans 3", -apple-system, "Segoe UI", Helvetica, Arial, sans-serif'


def themed(chart):
    """One look for every chart (app and proposal): the app's font, the same label sizes, light gridlines,
    no frame, transparent background. Styling only: data, titles and labels are unchanged."""
    return (chart.configure(font=FONT, background="transparent")
            .configure_view(stroke=None)
            .configure_axis(labelFontSize=11.5, titleFontSize=12, titleFontWeight="normal", labelColor="#555555",
                            titleColor="#555555", gridColor="#ecebe6", domainColor="#cfcac0", tickColor="#cfcac0")
            .configure_title(font=FONT, anchor="start", subtitleFont=FONT)
            .configure_text(font=FONT))


def _usd(x):
    return f"${x / 1e6:,.2f}M" if abs(x) >= 1e6 else f"${x / 1e3:,.0f}k"


def _years_x(n, title="Year of operation"):
    return alt.X("Year:Q", title=title, scale=alt.Scale(domain=[1, n], nice=False),
                 axis=alt.Axis(values=list(range(1, n + 1)), format="d", grid=False))


def _end_labels(df, x, y, series, colors, gap=0.07):
    """Line names just right of each line's last point (Vega's autosize makes room), spread
    vertically so they never overlap each other. Keep names short; details go in the caption."""
    last = df.sort_values(x).groupby(series, as_index=False).last()
    last = last[last[series].isin(list(colors))].sort_values(y)
    span = float(df[y].max() - df[y].min()) or 1.0
    ys, prev = [], None
    for v in last[y]:
        prev = v if prev is None else max(v, prev + gap * span)
        ys.append(prev)
    last = last.assign(_ly=ys)
    return [alt.Chart(last[last[series] == name]).mark_text(align="left", dx=8, baseline="middle", fontWeight="bold",
                                                            color=color).encode(x=f"{x}:Q", y="_ly:Q", text=f"{series}:N")
            for name, color in colors.items() if (last[series] == name).any()]


def _lines(df, x, y, series, colors, dashes=None, n=None, y_title=None, y_scale=None, x_enc=None):
    dashes = dashes or {}
    enc = dict(
        x=x_enc if x_enc is not None else _years_x(n),
        y=alt.Y(f"{y}:Q", title=y_title or y, scale=y_scale or alt.Scale(zero=False)),
        color=alt.Color(f"{series}:N", scale=alt.Scale(domain=list(colors), range=list(colors.values())), legend=None),
        strokeDash=alt.StrokeDash(f"{series}:N", scale=alt.Scale(domain=list(colors),
                                  range=[dashes.get(k, [1, 0]) for k in colors]), legend=None),
        tooltip=[f"{series}:N", alt.Tooltip(f"{x}:Q", format=".2f" if x_enc is not None else "d"),
                 alt.Tooltip(f"{y}:Q", format=",.1f")],
    )
    return alt.Chart(df).mark_line(point=alt.OverlayMarkDef(size=25), strokeWidth=2.5).encode(**enc)


def _upgrade_rules(plan, label=True):
    ups = plan["upgrade_years"]
    if not ups:
        return []
    u = pd.DataFrame({"Year": ups, "t": [f"Upgrade, yr {y}" for y in ups]})
    rules = alt.Chart(u).mark_rule(color=PLAN, strokeDash=[3, 3], opacity=0.7).encode(x="Year:Q")
    if not label:
        return [rules]
    text = alt.Chart(u).mark_text(align="left", dx=3, baseline="top", color=PLAN, fontSize=11).encode(
        x="Year:Q", y=alt.value(2), text="t:N")
    return [rules, text]


def _upgrade_words(years):
    if len(years) == 1:
        return f"the year-{years[0]} upgrade"
    return "the year " + ", ".join(str(y) for y in years[:-1]) + f" and {years[-1]} upgrades"


# ------------------------------------------------------------------- charts ---

def investment_timeline(plan):
    """1. Your investment plan: one marker per stage, labelled with what is installed and its cost."""
    r = plan["results"]
    n = r.inputs.project_years
    chem = r.inputs.battery_chemistry.replace("_", "-")
    from components.layout import usable_fraction   # here, not at import: layout imports Streamlit
    usable = usable_fraction(plan)
    rows = []
    for k, s in enumerate(r.plan_stages):
        batt = f"{s.battery_installed_kwh:,.0f} kWh ({s.battery_installed_kwh * usable:,.0f} usable)"
        if k == 0:
            what = f"Build\n{s.pv_added_kw:,.0f} kWp + {batt}"
        elif s.pv_added_kw > 0.5:
            what = f"Year {s.year}\n+{s.pv_added_kw:,.0f} kWp, new {batt}"
        else:
            what = f"Year {s.year}\nnew battery {batt}"
        rows.append(dict(Year=s.year, y=0, what=what, cost=_usd(s.capex_usd), usd=s.capex_usd,
                         ly=0.75 if k % 2 == 0 else -0.6, base="bottom" if k % 2 == 0 else "top",
                         align="left" if s.year < 0.45 * n else "right"))   # labels past mid-project grow leftwards
    df = pd.DataFrame(rows)
    later = r.plan_stages[1:]
    total_later = sum(s.capex_usd for s in later)
    title = (f"Your investment plan: {_usd(r.plan_stages[0].capex_usd)} to build, then "
             + (f"{_usd(total_later)} in year {later[0].year}" if len(later) == 1 else
                f"{len(later)} upgrades (years {', '.join(str(s.year) for s in later)}) totalling {_usd(total_later)}"
                if later else "no upgrades needed"))
    axis = alt.Chart(pd.DataFrame({"Year": [1, n], "y": [0, 0]})).mark_line(color="#cfcac0", strokeWidth=3).encode(
        x=_years_x(n), y=alt.Y("y:Q", axis=None, scale=alt.Scale(domain=[-1.9, 1.9])))
    dots = alt.Chart(df).mark_point(filled=True, color=PLAN, opacity=1).encode(
        x="Year:Q", y="y:Q", size=alt.Size("usd:Q", scale=alt.Scale(range=[120, 600]), legend=None),
        tooltip=["what:N", "cost:N"])
    labels = []
    for row in rows:
        one = pd.DataFrame([row])
        labels.append(alt.Chart(one).mark_text(align=row["align"], baseline=row["base"], fontSize=12,
                                               color=INK, lineBreak="\n").encode(
            x="Year:Q", y="ly:Q", text=alt.value(f"{row['what']}\n{row['cost']}")))
    chart = alt.layer(axis, dots, *labels).properties(height=250, title=_title(title))
    caption = (f"Decision: what to fund now and what to budget later. Each marker is an investment: kWp of solar "
               f"added and kWh of new {chem} battery, with its cost (marker size). Upgrade costs are at that "
               "year's prices (batteries assumed to get 4%/yr cheaper).")
    return chart, caption


def renewable_share(plan):
    """2. Hero: renewable share by year, with the plan vs without reinvestment."""
    r = plan["results"]
    n, target = r.inputs.project_years, r.inputs.renewable_target
    yrs = pd.DataFrame(plan["years"])
    ups = plan["upgrade_years"]
    names = {"With upgrades": PLAN, "Never upgraded": WITHOUT} if ups else {"The plan": PLAN}
    parts = [pd.DataFrame({"Year": yrs.year, "Share": yrs.share_plan * 100, "Line": list(names)[0]})]
    if ups:   # grey first, so the plan line is drawn on top where they coincide
        parts.insert(0, pd.DataFrame({"Year": yrs.year, "Share": yrs.share_without * 100,
                                      "Line": "Never upgraded"}))
    df = pd.concat(parts)
    low = min(df.Share.min(), target * 100)
    lines = _lines(df, "Year", "Share", "Line", names, n=n, y_title="Solar share (%)",
                   y_scale=alt.Scale(domain=[max(low - 4, 0), 101], nice=False))
    tline = alt.Chart(pd.DataFrame({"y": [target * 100]})).mark_rule(strokeDash=[6, 4], color=MUTED).encode(y="y:Q")
    tlabel = alt.Chart(pd.DataFrame({"y": [target * 100], "Year": [1], "t": [f"Target {target:.0%}"]})).mark_text(
        align="left", dx=3, dy=-7, color=MUTED).encode(x="Year:Q", y="y:Q", text="t:N")
    plan_min, last_without = yrs.share_plan.min(), yrs.share_without.iloc[-1]
    if ups:
        title = (f"Without {_upgrade_words(ups)}, solar share falls to {last_without:.0%} by year {n}; "
                 f"with {'the upgrade' if len(ups) == 1 else 'the upgrades'} it stays at or above {plan_min:.0%}")
    else:
        title = f"The first build keeps solar share at or above {plan_min:.0%} through year {n}"
    chart = alt.layer(lines, tline, tlabel, *_upgrade_rules(plan),
                      *_end_labels(df, "Year", "Share", "Line", names)
                      ).properties(height=320, title=_title(title))
    caption = (f"Decision: fund the upgrades on schedule. Green = the plan with its upgrades; grey = the first "
               f"build only, never upgraded. Target {target:.0%} renewable in every year; year 1 can sit above it "
               "because the build is sized to last until the first upgrade.")
    return chart, caption


def night_coverage(plan):
    """3. Why the upgrade years: nights of backup = usable battery / one night's demand (18:00-06:00)."""
    r = plan["results"]
    n = r.inputs.project_years
    yrs = pd.DataFrame(plan["years"])
    ups = plan["upgrade_years"]
    main = "With upgrades" if ups else "The plan"
    names = {main: PLAN}
    if ups:
        names["Never upgraded"] = WITHOUT
    df = pd.concat([   # grey first, so the plan line is drawn on top where they coincide
        pd.DataFrame({"Year": yrs.year, "Nights": yrs.night_without / 100, "Line": "Never upgraded"}) if ups else None,
        pd.DataFrame({"Year": yrs.year, "Nights": yrs.night_plan / 100, "Line": main}),
    ])
    lines = _lines(df, "Year", "Nights", "Line", names, n=n, y_title="Nights of backup",
                   y_scale=alt.Scale(domain=[0, max(1.2, float(df.Nights.max()) * 1.08)], nice=False))
    ref = alt.Chart(pd.DataFrame({"y": [1.0]})).mark_rule(color=MUTED, strokeDash=[2, 2]).encode(y="y:Q")
    reflabel = alt.Chart(pd.DataFrame({"y": [1.0], "Year": [1], "t": ["1 night"]})).mark_text(
        align="left", dx=3, dy=-7, color=MUTED).encode(x="Year:Q", y="y:Q", text="t:N")
    nights = yrs.night_plan / 100
    start = float(nights.iloc[0])
    if ups:
        before = ups[0] - 1
        x = float(nights.iloc[before - 1])
        after = float(nights.iloc[ups[0] - 1])
        title = (f"The battery's backup falls from {start:.1f} nights to {'only ' if x < 1 else ''}{x:.1f} by "
                 f"year {before}; the year-{ups[0]} upgrade restores {after:.1f} nights")
        low = min(float(nights.iloc[u - 2]) for u in ups)
        why = (f" Upgrades come at about {low:.1f} nights, not 1: on cloudy days the battery also stands in for "
               "missing daytime sun, so it needs a margin above one average night." if low >= 1 else "")
    else:
        title = (f"The battery's backup falls from {start:.1f} to {float(nights.iloc[-1]):.1f} nights by year {n}, "
                 "still enough for the target")
        why = ""
    sub = f"1 night = 18:00-06:00 demand ({plan['night_share']:.0%} of a day's demand)"
    chart = alt.layer(lines, ref, reflabel, *_upgrade_rules(plan), *_end_labels(df, "Year", "Nights", "Line", names)
                      ).properties(height=320, title=_title(title, sub))
    solar = yrs.solar_plan
    caption = ("Decision: when to schedule each upgrade. Green = with the plan's upgrades; grey = the first battery, "
               f"never replaced. Nights of backup = usable battery after fading / that night's demand.{why} "
               f"Daytime solar is not the limit: yearly solar output stays at {solar.min():.0f}-"
               f"{solar.max():.0f}% of yearly demand. What runs out is battery storage for the night.")
    return chart, caption


def fund_balance(plan):
    """4a. The yearly fund: balance saved toward upgrades vs each upgrade's cost."""
    r = plan["results"]
    n = r.inputs.project_years
    fund = pd.DataFrame(plan["fund"]).rename(columns={"year": "Year", "balance": "Balance"})
    fund["Line"] = "Fund"
    ups = plan["fund_upgrades"]
    dep, om = plan["fund_deposit"], plan["om_year1"]
    if not ups:
        title = f"No upgrades to save for: the {_usd(om + dep)}/yr set-aside covers O&M only"
    else:
        short = [u for u in ups if u["shortfall"] > 1]
        covered = [u for u in ups if u["shortfall"] <= 1]
        title = (f"Saving {_usd(dep)}/yr covers {_upgrade_words([u['year'] for u in covered])} "
                 f"({', '.join(_usd(u['cost']) for u in covered)})"
                 if len(short) < len(ups) else f"Saving {_usd(dep)}/yr does not cover the upgrades")
        if short:
            title += "; " + "; ".join(f"year {u['year']} is {_usd(u['shortfall'])} short" for u in short)
    line = _lines(fund, "Year", "Balance", "Line", {"Fund": PLAN}, n=n, y_title="Saved (USD)",
                  y_scale=alt.Scale(zero=True))
    # step-after: the balance holds through each year and the upgrade's withdrawal is a vertical drop at its year
    line = line.mark_line(interpolate="step-after", point=alt.OverlayMarkDef(size=25), strokeWidth=2.5).encode(
        y=alt.Y("Balance:Q", title="Saved (USD)", scale=alt.Scale(zero=True), axis=alt.Axis(format="$.2~s")))
    layers = [line]
    if ups and ups[-1]["year"] < n:      # saving continues after the last upgrade: say what it is for
        end = fund.tail(1)
        layers.append(alt.Chart(end).mark_text(align="right", baseline="bottom", dx=-6, dy=-6, fontWeight="bold",
                                               color=PLAN, lineBreak="\n").encode(   # two short lines: narrow charts
            x="Year:Q", y="Balance:Q", text=alt.value("Reserve toward the\nnext replacement")))
    else:
        layers += _end_labels(fund, "Year", "Balance", "Line", {"Fund": PLAN})
    for u in ups:
        c = pd.DataFrame({"y": [u["cost"]], "Year": [1], "t": [f"Year-{u['year']} upgrade {_usd(u['cost'])}"]})
        layers.append(alt.Chart(c).mark_rule(color=PLAN, strokeDash=[6, 4], opacity=0.6).encode(y="y:Q"))
        layers.append(alt.Chart(c).mark_text(align="left", dx=3, dy=-7, color=PLAN).encode(x="Year:Q", y="y:Q", text="t:N"))
    chart = alt.layer(*layers, *_upgrade_rules(plan, label=False)).properties(
        height=300, title=_title(title, f"Set aside {_usd(om + dep)}/yr: {_usd(om)} O&M spent each year + "
                                        f"{_usd(dep)} saved at {plan['discount_rate']:.0%} interest."))
    caption = ("Decision: how much to set aside each year. The saving is sized for the first upgrade and assumed "
               "to continue afterwards; any shortfall for later upgrades needs another funding round.")
    return chart, caption


def cost_bars(plan):
    """4b. Cost per kWh at the current diesel price: diesel only, full hybrid, island-paid."""
    r = plan["results"]
    ap, price = plan["at_price"], r.inputs.diesel_price_per_litre
    df = pd.DataFrame({"Cost": ["Diesel only", "Full hybrid", "Island-paid"],
                       "USD/kWh": [ap["diesel"], ap["full"], ap["island"]]})
    colors = [DIESEL, PLAN, PLAN_LIGHT]
    bars = alt.Chart(df).mark_bar().encode(
        y=alt.Y("Cost:N", sort=list(df.Cost), title=None, axis=alt.Axis(labelLimit=0)),
        x=alt.X("USD/kWh:Q", title="USD per kWh"),
        color=alt.Color("Cost:N", scale=alt.Scale(domain=list(df.Cost), range=colors), legend=None),
        tooltip=["Cost", alt.Tooltip("USD/kWh:Q", format="$.3f")])
    text = bars.mark_text(align="left", dx=4, color=INK).encode(text=alt.Text("USD/kWh:Q", format="$.2f"))
    cheaper = ap["island"] < ap["diesel"]
    title = (f"At ${price:.2f}/L the island pays ${ap['island']:.2f}/kWh if donors fund the first build, "
             f"{'vs' if cheaper else 'more than'} ${ap['diesel']:.2f}/kWh on diesel")
    chart = (bars + text).properties(height=150, title=_title(title))
    caption = ("Decision: who pays for the first build. Full hybrid = every cost including the first build. "
               "Island-paid = what the island pays if donors fund the first build: O&M, later upgrades, and "
               "generator fuel and O&M. Lifetime average cost per kWh.")
    return chart, caption


def strategy_npv(plan):
    """Alternatives: cheapest version of each strategy, present-value cost."""
    n = plan["results"].inputs.project_years
    strat = pd.DataFrame(plan["strategies"])
    strat["Strategy"] = strat.label + strat.feasible.map({True: "", False: " (misses target)"})
    strat["NPV ($M)"] = strat.npv / 1e6
    strat["Pick"] = strat.recommended.map({True: "Recommended", False: "Other"})
    bars = alt.Chart(strat).mark_bar().encode(
        y=alt.Y("Strategy:N", sort=list(strat.Strategy), title=None, axis=alt.Axis(labelLimit=0)),
        x=alt.X("NPV ($M):Q", title=f"{n}-yr cost, USD M"),
        color=alt.Color("Pick:N", scale=alt.Scale(domain=["Recommended", "Other"], range=[PLAN, "#cfcac0"]), legend=None),
        tooltip=["Strategy", "name", alt.Tooltip("NPV ($M):Q", format=".2f")])
    labels = bars.mark_text(align="left", dx=4, color=INK).encode(text=alt.Text("NPV ($M):Q", format="$.2f"))
    rec = next(x for x in plan["strategies"] if x["recommended"])
    saving = plan["saving_vs_a"]
    if saving is not None and saving > 0.0005:
        title = f"{rec['label']} costs {_usd(rec['npv'])} over {n} years, {saving:.0%} less than building big"
    else:
        title = f"{rec['label']} is the cheapest plan over {n} years ({_usd(rec['npv'])})"
    chart = (bars + labels).properties(height=190, title=_title(title))
    caption = ("Decision: which strategy to fund. Each bar is the cheapest version of that strategy that meets "
               "the target every year: present value at 8% of build, O&M, upgrades, and generator fuel and O&M.")
    return chart, caption


def price_breakeven(plan):
    """Alternatives: cost per kWh across diesel prices, with both breakevens."""
    r = plan["results"]
    names = {"Diesel only": DIESEL, "Full hybrid": PLAN, "Island-paid": PLAN_LIGHT}
    df = pd.DataFrame({"Price": plan["prices"], "Diesel only": plan["cost_diesel"],
                       "Full hybrid": plan["cost_full"], "Island-paid": plan["cost_island"]})
    df = df.melt("Price", var_name="Line", value_name="USD/kWh")
    x = alt.X("Price:Q", title="Diesel price (USD/L)", scale=alt.Scale(domain=[1, 3.5], nice=False))
    lines = alt.Chart(df).mark_line(strokeWidth=2.5).encode(
        x=x, y=alt.Y("USD/kWh:Q", title="USD per kWh"),
        color=alt.Color("Line:N", scale=alt.Scale(domain=list(names), range=list(names.values())), legend=None),
        tooltip=["Line", alt.Tooltip("Price:Q", format="$.2f"), alt.Tooltip("USD/kWh:Q", format="$.3f")])
    marks = [dict(x=r.inputs.diesel_price_per_litre, t=f"You ${r.inputs.diesel_price_per_litre:.2f}", c=MUTED,
                  align="right", dx=-3)]
    for key, label, c in (("breakeven_full", "Breakeven", PLAN), ("breakeven_island", "Island", PLAN_LIGHT)):
        if plan[key] is not None:
            marks.append(dict(x=plan[key], t=f"{label} ${plan[key]:.2f}", c=c, align="left", dx=3))
    rules = alt.Chart(pd.DataFrame([dict(x=m["x"], c=m["c"]) for m in marks])).mark_rule(strokeDash=[2, 3]).encode(
        x="x:Q", color=alt.Color("c:N", scale=None))
    texts = [alt.Chart(pd.DataFrame([dict(x=m["x"], t=m["t"])])).mark_text(
        align=m["align"], dx=m["dx"], baseline="top", color=m["c"]).encode(x="x:Q", y=alt.value(2 + 15 * k), text="t:N")
        for k, m in enumerate(marks)]
    be = plan["breakeven_full"]
    title = (f"On full cost the hybrid beats diesel above ${be:.2f}/L" if be is not None else
             "On full cost the hybrid " + ("beats diesel at every price from $1.00/L" if plan["cost_full"][-1] < plan["cost_diesel"][-1]
                                           else "does not beat diesel below $3.50/L"))
    bi = plan["breakeven_island"]
    title += (f"; for the island, above ${bi:.2f}/L" if bi is not None else
              "; for the island, at every price shown" if plan["cost_island"][0] < plan["cost_diesel"][0] else
              "; for the island, at no price shown")
    chart = alt.layer(lines, rules, *texts,
                      *_end_labels(df, "Price", "USD/kWh", "Line", names)
                      ).properties(height=300, title=_title(title))
    caption = ("Decision: how exposed the case is to diesel prices. Lines: diesel only (amber), full hybrid cost "
               "(green), island-paid if donors fund the first build (light green). Markers: your price and the "
               "breakevens. The plan is fixed; only the price changes.")
    return chart, caption


def fuel_shock(plan):
    """Risks: replay of 2026's monthly diesel prices, monthly bill with and without the plan."""
    r = plan["results"]
    fs = pd.DataFrame([vars(m) for m in r.fuel_shock])
    fs["Month"] = range(1, len(fs) + 1)
    month_names = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    fs["short"] = [month_names[int(m.split("-")[1]) - 1] for m in fs.month]
    names = {"Diesel only": DIESEL, "With solar": PLAN}
    df = pd.concat([pd.DataFrame({"Month": fs.Month, "label": fs.month, "USD": fs.cost_diesel_only_usd, "Line": "Diesel only"}),
                    pd.DataFrame({"Month": fs.Month, "label": fs.month, "USD": fs.cost_hybrid_usd, "Line": "With solar"})])
    x = alt.X("Month:Q", title="Month (2026)", scale=alt.Scale(domain=[1, len(fs)], nice=False),
              axis=alt.Axis(values=list(fs.Month), labelExpr=" ".join(
                  f"datum.value == {m} ? '{lab}' :" for m, lab in zip(fs.Month, fs.short)) + " ''"))
    lines = _lines(df, "Month", "USD", "Line", names, x_enc=x, y_title="USD per month", y_scale=alt.Scale(zero=True))
    peak = fs.loc[fs.diesel_price_per_litre.idxmax()]
    title = (f"At the {peak.short} 2026 price peak (${peak.diesel_price_per_litre:.2f}/L), the monthly bill is "
             f"{_usd(peak.cost_hybrid_usd)} with the plan vs {_usd(peak.cost_diesel_only_usd)} on diesel only")
    chart = alt.layer(lines, *_end_labels(df, "Month", "USD", "Line", names)
                      ).properties(height=260, title=_title(title))
    caption = ("Decision: how much fuel-price risk the plan removes. Monthly generator bill, diesel only vs with "
               "solar, replaying 2026's Apia price swings applied to your price.")
    return chart, caption


