"""
Hourly dispatch of a solar + battery + diesel mini-grid for one year.

Used by sizing (many times) and by the lifecycle model (once per year, with faded
battery capacity and grown demand). Keep the signature stable.

Dispatch rule, each hour:
  1. Solar serves load directly.
  2. Surplus solar charges the battery (charge losses applied); what doesn't fit is curtailed.
  3. Any deficit is drawn from the battery down to min SOC (discharge losses applied).
  4. The diesel generator covers the rest. It is unlimited, so unmet load is always 0.

Simplifications (deliberate, for now): no battery power (C-rate) limit, no inverter
limit, no generator minimum load, and the generator never charges the battery.
Time step is 1 hour, so kW and kWh per step are numerically equal.
"""

import math
from typing import Optional
from dataclasses import dataclass

import numpy as np

from sunsafe import config
from sunsafe.energy.diesel import litres_from_kwh


@dataclass
class SimResult:
    """
    One simulated year. Hourly arrays have one value per hour (normally 8760), in kW
    (= kWh in that hour).
    """
    # inputs, echoed back
    pv_kw: float                 # kWp installed
    battery_kwh: float           # nominal capacity used for this run (possibly faded)
    chemistry: str               # "lithium" or "lead_acid"

    # hourly arrays
    pv_avail: np.ndarray         # kW, PV that could be produced
    pv_used: np.ndarray          # kW, PV serving load directly
    charge: np.ndarray           # kW, PV sent into the battery (before charge losses)
    discharge: np.ndarray        # kW, delivered from battery to load (after discharge losses)
    soc: np.ndarray              # 0-1 of nominal capacity, at the END of each hour (0 if no battery)
    gen: np.ndarray              # kW, diesel generator output
    curtailed: np.ndarray        # kW, PV thrown away (battery full, load met)

    # annual summary
    load_kwh: float              # kWh/yr demand
    pv_kwh: float                # kWh/yr PV available
    renewable_share: float       # 0-1, 1 - gen_kwh / load_kwh
    gen_kwh: float               # kWh/yr from diesel
    curtailed_kwh: float         # kWh/yr curtailed
    diesel_litres: float         # litres/yr burned


def battery_params(chemistry: str) -> dict:
    """
    Battery parameters for a chemistry, from config.BATTERY.

    Returns:
        dict with min_soc (0-1), round_trip_eff (0-1), life_years (years),
        eta_charge and eta_discharge (0-1, each sqrt of round-trip).
    """
    if chemistry not in config.BATTERY:
        raise ValueError(f"unknown chemistry {chemistry!r}; use one of {list(config.BATTERY)}")
    p = dict(config.BATTERY[chemistry])
    p["eta_charge"] = p["eta_discharge"] = math.sqrt(p["round_trip_eff"])
    return p


