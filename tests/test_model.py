import dataclasses

from sunsafe import model
from sunsafe.interface import Results, run_sunsafe_fake


def test_run_sunsafe_matches_contract(lead_acid_run):
    inputs, real, _ = lead_acid_run
    fake = run_sunsafe_fake(inputs)
    assert isinstance(real, Results)
    assert [f.name for f in dataclasses.fields(real)] == [f.name for f in dataclasses.fields(fake)]
    assert real.sizing.pv_kw > 0 and real.sizing.battery_kwh >= 0
    assert real.backup_hours >= 0
    assert len(real.lifecycle) == inputs.project_years
    assert len(real.headroom.surplus_kwh_by_month) == 12
    assert any("SYNTHETIC" in w for w in real.warnings)


def test_run_sunsafe_uses_nothing_from_the_fake(lead_acid_run):
    # The fixture ran with run_sunsafe_fake patched to raise, so getting here proves it was
    # never called. Also: the model no longer imports it, and no FAKE warning remains.
    _, real, _ = lead_acid_run
    assert not hasattr(model, "run_sunsafe_fake")
    assert not any("FAKE" in w for w in real.warnings)
    fake = run_sunsafe_fake(real.inputs)
    for name in ("sizing", "lifecycle", "finance", "fuel_shock", "headroom"):
        assert getattr(real, name) != getattr(fake, name), name


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
    assert len(real.fuel_shock) == 6
    for m in real.fuel_shock:
        assert m.cost_hybrid_usd < m.cost_diesel_only_usd, m.month
