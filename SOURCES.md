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

## 2. Over 8 MWh lead-acid across the three atolls (Source B): Verified

- ITP Renewables, Projects page, entry "Tokelau Renewable Energy Project: Engineering design
  and supervision for the world's first solar-powered nation". The entry is undated; the
  site footer says (c) 2024. https://itprenewables.com/projects/
  Quote: "With funding from the New Zealand Ministry of Foreign Affairs and Trade (MFAT),
  approximately 1 MW of solar photovoltaics and over 8 MWh of lead-acid battery storage
  capacity were installed across Tokelau's three atolls. ITP developed engineering designs
  for the three atolls and provided owner's engineering services throughout project
  delivery."
  - Our automated fetch did not load the project text. The quote was copied from the page in
    a browser on 2026-10-03.
- **Per atoll,** "over 8 MWh" / 3 = about 2.7 MWh. `scripts/run_tokelau.py` and the app use
  this as "~2,700 kWh (Source B)".
- **The 2x conflict with Source A is resolved: Source B is nominal capacity, and Source A
  matches the usable half.** Primary data comes from IRENA (2013), *Pacific Lighthouses:
  Tokelau*, Table 2, p. 7 ("provided through communication by Government of Tokelau"). Each
  48 V cluster has 3,200 Ah C20 cells in parallel pairs, giving 6,400 Ah (p. 6).

  | Atoll | PV kWp | Battery Ah at 48 V | Nominal kWh (C20) | 50% usable kWh |
  |---|---|---|---|---|
  | Fakaofo | 330 | 70,400 (11 clusters) | 3,379 | 1,690 |
  | Atafu | 297 | 57,600 (9 clusters) | 2,765 | 1,382 |
  | Nukunonu | 264 | 51,200 (8 clusters) | 2,458 | 1,229 |
  | **Total** | **891** | 179,200 | **8,602** | 4,301 |

  - **Totals:** the nominal total, 8.6 MWh, matches Source B ("over 8 MWh").
  - **Per atoll:** the usable figures, 1.23-1.69 MWh, match Source A's 1.1-1.6 MWh.
    - Source A labels its range "[nominal]", but the numbers fit usable capacity at the
      50% depth of discharge that lead-acid systems are designed for.
  - **Cross-checks:**
    - Cell count: 28 clusters x 48 cells = 1,344, the reported battery count.
    - Cluster counts: 11/9/8 matches the battery charts in IT Power (2013), Figs 28, 61
      and 94.
    - Cell model: the battery photo (IT Power 2013, Fig. 67) appears to show Exide/GNB
      "Classic 22 OPzS 2750 LA", a 2 V tubular flooded cell rated about 3,000 Ah at C10.
      That reading of the photo is not yet confirmed.
- **What this means for the model and app:** compare SunSafe's *nominal* `battery_kwh` with
  2.5-3.4 MWh per atoll, not with Source A. Equivalently, compare usable capacity
  (nominal x 0.5 for lead-acid) with Source A. See Part 1b, item V1.

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
- `scripts/run_tokelau.py` section 7 reports the real system's payback at both costs: 10.9
  years at NZD 7M and 13.3 years at NZD 8.5M, against the reported ~9.

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

**Derivation flaw (found 2026-10-03):** the NZD 0.8-1M/yr spend is for *all* fuel imports.
Tokelau also imports petrol (over 1,000 outboard boats), kerosene and LPG (IRENA 2013, pp. 2-4).
Dividing all-fuel spend by power-diesel volume overstates the diesel price.

**Direct evidence on the landed diesel price** (IT Power 2013, pp. 28-29):
- "Diesel costs, landed on Tokelau, have been reported as: $1.16 per litre; $1.52 per litre
  and 'over' $2.00 per litre."
- "Diesel fuel wholesale in Samoa is around NZD 1.20 per litre"; ITP used **NZD 1.50/L**.
- At 0.81 USD/NZD that is about USD 0.94-1.62+/L, with USD 1.22/L as ITP's central value
  in 2013.
- For 2026: the Apia retail range is USD 1.17-1.93/L, and Tokelau adds freight to that.

**USD 2.70/L is therefore likely too high.** The model's breakeven is USD 2.34/L, so this
decides the economic result. See Part 1b, item P1.