def simulate(pv_kw: float, battery_kwh: float, load_kw: np.ndarray, pv_per_kw: np.ndarray,
             chemistry: str = "lithium", start_soc: float = 1.0,
             min_soc: Optional[float] = None) -> SimResult:
    """
    Simulate one year of hourly operation.

    Args:
        pv_kw: installed PV, kWp.
        battery_kwh: NOMINAL battery capacity, kWh. Pass a faded value for later years;
            usable energy is (1 - min_soc) x battery_kwh.
        load_kw: hourly demand, kW, shape (N,) (normally 8760).
        pv_per_kw: hourly PV output per kW installed, kW/kWp, same shape as load_kw.
        chemistry: "lithium" or "lead_acid" (sets min SOC and efficiencies).
        start_soc: state of charge at the start of hour 0, 0-1. Clamped to [min_soc, 1].
        min_soc: override the chemistry's minimum state of charge, 0-1 (e.g. operators who start
            the generator at 60%). None uses config.BATTERY[chemistry]["min_soc"].

    Returns:
        SimResult with hourly arrays and annual summary.
    """
    load = np.asarray(load_kw, dtype=float)
    pv_per_kw = np.asarray(pv_per_kw, dtype=float)
    if load.shape != pv_per_kw.shape or load.ndim != 1:
        raise ValueError(f"load_kw {load.shape} and pv_per_kw {pv_per_kw.shape} must be equal 1-D")
    if pv_kw < 0 or battery_kwh < 0:
        raise ValueError("pv_kw and battery_kwh must be >= 0")

    p = battery_params(chemistry)
    if min_soc is not None:
        p["min_soc"] = min_soc
    eta_c, eta_d = p["eta_charge"], p["eta_discharge"]
    e_max = float(battery_kwh)
    e_min = p["min_soc"] * e_max
    e = min(max(start_soc, p["min_soc"]), 1.0) * e_max   # kWh stored now

    pv_avail = pv_kw * pv_per_kw
    # Solar to load is independent of the battery, so do it vectorised.
    pv_used = np.minimum(pv_avail, load)
    surplus = (pv_avail - pv_used).tolist()
    deficit = (load - pv_used).tolist()

    n = len(load)
    charge = [0.0] * n
    discharge = [0.0] * n
    stored = [0.0] * n
    # Plain-Python loop over lists: ~2-3x faster than indexing numpy arrays per hour.
    for t in range(n):
        s = surplus[t]
        if s > 0.0:
            c = min(s, (e_max - e) / eta_c)
            e += c * eta_c
            charge[t] = c
        else:
            d = deficit[t]
            if d > 0.0:
                out = min(d, (e - e_min) * eta_d)
                if out > 0.0:
                    e = max(e - out / eta_d, e_min)
                    discharge[t] = out
        stored[t] = e

    charge = np.array(charge)
    discharge = np.array(discharge)
    curtailed = np.array(surplus) - charge
    gen = np.array(deficit) - discharge
    soc = np.array(stored) / e_max if e_max > 0 else np.zeros(n)

    load_kwh = float(load.sum())
    gen_kwh = float(gen.sum())
    return SimResult(
        pv_kw=float(pv_kw), battery_kwh=e_max, chemistry=chemistry,
        pv_avail=pv_avail, pv_used=pv_used, charge=charge, discharge=discharge,
        soc=soc, gen=gen, curtailed=curtailed,
        load_kwh=load_kwh,
        pv_kwh=float(pv_avail.sum()),
        renewable_share=1.0 - gen_kwh / load_kwh if load_kwh > 0 else 1.0,
        gen_kwh=gen_kwh,
        curtailed_kwh=float(curtailed.sum()),
        diesel_litres=litres_from_kwh(gen_kwh),
    )


def annual_gen_kwh(pv_kw: float, battery_kwh: float, load_kw: np.ndarray, pv_per_kw: np.ndarray,
                   chemistry: str = "lithium") -> float:
    """
    Generator kWh for one year: the same dispatch and arithmetic as simulate() (start_soc 1.0,
    chemistry min SOC), but keeps no hourly arrays. Used by the sizing grid search, where only
    the total is needed; gives exactly simulate(...).gen_kwh, about twice as fast.

    Args:
        as simulate().

    Returns:
        Generator output, kWh/yr.
    """
    load = np.asarray(load_kw, dtype=float)
    p = battery_params(chemistry)
    eta_c, eta_d = p["eta_charge"], p["eta_discharge"]
    e_max = float(battery_kwh)
    e_min = p["min_soc"] * e_max
    e = min(max(1.0, p["min_soc"]), 1.0) * e_max

    pv_avail = pv_kw * np.asarray(pv_per_kw, dtype=float)
    pv_used = np.minimum(pv_avail, load)
    surplus = (pv_avail - pv_used).tolist()
    deficit_arr = load - pv_used
    deficit = deficit_arr.tolist()

    discharge = [0.0] * len(load)
    for t, s in enumerate(surplus):
        if s > 0.0:
            e += min(s, (e_max - e) / eta_c) * eta_c
        else:
            d = deficit[t]
            if d > 0.0:
                out = min(d, (e - e_min) * eta_d)
                if out > 0.0:
                    e = max(e - out / eta_d, e_min)
                    discharge[t] = out
    return float((deficit_arr - np.array(discharge)).sum())
