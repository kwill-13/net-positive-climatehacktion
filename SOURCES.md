# SunSafe sources: validation references

Sources for the numbers used to **validate** the model against Tokelau. Sources for model
**inputs** (costs, efficiencies, fuel-shock series, discount rate) are in the block at the top
of `sunsafe/config.py`.

Status key:
- **Verified:** we opened the page on 2026-10-03 and the figure is stated there.
- **Partly verified:** the source exists but says something narrower, or the figure is our
  derivation from it.
- **Missing:** no source located. State this as a limitation.

## 1. Fakaofo real install: 265-365 kWp PV, 1.1-1.6 MWh lead-acid (Source A): Verified

- M. O'Reagan (ITP Renewables), "Solar and battery microgrid project to return Tokelau to
  100% renewables", *One Step Off The Grid*, 14 Nov 2019.
  https://onestepoffthegrid.com.au/solar-and-battery-microgrid-project-to-return-tokelau-to-100-renewables/
  Quote: "three island-scale PV and BESS systems (265-365kWP PV, 1.1-1.6 MWh [nominal] lead
  acid batteries)".
- **Caveat 1: the range covers all three atolls.** It is not split by atoll, so the range
  applies to each system and not specifically to Fakaofo.
- **Caveat 2: a second source gives a different range.** It says "between 240-400kW of PV and
  1.4-1.9 MWh of lead acid battery banks" per atoll, with no author or date:
  https://www.delahyde.com/NZ/pagesl/Tokelau_First_Nation_Solar_Power.html
- **Total size, consistent with Source A:** ~1 MW PV, 4,032 panels, 392 inverters and 1,344
  batteries (CleanTechnica 2013, below).

## 2. ~8 MWh lead-acid across the three atolls (Source B): Missing

- A web search summary stated "over 8 MWh of lead-acid battery storage", but we could not
  find the page it came from. None of CleanTechnica, RNZ, Matauala or tokelau.org.nz
  states an MWh total.
- Treat it as unsourced. Source A (3 x 1.1-1.6 MWh = 3.3-4.8 MWh) is the citable figure.

## 3. Reported ~9-year payback: Verified

- L. Guevara-Stone (Rocky Mountain Institute), "An Island (Tokelau) Powered 100% By Solar
  Energy", *CleanTechnica*, 6 Oct 2013 (first published on the RMI blog, 24 Sep 2013).
  https://cleantechnica.com/2013/10/06/an-island-tokelau-powered-100-by-solar-energy/
  Quote: "the system will pay for itself in a relatively short time period (nine years with
  simple payback)".
- **Caveat:** the article does not say which costs and savings go into that payback.

## 4. Project cost NZD 7M: Partly verified (the total was NZD 8.5M)

- CleanTechnica 2013 (above): "New Zealand advanced $7 million to Tokelau to install the PV
  systems."
- Matauala, Climate change: https://www.matauala.org.nz/climate-change
  - Calls it an "$8.5 million solar power project".
  - Says New Zealand supported it "through an advance of $7 million".
- **NZD 7M is New Zealand's advance; the full project cost was NZD 8.5M.**
- `scripts/run_tokelau.py` section 7 uses NZD 7M, which gives a 10.9-year payback for the
  real system. At NZD 8.5M the same calculation gives about 13 years (10.9 x 8.5 / 7).
  The model is frozen, so report both.

## 5. Tokelau delivered diesel price USD 2.70/L: Partly verified (derived, not quoted)

No source states a per-litre price. USD 2.70/L is derived from fuel volume and fuel spend,
using three statements:
- "Around 200 litres of fuel daily on each atoll" (Matauala, above; CleanTechnica says
  "burning 200 liters per day").
- "More than 2,000 barrels of diesel ... each year", costing "more than $1m NZD"
  (Matauala).
- "Nearly $800,000 per year" (CleanTechnica). The Tokelau Government's Solar Project page
  says "$829,000 every year to import fuels": https://www.tokelau.org.nz/Solar+Project.html

The two volume figures disagree:
- 200 L/day x 3 atolls = ~219,000 L/yr.
- 2,000 barrels = ~318,000 L/yr.

