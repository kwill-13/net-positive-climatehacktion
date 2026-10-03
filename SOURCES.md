# SunSafe sources

This file has two parts:

- **Part 1, validation questions:** each reference number checked against its source page.
- **Part 2, full source list:** every source used in the model and the proposal, grouped by
  what it supports.

Model input values and their source tags are in the block at the top of `sunsafe/config.py`.

Status key:
- **Verified:** we opened the page on 2026-10-03 and the figure is stated there.
- **Partly verified:** the source exists, but it says something narrower, the figure is our
  own derivation, or the page would not load for an automated check.
- **Missing:** no source located. State this as a limitation.

Reliability: RNZ, ADB, NREL, IRENA and the IT Power review are stronger sources. One Step
Off The Grid, TendersGo and delahyde.com are weaker. Where they overlap, cite the stronger.

---

# Part 1: Validation questions

## 1. Fakaofo real install: 265-365 kWp PV, 1.1-1.6 MWh lead-acid (Source A): Verified

- M. O'Reagan (ITP Renewables), "Solar and battery microgrid project to return Tokelau to
  100% renewables", *One Step Off The Grid*, 14 Nov 2019.
  https://onestepoffthegrid.com.au/solar-and-battery-microgrid-project-to-return-tokelau-to-100-renewables/
  Quote: "three island-scale PV and BESS systems (265-365kWP PV, 1.1-1.6 MWh [nominal] lead
  acid batteries)".
- **Caveat 1: the range covers all three atolls.** It is not split by atoll, so it applies
  to each system rather than to Fakaofo specifically.
- **Caveat 2: the outlet is lower-reliability,** but the author is from ITP Renewables, which
  installed the system.
- **Caveat 3: an uncited page gives a different range,** "between 240-400kW of PV and 1.4-1.9
  MWh of lead acid battery banks" per atoll:
  https://www.delahyde.com/NZ/pagesl/Tokelau_First_Nation_Solar_Power.html
- **Totals that agree with Source A:**
  - CleanTechnica 2013: "around one megawatt", 4,032 panels, 1,344 batteries.
  - 100% RE Atlas (posted 25 Jan 2019): "1344 batteries in 48V banks", and "up to 2 days of
    energy without any solar input". https://www.100-percent.org/tokelau/

## 2. ~8 MWh lead-acid across the three atolls (Source B): Partly verified

- Team-supplied source: ITP Renewables, Projects page ("over 8 MWh battery").
  https://itprenewables.com/projects/
  The page did not load its project text for our automated check, so we have not seen the
  figure ourselves. Open it in a browser and copy the exact wording here before citing.
- **Caveat: the two battery sources disagree by about 2x.** Source A gives 3 x 1.1-1.6 MWh =
  3.3-4.8 MWh in total. Source B gives "over 8 MWh". Both come from ITP Renewables.
  - A possible explanation: Source A is per atoll and nominal, while Source B is a rated
    total on a different basis. This is unconfirmed.
  - The IT Power 2013 review (item 8) should settle it.

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
- `scripts/run_tokelau.py` section 7 reports the real system's payback at both costs: about
  11 years at NZD 7M and about 13 years at NZD 8.5M, against the reported ~9.

## 5. Tokelau delivered diesel price USD 2.70/L: Partly verified (derived, not quoted)

No source states a per-litre price. The figure is derived from fuel volume and fuel spend,
using three statements:
- **Volume:** "Around 200 litres of fuel daily on each atoll" (Matauala). CleanTechnica
  says "burning 200 liters per day" without "each atoll".
- **Volume and spend:** "More than 2,000 barrels of diesel ... each year", costing "more
  than $1m NZD" (Matauala).
- **Spend:** "Nearly $800,000 per year" (CleanTechnica). The Tokelau Government's Solar
  Project page says "$829,000 every year to import fuels":
  https://www.tokelau.org.nz/Solar+Project.html

**Why we read "200 L/day" as per atoll:**
- Read as a total for all three atolls, it gives 73,000 L/yr, which implies about NZD 11/L.
  That is implausible.
