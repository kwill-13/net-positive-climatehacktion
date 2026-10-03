"""
Money over the project life: O&M, battery replacement, NPV, levelised cost, payback,
and the 2026 fuel-shock comparison.

Generator cost = fuel + generator O&M per kWh generated (config.GEN_OM_USD_PER_KWH),
applied the same way to the diesel-only case and to the hybrid's generator output.

Timing convention: capex at t = 0; each year's O&M and diesel at the END of that year
(t = year); a battery replacement "in year R" happens at the START of year R (t = R - 1).
All values real USD, discounted at config.PROJECT_DISCOUNT_RATE unless a rate is passed.
Generator capex is excluded from both (the genset stays in both). No salvage value.
"""

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np

from sunsafe import config
from sunsafe.energy.diesel import generator_cost_usd
from sunsafe.hours import monthly_sum
from sunsafe.interface import FuelShockMonth


def discount(t: float, rate: float = config.PROJECT_DISCOUNT_RATE) -> float:
    """Present-value factor for a cash flow t years from now: 1 / (1 + rate)^t."""
    return 1.0 / (1.0 + rate) ** t


def annual_om_usd(pv_kw: float, battery_kwh: float) -> float:
    """
    Yearly O&M of the solar + battery system.

    Args:
        pv_kw: kWp. battery_kwh: kWh nominal.

    Returns:
        USD/yr.
    """
    return pv_kw * config.OM_PV_USD_PER_KW_YEAR + battery_kwh * config.OM_BATTERY_USD_PER_KWH_YEAR


def replacement_cost_usd(battery_kwh: float, chemistry: str, replacement_year: int) -> float:
    """
    Cost of a new battery installed at the start of `replacement_year`, at the declined price.

    Args:
        battery_kwh: nominal kWh to buy.
        chemistry: "lithium" or "lead_acid".
        replacement_year: year of operation it is installed in (t = replacement_year - 1).

    Returns:
        USD in that year (not discounted).
    """
    t = replacement_year - 1
    price = (config.BATTERY_COST_USD_PER_KWH[chemistry]
             * (1.0 - config.BATTERY_PRICE_DECLINE_PER_YEAR) ** t)
    return battery_kwh * price


def lifetime_npv_usd(capex_usd: float, annual_om: float, gen_kwh_by_year: Sequence[float],
                     diesel_price: float, replacement_year: Optional[int] = None,
                     replacement_usd: float = 0.0,
                     rate: float = config.PROJECT_DISCOUNT_RATE) -> float:
    """
    Net present cost over the project: capex + O&M + replacement + generator fuel and O&M.

    Args:
        capex_usd: up-front cost, USD (t = 0).
        annual_om: solar + battery O&M, USD/yr (end of each year).
        gen_kwh_by_year: generator output in years 1..P, kWh.
        diesel_price: USD/litre (constant real price).
        replacement_year: year the battery is replaced (start of year), or None.
        replacement_usd: cost of that replacement, USD at the time.
        rate: discount rate per year, 0-1.

    Returns:
        USD, present value.
    """
    npv = capex_usd
    for year, gen_kwh in enumerate(gen_kwh_by_year, start=1):
        npv += (annual_om + generator_cost_usd(gen_kwh, diesel_price)) * discount(year, rate)
    if replacement_year is not None:
        npv += replacement_usd * discount(replacement_year - 1, rate)
    return npv


def sinking_fund_deposit(amount_usd: float, n_years: int,
                         rate: float = config.PROJECT_DISCOUNT_RATE) -> float:
    """
    Equal end-of-year deposit that grows to `amount_usd` after `n_years` at `rate`.

    deposit = amount x rate / ((1 + rate)^n - 1)   (annuity future-value formula)

    Returns:
        USD/yr (0 if amount is 0).
    """
    if amount_usd <= 0:
        return 0.0
    if n_years < 1:
        raise ValueError("n_years must be >= 1 to save for a replacement")
    if rate == 0:
        return amount_usd / n_years
    return amount_usd * rate / ((1.0 + rate) ** n_years - 1.0)


def levelised_cost_per_kwh(npv_usd: float, kwh_by_year: Sequence[float],
                           rate: float = config.PROJECT_DISCOUNT_RATE) -> float:
    """
    Lifetime cost per kWh served: NPV of cost / NPV of kWh (= annualised cost / annualised kWh).

    Returns:
        USD/kWh.
    """
    kwh_pv = sum(k * discount(y, rate) for y, k in enumerate(kwh_by_year, start=1))
    return npv_usd / kwh_pv


