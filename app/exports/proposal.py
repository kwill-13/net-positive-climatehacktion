"""Markdown exports built from a sunsafe.interface.Results plus the app's plan bundle. Swap for PDF later."""
from utils.formatting import money, pct, tco2, years


def _schedule(r):
    """Upgrade schedule lines from Results.plan_stages (first entry = the initial build)."""
    chem = r.inputs.battery_chemistry.replace("_", "-")
    lines = []
    for s in r.plan_stages[1:]:
        what = (f"add {s.pv_added_kw:,.0f} kWp solar and a new {s.battery_installed_kwh:,.0f} kWh {chem} battery"
                if s.pv_added_kw > 0.5 else f"replace the battery ({s.battery_installed_kwh:,.0f} kWh {chem})")
        lines.append(f"- Year {s.year}: {what}, about {money(s.capex_usd)}")
    return lines


def _breakeven(x, curve, plan):
    """Where a hybrid cost line beats diesel on the USD 1.00-3.50/L range."""
    if x is not None:
        return f"above ${x:.2f}/L"
    return "at no price up to $3.50/L" if curve[-1] > plan["cost_diesel"][-1] else "at every price from $1.00/L"


def build_proposal(r, plan):
    i, z, f, h = r.inputs, r.sizing, r.finance, r.headroom
    last = r.lifecycle[-1]
    ap = plan["at_price"]
    schedule = _schedule(r) or [f"- None needed: the first build holds the target through year {i.project_years}."]
    saving = plan["saving_vs_a"]
    return f"""# SunSafe Funding Proposal: {i.site_name}

## Project overview
Diesel-to-solar mini-grid plan for {i.site_name} ({i.latitude:.2f}, {i.longitude:.2f}), planned to meet
{pct(i.renewable_target)} renewable electricity in every year of a {i.project_years}-year project.
Planning estimate: SunSafe's engine is checked against Tokelau's measured performance; site data should be
confirmed before procurement.

## Current energy situation
{i.diesel_litres_per_day:,.0f} L/day of diesel at ${i.diesel_price_per_litre:.2f}/L delivered.
Demand growth assumed: {plan['growth_label']}.

## Build now
{z.pv_kw:,.0f} kWp solar and {z.battery_kwh:,.0f} kWh {i.battery_chemistry.replace('_', '-')} battery,
capex {money(z.capex_usd)}. Year-1 renewable share {pct(z.renewable_share_year1)}.

## Upgrade schedule
{chr(10).join(schedule)}

Strategy: {plan['rec_name']}.{f" {saving:.0%} cheaper over the project than building big on day one." if saving and saving > 0.0005 else ""}
Without reinvestment the renewable share falls to {pct(last.share_funded_day_one)} by year {last.year};
with the schedule above it holds at {pct(last.share_funded_year_15)}.

## Financial case
| Cost per kWh at ${i.diesel_price_per_litre:.2f}/L | USD/kWh |
|---|---:|
| Diesel only | {ap['diesel']:.2f} |
| Full hybrid cost (all capex) | {ap['full']:.2f} |
| Island-paid, if donors fund the first build | {ap['island']:.2f} |

Island-paid = O&M, later upgrades, and generator fuel and O&M. The hybrid beats diesel
{_breakeven(plan['breakeven_full'], plan['cost_full'], plan)} on full cost and
{_breakeven(plan['breakeven_island'], plan['cost_island'], plan)} for the island.
Set aside {money(f.om_fund_per_year_usd)}/year for O&M and the first upgrade. Simple payback: {years(f.payback_years)}.

## Fuel-price risk and resilience
See the fuel-shock replay in the app. Critical load backup: {r.backup_hours:,.0f} hours without fuel.

## Electrification opportunities
Electricity share of local energy use: {pct(h.electricity_share_before)} → {pct(h.electricity_share_after)}.
Suggested new loads: {'; '.join(h.suggested_new_loads)}.

## Expected impact
{z.diesel_litres_avoided_year1:,.0f} L diesel avoided in year 1 (about {tco2(z.diesel_litres_avoided_year1):,.0f} tCO2e).

## Next steps
Confirm site demand and delivered diesel price, agree who funds the first build and each upgrade, and set up the O&M fund.
"""


def build_onepager(r, plan):
    i, z, h = r.inputs, r.sizing, r.headroom
    ap = plan["at_price"]
    schedule = _schedule(r)
    upgrades = ("\n".join(f"  {line}" for line in schedule) if schedule
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
