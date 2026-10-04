# Sensitivity: Fakaofo, 15 years

Analysis only. No model defaults were changed. To reproduce the tables below, run
`python scripts/run_sensitivity.py` (about 50 s).

**Case:** Fakaofo, Tokelau.
- 600 kWh/day, lead-acid, 95% renewable in every year.
- Diesel USD 1.87/L, discount rate 8% real.
- Strategies: A build big, B same-size battery replacement, C staged expansion, D rolling plan.
- Sections 2 and 3 use the config default growth, a constant 9%/yr (the validation case). The app's
  default growth, 9% for 5 years then 3%, is the third row of section 1.

## Findings

1. **Growth decides the strategy.**
   - At a constant 9%/yr, the rolling plan (D) wins: it costs 27% less than building big.
   - At 5%/yr, or at 9% falling to 3% after 5 years, one staged upgrade around year 9 (C) is
     enough. D's best plan then has the same cost as C, and the saving over building big
     shrinks to 15% and 9%.
   - In every case, a staged plan beats both building big and like-for-like battery replacement.
2. **O&M:** with Tokelau's measured O&M, the hybrid's full cost falls from USD 0.84 to 0.74/kWh.
   The breakeven diesel price falls from USD 2.42 to 2.11/L. The recommended plan stays the same.
   - This uses the measured figure: NZD 12,000/yr per atoll, about 5-6x less than the config rates.
   - At the default USD 1.87/L, diesel-only is still cheaper per kWh over the full life cost.
3. **If donors fund the first build,** the island pays about USD 0.47/kWh with the hybrid,
   against USD 0.50-0.85/kWh for diesel only.
   - The hybrid is cheaper for the island at any diesel price above USD 1.28/L.
   - It barely depends on diesel price: about 95% of the energy is solar.
   - The island's cost is mostly O&M and the later upgrades (years 7 and 13).

## 1. Demand growth

| Growth | Recommended | Stages (upgrade years) | NPV A | NPV best B | NPV best C | NPV best D | Saving vs A |
|---|---|---|---:|---:|---:|---:|---:|
| constant 9%/yr | D: rolling plan, 6-yr stages (upgrades in years 7, 13) | build 305 kWp / 1,277 kWh; yr 7: +219 kWp, new 2,141 kWh; yr 13: +139 kWp, new 2,664 kWh | 3.76M | 3.46M | 2.80M | 2.74M | 27% |
| constant 5%/yr | C: expand in year 9 (+133 kWp, new 1,694 kWh battery) | build 279 kWp / 1,241 kWh; yr 9: +133 kWp, new 1,694 kWh | 2.23M | 2.13M | 1.89M | 1.89M | 15% |
| 9%/yr for 5 yrs, then 3%/yr | C: expand in year 9 (+94 kWp, new 1,717 kWh battery) | build 324 kWp / 1,439 kWh; yr 9: +94 kWp, new 1,717 kWh | 2.27M | 2.20M | 2.06M | 2.06M | 9% |

Best B/C/D = lowest-NPV variant of that strategy that meets the target every year. NPV in USD, 8% real.

## 2. Solar + battery O&M

Tokelau-measured: NZD 12,000/yr per atoll x 0.8 = USD 9,600/yr, split pro rata to capex of Fakaofo's real system (330 kWp / 3,379 kWh) = USD 12.0/kWp/yr + USD 1.67/kWh/yr.

| O&M case | Rates (PV / battery) | Recommended | O&M yr 1 | Hybrid USD/kWh | Diesel-only USD/kWh | Breakeven diesel USD/L |
|---|---|---|---:|---:|---:|---:|
| Current config | 70.0 /kWp, 10.00 /kWh | D: rolling plan, 6-yr stages (upgrades in years 7, 13) | 34,147 | 0.843 | 0.663 | 2.42 |
| Tokelau-measured | 12.0 /kWp, 1.67 /kWh | D: rolling plan, 6-yr stages (upgrades in years 7, 13) | 5,788 | 0.740 | 0.663 | 2.11 |

At USD 1.87/L, constant 9%/yr growth. Plan re-chosen under each O&M case.

## 3. Island-paid cost: "if donors fund the first build"

Plan: D: rolling plan, 6-yr stages (upgrades in years 7, 13); build 305 kWp / 1,277 kWh; yr 7: +219 kWp, new 2,141 kWh; yr 13: +139 kWp, new 2,664 kWh; first build capex USD 1,210,432 (excluded from island-paid).

| Diesel USD/L | Island-paid hybrid USD/kWh | Full hybrid USD/kWh | Diesel-only USD/kWh |
|---:|---:|---:|---:|
| 1.37 (pre-shock 2026 Apia price x1.25 freight) | 0.467 | 0.840 | 0.497 |
| 1.87 (default) | 0.470 | 0.843 | 0.663 |
| 2.42 (full-cost breakeven) | 0.474 | 0.847 | 0.847 |

Island-paid = O&M + later stages (upgrades) + generator fuel and O&M, NPV / discounted kWh at 8%. Breakeven diesel price: island-paid USD 1.28/L, full cost USD 2.42/L. Plan fixed at the USD 1.87/L recommendation, current O&M.

## Notes and caveats

- **Saving vs A:** the recommended plan's NPV is compared with A's.
- **Tokelau O&M split:** the measured figure is split between PV and battery in proportion to
  their capex in Fakaofo's real 2012 system (330 kWp / 3,379 kWh; IRENA 2013). It is then
  applied per kWp and per kWh, so it scales with each plan.
  - The measured figure excludes battery replacements, which the model costs separately.
  - Only this single O&M figure is taken from IT Power (2013).
- **Island-paid cost** includes every reinvestment after the first build:
  - D's two later stages, USD 1.13M and 0.92M before discounting.
  - Solar and battery O&M.
  - Generator fuel and O&M.

  It is not a tariff. It assumes the upgrades happen on time and that the island funds them.
- **The three diesel prices:** USD 1.37/L is the March 2026 (pre-shock) Apia retail price x1.25 freight,
  not the app's low scenario (USD 1.22/L, the 2013 landed price). USD 1.87/L is the default. USD 2.42/L is
  the validation case's full-cost breakeven (`scripts/run_tokelau.py` section 6), where the full hybrid
  and diesel-only costs are equal.
- **Other inputs:** the load shape, PV capex and fade rates are as in `sunsafe/config.py`. Known
  limitations are listed in `CLAUDE.md`.