def simple_payback_years(capex_usd: float, annual_diesel_saving_usd: float,
                         annual_om: float) -> float:
    """
    capex / (annual generator saving - annual solar+battery O&M), year-1 values, undiscounted.
    The saving includes avoided generator O&M as well as fuel.

    Returns:
        Years; float("inf") if the system never pays back (net saving <= 0).
    """
    net = annual_diesel_saving_usd - annual_om
    return capex_usd / net if net > 0 else float("inf")


def fuel_shock(load_kw: np.ndarray, gen_kw: np.ndarray, base_price: float,
               annual_om: float) -> List[FuelShockMonth]:
    """
    Monthly cost, diesel-only vs hybrid, under the 2026 price path in config.FUEL_SHOCK_2026.

    Diesel-only: all of that month's load from the generator (fuel + generator O&M).
    Hybrid: that month's generator output (year-1 simulation), fuel + generator O&M,
    plus solar + battery O&M / 12.

    Args:
        load_kw: year-1 hourly load, kW (8760).
        gen_kw: year-1 hourly generator output of the hybrid system, kW (8760).
        base_price: the site's diesel price, USD/litre; config multipliers apply to it.
        annual_om: hybrid O&M, USD/yr.

    Returns:
        List of FuelShockMonth, one per configured month.
    """
    load_m = monthly_sum(load_kw)
    gen_m = monthly_sum(gen_kw)
    out = []
    for month, mult in config.FUEL_SHOCK_2026:
        i = int(month[5:7]) - 1
        price = base_price * mult
        out.append(FuelShockMonth(
            month=month,
            diesel_price_per_litre=round(price, 2),
            cost_diesel_only_usd=round(generator_cost_usd(load_m[i], price)),
            cost_hybrid_usd=round(generator_cost_usd(gen_m[i], price) + annual_om / 12),
        ))
    return out


@dataclass
class Economics:
    npv_hybrid_usd: float            # present cost, solar + battery + remaining generator use
    npv_diesel_only_usd: float       # present cost, all load from the generator
    cost_per_kwh_hybrid_usd: float   # levelised, USD/kWh served
    cost_per_kwh_diesel_usd: float   # levelised, USD/kWh served
    payback_years: float             # simple, year-1 values; inf if never
    annual_saving_year1_usd: float   # generator fuel + O&M avoided in year 1, USD


def economics(capex_usd: float, annual_om: float, load_kwh_by_year: Sequence[float],
              gen_kwh_by_year: Sequence[float], diesel_price: float,
              replacement_year: Optional[int] = None, replacement_usd: float = 0.0,
              rate: float = config.PROJECT_DISCOUNT_RATE) -> Economics:
    """
    Hybrid vs diesel-only economics of a FIXED design at one diesel price and discount rate.

    Args:
        capex_usd: PV + battery up front, USD.
        annual_om: solar + battery O&M, USD/yr.
        load_kwh_by_year: demand in years 1..P, kWh (all served in both cases).
        gen_kwh_by_year: hybrid generator output in years 1..P, kWh.
        diesel_price: USD/litre.
        replacement_year, replacement_usd: planned battery replacement, if any.
        rate: discount rate per year, 0-1.

    Returns:
        Economics.
    """
    npv_h = lifetime_npv_usd(capex_usd, annual_om, gen_kwh_by_year, diesel_price,
                             replacement_year, replacement_usd, rate)
    npv_d = lifetime_npv_usd(0.0, 0.0, load_kwh_by_year, diesel_price, rate=rate)
    saving = (generator_cost_usd(load_kwh_by_year[0], diesel_price)
              - generator_cost_usd(gen_kwh_by_year[0], diesel_price))
    return Economics(
        npv_hybrid_usd=npv_h,
        npv_diesel_only_usd=npv_d,
        cost_per_kwh_hybrid_usd=levelised_cost_per_kwh(npv_h, load_kwh_by_year, rate),
        cost_per_kwh_diesel_usd=levelised_cost_per_kwh(npv_d, load_kwh_by_year, rate),
        payback_years=simple_payback_years(capex_usd, saving, annual_om),
        annual_saving_year1_usd=saving,
    )