So the implied price spans about NZD 2.5-4.6/L, or USD 2.0-3.7/L at ~0.80 USD/NZD. USD 2.70
sits inside that range but is not a quoted figure.

Further caveats:
- The 0.80 USD/NZD (2012) rate has no cited source.
- The SPC 2016 page cited in config.py returned HTTP 403 when we tried to open it, so it is
  not verified here:
  https://www.spc.int/updates/blog/2016/11/zoom-tokelau-leads-world-in-renewable-energy

## 6. Apia monthly diesel prices, Mar-Oct 2026: Partly verified (links supplied, not checked)

The series (WST/L) is `FUEL_SHOCK_APIA_WST_PER_L` in `sunsafe/config.py`. Links supplied by
William:
- https://samoanewshub.com/2026/01/01/fuel-prices-increase-across-samoa-for-january-2026/
- https://samoaglobalnews.com/samoa-fuel-prices-rise-across-all-products-from-april-1/
- https://www.samoaobserver.ws/category/samoa/120219
- https://talamua.com/?p=61207
- https://talamua.com/?p=62013
- https://talamua.com/?p=62357

**To do:** nobody has checked these against each month, and which article gives which month
was not recorded. Before citing, map each of the 8 months to an article.

## 7. Measured data from the real system: Mostly missing

Found (qualitative only):
- **Battery replacement:** RNZ, "New solar system for Tokelau", 4 Mar 2020:
  https://www.rnz.co.nz/international/pacific-news/410925/new-solar-system-for-tokelau
  - NZD 9M (USD 5.7M) for an extra 210 kW of PV and 2 MWh of Li-ion on each of Atafu,
    Fakaofo and Nukunonu.
  - This makes "the existing lead acid batteries redundant".
  - The system "was eight years old and in need of upgrading because of increasing demand
    for electricity and wear and tear from the harsh marine environment".
  - **Caveat:** this is an announcement, not a commissioning date.
- **Decline and demand growth:** O'Reagan / ITP 2019 (item 1).
  - "The battery capacity fades, maintenance requirements of the generators increase, and
    fuel consumption rises."
  - "Load growth was found to be increasing at a rate of 9% per year historically."
  - **This is above the model's 3%/yr placeholder.** List it as a limitation; the model is
    frozen.
- **Diesel use before solar:** 200 L/day per atoll (items 4-5). Also, Tokelau Government
  Energy page: "Annual imports of fuel in 2003 totalled 162,000 litres of diesel":
  https://www.tokelau.org.nz/Tokelau+Government/Government+Departments/Energy+and+Telecommunications/Energy.html

Missing:
- A diesel-use time series after 2012.
- Measured battery capacity or state of health over time.
- The actual date the lead-acid banks were retired.
- Measured renewable share by year.

## 8. Tokelau technical review: Missing (exists, not downloaded)

- ITP Renewables carried out a technical review for NZ MFAT: "a technical review of existing
  data and proposals for increasing renewable energy in Tokelau ... to achieve ... 100% RE on
  a least-cost basis". It is referenced by ITP's projects page and the 2019 article (item 1).
  - It is the best candidate for items 2 and 7.
  - Nobody on the team has a copy, and the projects page did not load its content for us:
    https://itprenewables.com/projects/
  - It may be obtainable from MFAT or ITP.
- The Government Energy page lists earlier reports, which we have not obtained:
  - "Grid-connected Photovoltaic Electricity Supply on Tokelau - Hardware Specification and
    Feasibility Study Report"
  - The EIA for the same project
  - The PIREP Tokelau National Report

## Limitations to state

1. The battery size has one citable range (Source A). The second figure (~8 MWh, Source B)
   is unsourced, and a third, uncited page gives 1.4-1.9 MWh per atoll.
2. The ~9-year payback is reported without its method. The project cost was NZD 8.5M, of
   which NZD 7M was New Zealand's advance.
3. The USD 2.70/L diesel price is derived from fuel volume and fuel spend. The source
   figures imply USD 2.0-3.7/L.
4. There is no measured performance data (diesel use, battery health, renewable share) for
   2012-2020. Decline is described only qualitatively.
5. Historical load growth was reported as 9%/yr; the model assumes a 3%/yr placeholder.
6. The Apia fuel-shock links are not yet mapped to individual months.
