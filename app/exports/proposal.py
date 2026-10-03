"""Markdown exports built from a sunsafe.interface.Results. Swap for PDF later."""
from utils.formatting import money, pct, tco2, years


def build_proposal(r):
    i, z, f, h = r.inputs, r.sizing, r.finance, r.headroom
    last = r.lifecycle[-1]
    return f"""# SunSafe Funding Proposal — {i.site_name}
{"**DEMO — illustrative numbers, not an engineering recommendation.**" if any("FAKE" in w for w in r.warnings) else ""}

## Project overview
Diesel-to-solar transition planning for {i.site_name} ({i.latitude:.2f}, {i.longitude:.2f}).

## Current energy situation
{i.diesel_litres_per_day:,.0f} L/day of diesel at ${i.diesel_price_per_litre:.2f}/L.

## Proposed system
{z.pv_kw:,.0f} kW solar and {z.battery_kwh:,.0f} kWh {i.battery_chemistry.replace('_', ' ')} battery.
Year-1 renewable share {pct(z.renewable_share_year1)}.

## Lifecycle plan ({i.project_years} years)
Without battery replacement the renewable share falls to {pct(last.share_funded_day_one)} by year {last.year};
funded for year 15 it holds at {pct(last.share_funded_year_15)}. O&M and replacement fund: {money(f.om_fund_per_year_usd)}/year.

## Financial case
Capex {money(z.capex_usd)}. Cost per kWh: ${f.cost_per_kwh_hybrid_usd:.2f} hybrid vs ${f.cost_per_kwh_diesel_usd:.2f} diesel. Payback: {years(f.payback_years)}.

## Fuel-price risk and resilience
See the fuel-shock replay in the app. Critical load backup: {r.backup_hours:,.0f} hours without fuel.

## Electrification opportunities
Electricity share of local energy use: {pct(h.electricity_share_before)} → {pct(h.electricity_share_after)}.
Suggested new loads: {'; '.join(h.suggested_new_loads)}.

## Expected impact
{z.diesel_litres_avoided_year1:,.0f} L diesel avoided in year 1 (about {tco2(z.diesel_litres_avoided_year1):,.0f} tCO2e).

## Next steps
Validate against Tokelau/REopt, confirm site data, agree funding and O&M arrangements.
"""


def build_onepager(r):
    i, z, h = r.inputs, r.sizing, r.headroom
    return f"""# {i.site_name}: Our Solar Plan
{"(Example numbers only)" if any("FAKE" in w for w in r.warnings) else ""}

- New solar panels ({z.pv_kw:,.0f} kW) and a battery ({z.battery_kwh:,.0f} kWh).
- About {pct(z.renewable_share_year1)} of our power comes from the sun.
- We save about {z.diesel_litres_avoided_year1:,.0f} litres of diesel each year.
- Money is set aside every year so the battery can be replaced.
- The clinic and radio can stay on for about {r.backup_hours:,.0f} hours with no fuel.
- Extra clean power could run: {'; '.join(h.suggested_new_loads)}.
"""