Further caveats:
- USD/NZD 2012: the annual average was 0.810 (OFX), and IRENA (2013) gives USD 1 = NZD 1.22
  on 23 Oct 2012 (0.82). The config's 0.80 is consistent.
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
| 2026-07 | 4.48 | "dropping from $5.31 in June to $4.48 per litre for July" | Talamua, 1 Jul 2026: https://talamua.com/?p=61207 |
| 2026-08 | 3.89 | "from $3.89 to $4.22" | Talamua, 1 Sep 2026: https://talamua.com/?p=62013 |
| 2026-09 | 4.22 | same | same |
| 2026-10 | 4.44 | "from $4.22 to $4.44" | Talamua, 1 Oct 2026: https://talamua.com/?p=62357 |

- **July is stated in the article.** The verbatim sentence is "Diesel price decreased by
  82.3 sene per litre, dropping from $5.31 in June to $4.48 per litre for July."
  - The sene drop implies 4.487, but the stated price is used.
  - The value was 4.49 (derived) until 3 Oct 2026.
- **Lower-bound check:** Samoa News Hub, 1 Jan 2026, gives January diesel at $3.22 (from
  $3.10 in December). At 0.3635 USD/WST that is USD 1.17/L, matching config.py.
  https://samoanewshub.com/2026/01/01/fuel-prices-increase-across-samoa-for-january-2026/
- **Exchange rate:** WST/USD 0.3635 on 3 Oct 2026, https://www.currency.me.uk/convert/wst/usd

## 7. Measured data from the real system: Partly available (2008 and 2012-13)

