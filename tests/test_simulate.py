import time

import numpy as np
import pytest

from sunsafe import config
from sunsafe.energy.simulate import simulate

TOL = 1e-6
CASES = [  # (pv_kw, battery_kwh, chemistry)
    (0.0, 0.0, "lithium"),
    (100.0, 0.0, "lead_acid"),
    (150.0, 400.0, "lithium"),
    (300.0, 1500.0, "lead_acid"),
    (800.0, 3000.0, "lithium"),
]


@pytest.mark.parametrize("pv_kw,battery_kwh,chem", CASES)
def test_energy_balance_every_hour(pv_kw, battery_kwh, chem, load_kw, pv_per_kw):
    r = simulate(pv_kw, battery_kwh, load_kw, pv_per_kw, chem)
    np.testing.assert_allclose(r.pv_used + r.discharge + r.gen, load_kw, atol=TOL)
    np.testing.assert_allclose(r.pv_used + r.charge + r.curtailed, pv_kw * pv_per_kw, atol=TOL)
    for arr in (r.pv_used, r.charge, r.discharge, r.gen, r.curtailed):
        assert arr.min() >= -TOL


@pytest.mark.parametrize("pv_kw,battery_kwh,chem", [c for c in CASES if c[1] > 0])
def test_battery_energy_bookkeeping(pv_kw, battery_kwh, chem, load_kw, pv_per_kw):
    """Stored energy change over the year = charge in x eta_c - discharge out / eta_d."""
    r = simulate(pv_kw, battery_kwh, load_kw, pv_per_kw, chem, start_soc=1.0)
    eta = np.sqrt(config.BATTERY[chem]["round_trip_eff"])
    delta = (r.soc[-1] - 1.0) * battery_kwh
    assert delta == pytest.approx(r.charge.sum() * eta - r.discharge.sum() / eta, abs=1e-6)


@pytest.mark.parametrize("pv_kw,battery_kwh,chem", [c for c in CASES if c[1] > 0])
def test_soc_within_limits(pv_kw, battery_kwh, chem, load_kw, pv_per_kw):
    r = simulate(pv_kw, battery_kwh, load_kw, pv_per_kw, chem)
    min_soc = config.BATTERY[chem]["min_soc"]
    assert r.soc.min() >= min_soc - TOL
    assert r.soc.max() <= 1.0 + TOL


def test_zero_pv_zero_battery_all_generator(load_kw, pv_per_kw):
    r = simulate(0.0, 0.0, load_kw, pv_per_kw, "lithium")
    assert r.renewable_share == pytest.approx(0.0, abs=TOL)
    np.testing.assert_allclose(r.gen, load_kw, atol=TOL)
    assert r.gen_kwh == pytest.approx(load_kw.sum())
    assert r.diesel_litres == pytest.approx(load_kw.sum() / config.DIESEL_KWH_PER_LITRE)


def test_huge_system_nearly_all_renewable(load_kw, pv_per_kw):
    avg_kw = load_kw.mean()
    r = simulate(20 * avg_kw, 5 * load_kw.sum() / 365, load_kw, pv_per_kw, "lithium")
    assert r.renewable_share > 0.99


def test_more_battery_never_worse(load_kw, pv_per_kw):
    shares = [simulate(200.0, b, load_kw, pv_per_kw, "lithium").renewable_share
              for b in (0, 200, 600, 1200)]
    assert shares == sorted(shares)


def test_faded_battery_reduces_share(load_kw, pv_per_kw):
    """What the lifecycle model relies on: smaller nominal capacity -> more diesel."""
    new = simulate(200.0, 800.0, load_kw, pv_per_kw, "lead_acid")
    faded = simulate(200.0, 800.0 * 0.6, load_kw, pv_per_kw, "lead_acid")
    assert faded.gen_kwh > new.gen_kwh


def test_mismatched_lengths_rejected(load_kw, pv_per_kw):
    with pytest.raises(ValueError):
        simulate(100.0, 100.0, load_kw[:100], pv_per_kw, "lithium")


def test_unknown_chemistry_rejected(load_kw, pv_per_kw):
    with pytest.raises(ValueError):
        simulate(100.0, 100.0, load_kw, pv_per_kw, "lead-acid")


def test_one_year_well_under_a_second(load_kw, pv_per_kw):
    t0 = time.perf_counter()
    simulate(300.0, 1500.0, load_kw, pv_per_kw, "lead_acid")
    assert time.perf_counter() - t0 < 0.2
