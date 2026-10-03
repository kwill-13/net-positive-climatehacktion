import dataclasses

import sunsafe.interface
import sunsafe_interface
from sunsafe import config, model
from sunsafe.interface import (Finance, FuelShockMonth, Headroom, LifecycleYear, Results,
                               Sizing)


def test_run_sunsafe_matches_contract(lead_acid_run):
    inputs, real, _ = lead_acid_run
    assert isinstance(real, Results)
    for f in dataclasses.fields(Results):
        assert hasattr(real, f.name), f.name
    assert isinstance(real.sizing, Sizing) and isinstance(real.finance, Finance)
    assert isinstance(real.headroom, Headroom)
    assert all(isinstance(y, LifecycleYear) for y in real.lifecycle)
    assert all(isinstance(m, FuelShockMonth) for m in real.fuel_shock)
    assert real.sizing.pv_kw > 0 and real.sizing.battery_kwh >= 0
    assert real.backup_hours >= 0
    assert len(real.lifecycle) == inputs.project_years
    assert len(real.headroom.surplus_kwh_by_month) == 12
    assert any("SYNTHETIC" in w for w in real.warnings)


def test_no_fake_model_left(lead_acid_run):
    # The fake implementation has been removed: the contract holds data definitions only,
    # and the root shim runs the real model.
    assert not hasattr(sunsafe.interface, "run_sunsafe_fake")
    assert not hasattr(sunsafe.interface, "run_sunsafe")
    assert sunsafe_interface.run_sunsafe is model.run_sunsafe
    _, real, _ = lead_acid_run
    assert not any("FAKE" in w for w in real.warnings)


def test_lifecycle_fields_follow_contract(lead_acid_run):
    inputs, real, comp = lead_acid_run
    rec = comp.recommended
    for ly, planned in zip(real.lifecycle, rec.years):
        assert ly.share_funded_year_15 == round(planned.renewable_share, 4)
        assert ly.share_funded_day_one <= ly.share_funded_year_15 + 1e-9
    # battery_capacity_kwh is usable, never-replaced capacity: it only goes down.
    caps = [ly.battery_capacity_kwh for ly in real.lifecycle]
    assert caps == sorted(caps, reverse=True)


def test_fuel_shock_hybrid_cheaper_every_month(lead_acid_run):
    _, real, _ = lead_acid_run
    assert [m.month for m in real.fuel_shock] == [m for m, _ in config.FUEL_SHOCK_2026]
    for m in real.fuel_shock:
        assert m.cost_hybrid_usd < m.cost_diesel_only_usd, m.month