**Measured (IT Power 2013 and IRENA 2013):**
- **2008 demand, diesel era** (IRENA 2013, Table 1, p. 4, from the Tokelau Energy Office):

  | Atoll | kWh/yr | kWh/day | Peak kW | Peak / average | Diesel L/yr | Implied kWh/L |
  |---|---|---|---|---|---|---|
  | Fakaofo | 255,100 | 699 | 51.2 | 1.76 | 94,540 | 2.70 |
  | Atafu | 201,800 | 553 | 38.0 | 1.65 | 100,470 | 2.01 |
  | Nukunonu | 219,400 | 601 | 36.7 | 1.47 | 76,650 | 2.86 |

  - The table's fuel total (271,660 L) disagrees with IRENA's own text ("around 160,000
    litres").
  - Load curves have "sharp load peaks early in the morning and in the evening" and barely
    change over the week (p. 6).
- **2012-13 operation, solar era.** Measured Nov 2012-May 2013, scaled to a year (IT Power
  2013, pp. 14-24):
  - Total generation (PV + diesel): Atafu 343,898 kWh/yr (942/day), Nukunonu 320,403
    (878/day), Fakaofo 491,205 (1,346/day).
    - Fakaofo's figure is estimated, because its SD cards were missing.
    - ITP's sales-based model gives about 248,000 kWh/yr (680/day) for Fakaofo instead
      (p. 28).
  - **Solar fraction measured:** Atafu 92.5%, Nukunonu 93.5%, Fakaofo ~89%. The designed
    fractions were 89/91/86% (p. 8).
  - Diesel use after solar: Atafu 23.7 L/day, Nukunonu 18.9, Fakaofo 49.3 (estimated at
    3 kWh/L).
  - PV specific yield (wet season, grid-tied arrays only): 1,060-1,198 kWh/kWp/yr.
- **Implied demand growth, 2008 to 2013:** Atafu 553 to 942 kWh/day (~11%/yr), Nukunonu
  601 to 878 (~8%/yr). This is consistent with ITP's 2019 "9% per year historically".
  - Caveat: 2013 generation includes battery losses (about 5%) and is scaled from 7 months.

Found (qualitative):
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
  - **This is above the model's 3%/yr default placeholder.** State it as a limitation.
    Users can set demand growth on the app's Site Setup page.
- **Load size:** TendersGo, Tokelau battery upgrade, gives "~30 kW load per island"
  (lower-reliability source).
  https://www.tendersgo.com/post/tokelaus-90-solar-power-transition-battery-upgrade-project-6642
  - 30 kW average is about 720 kWh/day, the upper of the two loads in `run_tokelau.py`.
- **Diesel use before solar:** 200 L/day per atoll (item 5). Also, Tokelau Government Energy
  page: "Annual imports of fuel in 2003 totalled 162,000 litres of diesel":
  https://www.tokelau.org.nz/Tokelau+Government/Government+Departments/Energy+and+Telecommunications/Energy.html

Still missing:
- Any data after mid-2013: diesel use, renewable share and battery state of health by year.
- The actual date the lead-acid banks were retired.

## 8. Tokelau technical review: Read (2026-10-03)

- IT Power, *Tokelau Renewable Energy Project Review*, 2013, 136 pp. It is a
  post-installation review of the financial and technical performance of the three systems.
  - Listing: https://www.pcreee.org/publication/tokelau-renewable-energy-project-review
  - PDF: https://prdrse4all.spc.int/system/files/energy_tokelau_pv_system_review_-_final.pdf
- Obtained by the team in a browser (the PDF returns HTTP 403 to automated access) and
  read in full.
  - **Do not commit the PDF.** Its cover marks it "Confidential - client only", even though
    it is publicly hosted. Cite it by page.
- **What it contributed:** measured 2012-13 performance (item 7), landed diesel prices
  (item 5), and cost, life and O&M evidence (Part 1b).
- **What it does not contain:** the ~9-year payback method (item 3), and per-atoll battery
  kWh (those come from IRENA 2013).
- Earlier reports listed on the Tokelau Government Energy page, which we have not obtained:
  - "Grid-connected Photovoltaic Electricity Supply on Tokelau - Hardware Specification and
    Feasibility Study Report"
  - The EIA for the same project
  - The PIREP Tokelau National Report

## Limitations to state

1. **Battery size:** resolved. Per atoll, nominal is 2.46-3.38 MWh and usable is
   1.23-1.69 MWh (IRENA 2013). Source A is usable capacity; Source B is the nominal total.
   The current validation compares the model's *nominal* battery with Source A, which is
   not like for like (Part 1b, V1).
2. **Payback:** the ~9 years is reported without its method. The project cost was NZD 8.5M,
   of which NZD 7M was New Zealand's advance. Modelled real-system payback is 10.9 years at
   NZD 7M and 13.3 years at NZD 8.5M.
3. **Diesel price:** USD 2.70/L divides all-fuel spend by diesel volume, so it is likely
   too high. Landed diesel in 2013 was NZD 1.16-2.00+/L (IT Power 2013). This decides
   whether solar beats diesel in the model (Part 1b, P1).
4. **Measured performance stops in 2013.** There is no data on 2014-2020 decline.
5. **Load growth:** 8-11%/yr implied for 2008-13, and 9%/yr reported by ITP; the model's
   default is 3%/yr.
6. **Demand level:** real 2013 demand was about 850-940 kWh/day (Atafu, Nukunonu), above
   the 600-720 kWh/day validation loads.

---

# Part 1b: Evidence for placeholders, and validation fixes (2026-10-03)

Found by reading IT Power (2013) and IRENA (2013), plus targeted searches. **Nothing here
has been applied to `config.py` or the app yet.** Each row needs a decision from William.

## Placeholders and unsourced values

| ID | Item | Current | Evidence found | Suggestion |
|---|---|---|---|---|
| P1 | Diesel price (Tokelau) | USD 2.70/L | Landed 2013: NZD 1.16 / 1.52 / >2.00 per L; ITP used NZD 1.50 (IT Power 2013, pp. 28-29) = USD ~1.22. Apia retail 2026: USD 1.17-1.93. The 2.70 derivation divides all-fuel spend by diesel volume (item 5) | Re-derive. Use a sourced delivered price for 2026 (Apia retail plus freight) and keep 2.70 as a high scenario. **This decides solar vs diesel:** breakeven is USD 2.34/L |
| P2 | PV capex | USD 2,500/kW (TODO) | Tokelau 2012 back-calculation: USD 6.95M total (IRENA 2013) minus ~USD 3.0-3.2M batteries (P3) over 891 kWp = **~USD 4,200-4,400/kWp** including inverters, BOS and install. Tokelau 2020 (RNZ): USD 2,500-3,300/kWp, depending on the Li-ion price assumed. Tuvalu 2024: USD 6M for 500 kW + 2 MWh (pv magazine), project-level. Global utility average: USD 691/kW (IRENA 2024) | Keep 2,500 as the low case and add ~4,000 as a remote-atoll high case. Mark sourced as a range |
| P3 | Lead-acid capex | USD 350/kWh (TODO) | ITP's battery replacement estimate: NZD 3.75-4.0M (IT Power 2013, pp. 27, 32) for 8,602 kWh = NZD 436-465/kWh = **USD 353-377/kWh** (2013) | Keep 350 and mark it sourced |
| P4 | Lead-acid life | 8 yrs (sourced) | ITP's tariff model also uses 8 yrs (IT Power 2013, p. 27). Replaced after ~8 yrs (RNZ 2020) | No change; add the citation |
| P5 | Lead-acid fade | 6%/yr (TODO) | Exide Classic OPzS: 20-yr design life at 20 °C to 80% C10, which is ~1.1%/yr at 20 °C. Tokelau battery rooms measured 31-34 °C (IT Power 2013, pp. 58, 88, 117), so faster ageing is expected. Reaching 80% after ~8 yrs implies ~2.8%/yr. ITP 2019 cites a "gradual decrease in battery capacity" | Consider 3%/yr as the base case, with 6% as pessimistic. The 0.04-0.08 sensitivity already brackets this |
| P6 | Li-ion fade | 2.5%/yr (TODO) | No Pacific-specific source found. Lab literature gives wide ranges | Keep TODO |
| P7 | Demand growth | 3%/yr (TODO) | Tokelau 2008-13: ~8-11%/yr (item 7); ITP 2019: 9%/yr | Use 9% for Tokelau runs. The generic default is a decision |
| P8 | Load shape | generic, evening peak (placeholder) | IRENA 2013: sharp early-morning and evening peaks, flat across the week; 2008 peak/average 1.47-1.76. The current shape's peak/average is 1.77, but its morning peak is weak | Partly supported. Add a sharper morning peak (IRENA Fig. 3 is an image only) |
| P9 | Freezer candidate load | 8 kWh/day (TODO) | Nukunonu community freezer: "approximate energy requirement of 25 kWh/day", compressor under 3 kW (IT Power 2013, p. 100) | Change to 25 kWh/day |
| P10 | Non-electric energy | 3x electric (TODO) | IRENA 2013: kerosene and LPG for cooking, petrol for over 1,000 outboard boats; no volumes in text (Fig. 2 is an image) | Keep TODO |
| P11 | Solar O&M | PV USD 70/kW/yr + battery USD 10/kWh/yr | ITP: solar O&M NZD 12,000/yr per atoll (~USD 9,700), excluding replacements (IT Power 2013, p. 31). The config gives ~USD 57,000/yr for a Fakaofo-size system | The config is ~6x ITP. Review it; ITP's figure covers labour and consumables only |
| P12 | USD/NZD 2012 | 0.80 (unsourced) | 2012 average 0.810 (OFX); 0.82 on 23 Oct 2012 (IRENA 2013) | Keep; add the citation |
| P13 | Generator kWh/L | 3.0 (sourced) | ITP assumed 3 kWh/L, range 2.5-3.6 (IT Power 2013, p. 28). 2008 implied 2.0-2.9 kWh/L (IRENA Table 1) | Keep. Real gensets may be worse, which favours solar |

## Validation fixes

- **V1. Battery comparison is not like for like.** The app's validation table and
  `run_tokelau.py` compare the model's *nominal* battery with Source A, which is
  effectively *usable*.
  - Like-for-like, the recommended 1,481 kWh nominal (740 usable) is **about 0.44-0.60x** the
    real system's nominal 2.46-3.38 MWh.
  - PV (315 kWp) stays within the real 264-363 kWp range.
- **V2. The "real system" in `run_tokelau.py` is too small.** It uses 300 kWp / 1,350 kWh
  nominal, which is Source A misread as nominal. The IRENA per-atoll sizes are, for example,
  Fakaofo 330 kWp / 3,379 kWh nominal. Using them changes the outputs of sections 3, 5
  and 7.
- **V3. Validation loads.** 600/720 kWh/day sits within the 2008 measured range (553-699),
  but 2013 demand was ~850-940 kWh/day (Atafu, Nukunonu).
- **V4. A new validation test is possible.** Simulate each real system (IRENA sizes) at its
  2013 demand with NASA weather, and compare the renewable share with the **measured** 2013
  solar fractions (Atafu 92.5%, Nukunonu 93.5%) and the design fractions (89-91%).
- **V5. A payback cross-check.** ITP estimates a "saving of around NZD 15m through the
  reduction in diesel usage over the life of the project" (25 yrs, 2013 dollars,
  undiscounted; IT Power 2013, p. 35). That is ~NZD 0.6M/yr across three atolls, giving a
  simple payback of ~14 yrs at NZD 8.5M or ~12 yrs at NZD 7M. This agrees with the model's
  13.3 / 10.9 yrs, and sits above the ~9 yrs CleanTechnica reported.

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
- [NREL ATB: Utility-scale battery storage](https://atb.nlr.gov/electricity/2024/utility-scale_battery_storage) [NREL-ATB]
- [Energy-Storage.News: BNEF and Ember 2025 storage prices](https://www.energy-storage.news/battery-storage-system-prices-continue-to-fall-sharply-bnef-and-ember-reports-find/) [BNEF25]

**Discount rate**
- [ADB: Nauru economic analysis (9%)](https://www.adb.org/sites/default/files/linked-documents/49450-009-ea.pdf) [ADB-NRU]
- [ADB: Tonga Renewable Energy Project economic analysis (6%)](https://www.adb.org/sites/default/files/linked-documents/49450-012-ea.pdf) [ADB-TON]

**Tokelau system, decline and payback** (validation; see Part 1)
- [CleanTechnica: Tokelau powered 100% by solar (NZ advance NZD 7M, ~9-year payback)](https://cleantechnica.com/2013/10/06/an-island-tokelau-powered-100-by-solar-energy/) [CT13]
- [One Step Off The Grid: Project to return Tokelau to 100% renewables](https://onestepoffthegrid.com.au/solar-and-battery-microgrid-project-to-return-tokelau-to-100-renewables/) (lower reliability; ITP author)
- [Power Technology: Tokelau, world's first solar sufficient nation](https://www.power-technology.com/features/featuretokelau-world-first-solar-power-sufficient-nation/)
- [100% RE Atlas: Tokelau (battery banks, 2 days autonomy)](https://www.100-percent.org/tokelau/)
- [ITP Renewables: Projects (over 8 MWh battery)](https://itprenewables.com/projects/) (Source B; quote in Part 1, item 2)
- [TendersGo: Tokelau battery upgrade (~30 kW load per island)](https://www.tendersgo.com/post/tokelaus-90-solar-power-transition-battery-upgrade-project-6642) (lower reliability)
- [IRENA: Tokelau energy profile](https://www.irena.org/-/media/Files/IRENA/Agency/Statistics/Statistical_Profiles/Oceania/Tokelau_Oceania_RE_SP.pdf)
- [PCREEE: Tokelau Renewable Energy Project Review (IT Power, 2013)](https://www.pcreee.org/publication/tokelau-renewable-energy-project-review): read 2026-10-03; cite by page. The PDF is marked "Confidential - client only", so do not commit it.
- [IRENA (2013): Pacific Lighthouses - Tokelau (per-atoll PV kWp and battery Ah; 2008 demand; NZD 8.5M = USD 6.95M)](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2013/Sep/Tokelau.pdf)
- [Exide Classic OPzS 22 OPzS 2750 LA product listing (2 V, ~3,000 Ah C10)](https://batterygroup.co.uk/batteries-by-type/lead-acid-batteries/7911/exide-classic-opzs-2v-22-opzs-2750-la-2v-3000ah) and [Exide Classic OPzS datasheet (20-yr design life at 20 °C to 80% C10)](https://www.exidegroup.com/eu/en/document/classic-opzs-datasheet)
- [OFX: NZD/USD yearly average rates (2012: 0.810)](https://www.ofx.com/en-nz/forex-news/historical-exchange-rates/yearly-average-rates/)
- [pv magazine (2024): ADB commissions 500 kW solar + 2 MWh storage in Tuvalu (USD 6M)](https://www.pv-magazine.com/2024/12/04/adb-commissions-500-kw-solar-project-with-2-mwh-of-storage-in-tuvalu/)
- [pv magazine (2025): IRENA 2024 global utility solar installed cost USD 691/kW](https://www.pv-magazine.com/2025/07/23/global-average-solar-lcoe-stood-at-0-043-kwh-in-2024-says-irena/)

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