- Read per atoll, it gives about 219,000 L/yr.
- "2,000 barrels" is about 318,000 L/yr.
- So the implied price is about NZD 2.5-4.6/L, or USD 2.0-3.7/L at ~0.80 USD/NZD. USD 2.70
  sits in that range.

Further caveats:
- The 0.80 USD/NZD (2012) rate has no cited source.
- The SPC 2016 page returned HTTP 403 when we tried to open it, so it is not verified here:
  https://www.spc.int/updates/blog/2016/11/zoom-tokelau-leads-world-in-renewable-energy

## 6. Apia monthly diesel prices, Mar-Oct 2026: Verified (one value derived)

Series in `sunsafe/config.py` (`FUEL_SHOCK_APIA_WST_PER_L`), WST/litre. Each value was
checked against its article.

| Month | Value | Article wording | Source |
|---|---|---|---|
| 2026-03 | 2.99 | "from $2.99 to 3.09" | Samoa Global News, 31 Mar 2026: https://samoaglobalnews.com/samoa-fuel-prices-rise-across-all-products-from-april-1/ |
| 2026-04 | 3.09 | same | same |
| 2026-05 | 4.50 | "from $4.50 to $5.31" | Samoa Observer, 1 Jun 2026: https://www.samoaobserver.ws/category/samoa/120219 |
| 2026-06 | 5.31 | same | same |
| 2026-07 | 4.49 | drop of 82.3 sene from $5.31 | Talamua, 1 Jul 2026: https://talamua.com/?p=61207 |
| 2026-08 | 3.89 | "from $3.89 to $4.22" | Talamua, 1 Sep 2026: https://talamua.com/?p=62013 |
| 2026-09 | 4.22 | same | same |
| 2026-10 | 4.44 | "from $4.22 to $4.44" | Talamua, 1 Oct 2026: https://talamua.com/?p=62357 |

- **July is derived, not quoted:** 5.31 - 0.823 = 4.487, rounded to 4.49. Our fetch of the
  article read "$4.48 per litre" as the stated price. That is a 0.01 difference (0.2%), with
  negligible effect. The model is frozen, so 4.49 is kept and noted.
- **Lower-bound check:** Samoa News Hub, 1 Jan 2026, gives January diesel at $3.22 (from
  $3.10 in December). At 0.3635 USD/WST that is USD 1.17/L, matching config.py.
  https://samoanewshub.com/2026/01/01/fuel-prices-increase-across-samoa-for-january-2026/
- **Exchange rate:** WST/USD 0.3635 on 3 Oct 2026, https://www.currency.me.uk/convert/wst/usd

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
  - **This is above the model's 3%/yr placeholder.** State it as a limitation; the model is
    frozen.
- **Load size:** TendersGo, Tokelau battery upgrade, gives "~30 kW load per island"
  (lower-reliability source).
  https://www.tendersgo.com/post/tokelaus-90-solar-power-transition-battery-upgrade-project-6642
  - 30 kW average is about 720 kWh/day, the upper of the two loads in `run_tokelau.py`.
- **Diesel use before solar:** 200 L/day per atoll (item 5). Also, Tokelau Government Energy
  page: "Annual imports of fuel in 2003 totalled 162,000 litres of diesel":
  https://www.tokelau.org.nz/Tokelau+Government/Government+Departments/Energy+and+Telecommunications/Energy.html

Missing:
- A diesel-use time series after 2012.
- Measured battery capacity or state of health over time.
- The actual date the lead-acid banks were retired.
- Measured renewable share by year.

## 8. Tokelau technical review: Located, not read

- IT Power, *Tokelau Renewable Energy Project Review*, 2013, 136 pp. It is a
  post-installation review of the financial and technical performance of the three systems.
  - Listing: https://www.pcreee.org/publication/tokelau-renewable-energy-project-review
  - PDF: https://prdrse4all.spc.int/system/files/energy_tokelau_pv_system_review_-_final.pdf
