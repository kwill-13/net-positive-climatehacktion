"""Exports built from a sunsafe.interface.Results plus the app's plan bundle.

- Funding proposal: one self-contained HTML file with the same charts as the "Your plan" page
  (Altair specs rendered by vega-embed from the jsDelivr CDN; print to PDF from a browser).
- Community one-pager: Markdown.
"""
import html
import json

import altair as alt

from components import charts
from utils.formatting import money, pct, tco2, years

_VEGA = getattr(alt, "VEGA_VERSION", "5").split(".")[0]
_VEGALITE = getattr(alt, "VEGALITE_VERSION", "5")
_EMBED = getattr(alt, "VEGAEMBED_VERSION", "6").split(".")[0]


def _schedule(r):
    """Upgrade schedule lines from Results.plan_stages (first entry = the initial build)."""
    chem = r.inputs.battery_chemistry.replace("_", "-")
    lines = []
    for s in r.plan_stages[1:]:
        what = (f"add {s.pv_added_kw:,.0f} kWp solar and a new {s.battery_installed_kwh:,.0f} kWh {chem} battery"
                if s.pv_added_kw > 0.5 else f"replace the battery ({s.battery_installed_kwh:,.0f} kWh {chem})")
        lines.append(f"Year {s.year}: {what}, about {money(s.capex_usd)}")
    return lines


def _breakeven(x, curve, plan):
    """Where a hybrid cost line beats diesel on the USD 1.00-3.50/L range."""
    if x is not None:
        return f"above ${x:.2f}/L"
    return "at no price up to $3.50/L" if curve[-1] > plan["cost_diesel"][-1] else "at every price from $1.00/L"


def _chart(builder, plan, k):
    chart, caption = builder(plan)
    spec = charts.fit_width(chart).properties(width=560).to_json(indent=None).replace("</", "<\\/")   # + labels fits 780 px
    return (f'<figure><div id="chart{k}"></div><figcaption>{html.escape(caption)}</figcaption></figure>'
            f'<script>vegaEmbed("#chart{k}", {spec}, {{actions: false, renderer: "svg"}});</script>')


_CSS = """body{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;color:#2b2b2b;max-width:820px;
margin:32px auto;padding:0 20px;line-height:1.5}h1{font-size:1.7rem;margin-bottom:4px}
h2{font-size:1.15rem;margin-top:28px;border-bottom:1px solid #e0ddd5;padding-bottom:4px}
.meta{color:#666}figure{margin:16px 0 24px}figcaption{color:#666;font-size:.85rem;margin-top:4px}
table{border-collapse:collapse}td,th{border:1px solid #e0ddd5;padding:4px 10px;text-align:left}
td.n{text-align:right}.note{background:#f4f8f4;border-left:4px solid #2e7d32;padding:8px 12px}
@media print{figure{break-inside:avoid}}"""


