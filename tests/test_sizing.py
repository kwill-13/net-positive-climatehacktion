import pytest

from sunsafe.energy.simulate import simulate
from sunsafe.energy.sizing import capital_recovery_factor, size_system


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
