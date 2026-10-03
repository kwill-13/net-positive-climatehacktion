import pytest

from sunsafe.energy.simulate import simulate
from sunsafe.energy.sizing import capital_recovery_factor, size_system
from sunsafe.lifecycle.degradation import battery_capacity, demand


@pytest.mark.parametrize("chem,target", [("lithium", 0.90), ("lead_acid", 0.95), ("lithium", 0.5)])
def test_sized_system_meets_target_when_resimulated(chem, target, load_kw, pv_per_kw):
    opt = size_system(load_kw, pv_per_kw, target, chem, diesel_price=1.10)
    assert opt.meets_target
    r = simulate(opt.pv_kw, opt.battery_kwh, load_kw, pv_per_kw, chem)
    assert r.renewable_share >= target - 1e-9
    assert r.renewable_share == pytest.approx(opt.renewable_share)
    assert opt.sim is not None and opt.sim.renewable_share == pytest.approx(opt.renewable_share)


def test_higher_target_costs_more(load_kw, pv_per_kw):
    lo = size_system(load_kw, pv_per_kw, 0.80, "lithium", 1.10)
    hi = size_system(load_kw, pv_per_kw, 0.97, "lithium", 1.10)
    assert hi.annualised_cost_usd >= lo.annualised_cost_usd


def test_unreachable_target_is_flagged(load_kw, pv_per_kw):
    opt = size_system(load_kw, pv_per_kw, 1.01, "lead_acid", 1.10)
    assert not opt.meets_target
    assert opt.sim is not None


def test_crf_known_values():
    assert capital_recovery_factor(0.08, 20) == pytest.approx(0.101852, abs=1e-6)
    assert capital_recovery_factor(0.0, 10) == pytest.approx(0.1)


@pytest.mark.parametrize("chem", ["lead_acid", "lithium"])
def test_design_year_sizing_meets_target_in_that_year(chem, load_kw, pv_per_kw):
    year, target = 15, 0.90
    opt = size_system(load_kw, pv_per_kw, target, chem, 1.10, design_year=year)
    assert opt.meets_target and opt.design_year == year
    r = simulate(opt.pv_kw, battery_capacity(year, opt.battery_kwh, chem),
                 demand(year, load_kw), pv_per_kw, chem)
    assert r.renewable_share >= target - 1e-9
    assert r.renewable_share == pytest.approx(opt.renewable_share)
    # Sized for a faded battery and bigger load, so it costs more up front than year 1.
    year1 = size_system(load_kw, pv_per_kw, target, chem, 1.10)
    assert opt.capex_usd > year1.capex_usd


def test_design_year_one_is_default(load_kw, pv_per_kw):
    a = size_system(load_kw, pv_per_kw, 0.9, "lithium", 1.10)
    b = size_system(load_kw, pv_per_kw, 0.9, "lithium", 1.10, design_year=1)
    assert (a.pv_kw, a.battery_kwh, a.annualised_cost_usd) == (b.pv_kw, b.battery_kwh,
                                                               b.annualised_cost_usd)