- The PDF returns HTTP 403 to automated access, so nobody on the team has read it yet.
  **Download it in a browser.** It is the best source for:
  - per-atoll PV and battery sizes (items 1-2),
  - early performance data (item 7),
  - the payback method (item 3).
- Earlier reports listed on the Tokelau Government Energy page, which we have not obtained:
  - "Grid-connected Photovoltaic Electricity Supply on Tokelau - Hardware Specification and
    Feasibility Study Report"
  - The EIA for the same project
  - The PIREP Tokelau National Report

## Limitations to state

1. **Battery size:** the two ITP figures disagree by about 2x (3.3-4.8 MWh vs over 8 MWh),
   and a third, uncited page gives 1.4-1.9 MWh per atoll. The IT Power review is the
   tie-breaker, and nobody has read it yet.
2. **Payback:** the ~9 years is reported without its method. The project cost was NZD 8.5M,
   of which NZD 7M was New Zealand's advance. Modelled real-system payback is about 11
   years at NZD 7M and about 13 years at NZD 8.5M.
3. **Diesel price:** USD 2.70/L is derived from fuel volume and fuel spend, reading
   "200 L/day" as per atoll. The source figures imply USD 2.0-3.7/L.
4. **No measured performance data:** there is none for 2012-2020 (diesel use, battery
   health, renewable share). Decline is described only qualitatively.
5. **Load growth:** reported historically as 9%/yr; the model assumes a 3%/yr placeholder.
6. **Fuel shock:** July 2026 is derived from the reported drop (4.49 vs 4.48 as stated).

---

# Part 2: Full source list

Tags in [brackets] match the source block in `sunsafe/config.py`.