def build_proposal(r, plan):
    """Funding proposal as one HTML document (string)."""
    i, z, f, h = r.inputs, r.sizing, r.finance, r.headroom
    e = html.escape
    ap = plan["at_price"]
    sched = _schedule(r) or [f"None needed: the first build holds the target through year {i.project_years}."]
    saving = plan["saving_vs_a"]
    k = iter(range(100))
    chart = lambda b: _chart(b, plan, next(k))
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>SunSafe funding proposal: {e(i.site_name)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/vega@{_VEGA}"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-lite@{_VEGALITE}"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-embed@{_EMBED}"></script>
<style>{_CSS}</style></head><body>
<h1>SunSafe funding proposal: {e(i.site_name)}</h1>
<p class="meta">({i.latitude:.2f}, {i.longitude:.2f}) · {i.diesel_litres_per_day:,.0f} L/day diesel at
${i.diesel_price_per_litre:.2f}/L delivered · target {pct(i.renewable_target)} renewable in every year ·
{i.project_years} years · demand growth {e(plan['growth_label'])}</p>
<p class="note">Planning estimate. SunSafe's engine is checked against Tokelau's measured performance;
confirm site demand and diesel price before procurement.</p>

<h2>The plan</h2>
<p>Build {z.pv_kw:,.0f} kWp solar and a {z.battery_kwh:,.0f} kWh {e(i.battery_chemistry.replace('_', '-'))}
battery now (capex {money(z.capex_usd)}), then:</p>
<ul>{''.join(f'<li>{e(s)}</li>' for s in sched)}</ul>
<p>Strategy: {e(plan['rec_name'])}.{f" {saving:.0%} cheaper over the project than building big on day one." if saving and saving > 0.0005 else ""}</p>
{chart(charts.investment_timeline)}

<h2>It still works in the final year</h2>
{chart(charts.renewable_share)}
{chart(charts.night_coverage)}

<h2>Who pays</h2>
<table><tr><th>Cost per kWh at ${i.diesel_price_per_litre:.2f}/L</th><th>USD/kWh</th></tr>
<tr><td>Diesel only</td><td class="n">{ap['diesel']:.2f}</td></tr>
<tr><td>Full hybrid cost (all capex)</td><td class="n">{ap['full']:.2f}</td></tr>
<tr><td>Island-paid, if donors fund the first build</td><td class="n">{ap['island']:.2f}</td></tr></table>
<p>Island-paid = O&amp;M, later upgrades, and generator fuel and O&amp;M. The hybrid beats diesel
{_breakeven(plan['breakeven_full'], plan['cost_full'], plan)} on full cost and
{_breakeven(plan['breakeven_island'], plan['cost_island'], plan)} for the island.
Set aside {money(f.om_fund_per_year_usd)}/year for O&amp;M and the first upgrade. Simple payback: {years(f.payback_years)}.</p>
{chart(charts.cost_bars)}
{chart(charts.fund_balance)}

<h2>Fuel-price risk and resilience</h2>
{chart(charts.fuel_shock)}
<p>Critical load backup: {r.backup_hours:,.0f} hours without fuel ({i.critical_load_kw:g} kW: clinic, radio).</p>

<h2>Electrification opportunities</h2>
<p>Electricity share of local energy use: {pct(h.electricity_share_before)} → {pct(h.electricity_share_after)}.
Suggested new loads: {e('; '.join(h.suggested_new_loads))}.</p>

<h2>Expected impact</h2>
<p>{z.diesel_litres_avoided_year1:,.0f} L diesel avoided in year 1 (about {tco2(z.diesel_litres_avoided_year1):,.0f} tCO2e).</p>

<h2>Alternatives we considered</h2>
{chart(charts.strategy_npv)}
{chart(charts.price_breakeven)}

<h2>Next steps</h2>
<p>Confirm site demand and delivered diesel price, agree who funds the first build and each upgrade, and set up
the O&amp;M fund.</p>
<p class="meta">Generated by SunSafe. Assumptions and sources: SOURCES.md in the project repository.</p>
</body></html>"""


def build_onepager(r, plan):
    i, z, h = r.inputs, r.sizing, r.headroom
    ap = plan["at_price"]
    schedule = _schedule(r)
    upgrades = ("\n".join(f"  - {line}" for line in schedule) if schedule
                else "  - No upgrades needed during the project.")
    return f"""# {i.site_name}: Our Solar Plan

- New solar panels ({z.pv_kw:,.0f} kW) and a battery ({z.battery_kwh:,.0f} kWh).
- About {pct(z.renewable_share_year1)} of our power comes from the sun, and the plan keeps it above
  {pct(i.renewable_target)} every year for {i.project_years} years.
- Planned upgrades as our island uses more power:
{upgrades}
- If donors pay for the first build, our power costs about ${ap['island']:.2f} per kWh,
  compared with ${ap['diesel']:.2f} per kWh running on diesel.
- We save about {z.diesel_litres_avoided_year1:,.0f} litres of diesel in the first year.
- Money is set aside every year for maintenance and the next upgrade.
- The clinic and radio can stay on for about {r.backup_hours:,.0f} hours with no fuel.
- Extra clean power could run: {'; '.join(h.suggested_new_loads)}.
"""