**Diesel price (Tokelau, 2012)**
- [SPC: Tokelau leads world in renewable energy](https://www.spc.int/updates/blog/2016/11/zoom-tokelau-leads-world-in-renewable-energy) [SPC16]
- [Matauala: Climate change (Tokelau fuel cost)](https://www.matauala.org.nz/climate-change) [MAT]

**Apia diesel prices 2026 (fuel-shock series)** [APIA], [FX-WST]
- [Samoa News Hub: January 2026 prices](https://samoanewshub.com/2026/01/01/fuel-prices-increase-across-samoa-for-january-2026/)
- [Samoa Global News: April 2026 prices](https://samoaglobalnews.com/samoa-fuel-prices-rise-across-all-products-from-april-1/)
- [Samoa Observer: June 2026 prices ($5.31)](https://www.samoaobserver.ws/category/samoa/120219)
- [Talamua: July 2026 prices](https://talamua.com/?p=61207)
- [Talamua: September 2026 prices](https://talamua.com/?p=62013)
- [Talamua: October 2026 prices](https://talamua.com/?p=62357)
- [currency.me.uk: WST to USD rate](https://www.currency.me.uk/convert/wst/usd)

**Generator O&M and efficiency**
- [ADB: Nauru Solar Power Development Project economic analysis](https://www.adb.org/sites/default/files/linked-documents/49450-009-ea.pdf) [ADB-NRU]
- [HOMER: Diesel O&M costs](https://homerenergy.com/docs/knowledgebase/article/diesel-om-costs/) [HOMER]
- [CIF: POISED Maldives outer islands case study](https://www.cif.org/sites/cif_enc/files/knowledge-documents/66436_191219_maldives_case_study_v7s.pdf) [POISED]

**PV degradation**
- [NREL: Photovoltaic Degradation Rates, an Analytical Review (Jordan & Kurtz)](https://docs.nlr.gov/docs/fy12osti/51664.pdf) [NREL-DEG]

**Battery life, cost and O&M**
- [RNZ: New solar system for Tokelau (2020 upgrade, NZ$9M)](https://www.rnz.co.nz/international/pacific-news/410925/new-solar-system-for-tokelau) [RNZ20]
- [World Bank / KGGTF: Pacific BESS policy and program report](https://www.wbgkggtf.org/sites/kggtf/files/2023-02/COCF_Final%20Report_Development%20of%20regional%20Battery%20Energy%20Storage%20System%20(BESS)%20Policy%20and%20Program%20for%20the%20Pacific%20Island%20Countries%20(PICs).pdf) [WB-BESS]
- [NREL ATB: Utility-scale battery storage](https://atb.nrel.gov/electricity/2024/utility-scale_battery_storage) [NREL-ATB]
- [Energy-Storage.News: BNEF and Ember 2025 storage prices](https://www.energy-storage.news/battery-storage-system-prices-continue-to-fall-sharply-bnef-and-ember-reports-find/) [BNEF25]

**Discount rate**
- [ADB: Nauru economic analysis (9%)](https://www.adb.org/sites/default/files/linked-documents/49450-009-ea.pdf) [ADB-NRU]
- [ADB: Tonga Renewable Energy Project economic analysis (6%)](https://www.adb.org/sites/default/files/linked-documents/49450-012-ea.pdf) [ADB-TON]

**Tokelau system, decline and payback** (validation; see Part 1)
- [CleanTechnica: Tokelau powered 100% by solar (NZ advance NZD 7M, ~9-year payback)](https://cleantechnica.com/2013/10/06/an-island-tokelau-powered-100-by-solar-energy/) [CT13]
- [One Step Off The Grid: Project to return Tokelau to 100% renewables](https://onestepoffthegrid.com.au/solar-and-battery-microgrid-project-to-return-tokelau-to-100-renewables/) (lower reliability; ITP author)
- [Power Technology: Tokelau, world's first solar sufficient nation](https://www.power-technology.com/features/featuretokelau-world-first-solar-power-sufficient-nation/)
- [100% RE Atlas: Tokelau (battery banks, 2 days autonomy)](https://www.100-percent.org/tokelau/)
- [ITP Renewables: Projects (over 8 MWh battery)](https://itprenewables.com/projects/) (not loaded by our check)
- [TendersGo: Tokelau battery upgrade (~30 kW load per island)](https://www.tendersgo.com/post/tokelaus-90-solar-power-transition-battery-upgrade-project-6642) (lower reliability)
- [IRENA: Tokelau energy profile](https://www.irena.org/-/media/Files/IRENA/Agency/Statistics/Statistical_Profiles/Oceania/Tokelau_Oceania_RE_SP.pdf)
- [PCREEE: Tokelau Renewable Energy Project Review (IT Power, 2013)](https://www.pcreee.org/publication/tokelau-renewable-energy-project-review) (PDF not yet read)

**Pacific fuel crisis and diesel dependence** (proposal context)
- [Devpolicy: Pacific fuel crisis exposes gap between targets and delivery](https://devpolicy.org/pacific-fuel-crisis-exposes-gap-between-renewable-targets-and-delivery-20260611/)
- [Asia Pacific Report: Timeline of the fuel crisis in the Pacific](https://asiapacificreport.nz/2026/06/25/a-timeline-of-how-the-fuel-crisis-impacted-the-pacific/)
- [Zero Carbon Analytics: Pacific Island Countries and the Middle East conflict](https://zerocarbon-analytics.org/energy/middle-east-conflict-underscores-the-urgency-for-pacific-island-countries-to-electrify-and-switch-to-renewables/)

**Capacity gap** (proposal context)
- [ADB: Pacific Renewable Energy Investment Facility](https://ewsdata.rightsindevelopment.org/files/documents/04/ADB-49450-004_RMfnZjh.pdf)
- [East-West Center: Clean energy transitions in the Pacific Islands](https://www.eastwestcenter.org/publications/clean-energy-transitions-in-the-pacific-islands-present-opportunities-strategic-us)
- [Energy Economics: Does donor funding promote clean energy transition in PICs?](https://www.sciencedirect.com/science/article/pii/S0140988324002755)
- [Lowy Institute: Revisiting the Green Climate Fund in the Pacific](https://www.lowyinstitute.org/the-interpreter/revisiting-green-climate-fund-pacific)
- [ICLEI Oceania: Multi-level governance guidance for the Pacific](https://icleioceania.org/wp-content/uploads/2025/10/MLG-Guide-FINAL.pdf)
