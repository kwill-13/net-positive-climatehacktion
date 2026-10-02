import dataclasses

from sunsafe import model
from sunsafe.energy.solar import synthetic_tropical_weather
from sunsafe.interface import Inputs, Results, run_sunsafe_fake


def _inputs(**kw):
    base = dict(site_name="Test atoll", latitude=-9.38, longitude=-171.24,
                diesel_litres_per_day=200, diesel_price_per_litre=1.10)
    base.update(kw)
    return Inputs(**base)


def test_run_sunsafe_matches_contract(monkeypatch):
    # Offline: synthetic weather has no attrs["source"] == "nasa_power", so expect that warning.
    monkeypatch.setattr(model, "fetch_weather", lambda lat, lon: synthetic_tropical_weather())
    inputs = _inputs()
    real, fake = model.run_sunsafe(inputs), run_sunsafe_fake(inputs)
    assert isinstance(real, Results)
    assert [f.name for f in dataclasses.fields(real)] == [f.name for f in dataclasses.fields(fake)]
    assert real.sizing.renewable_share_year1 >= inputs.renewable_target
    assert real.sizing.pv_kw > 0 and real.sizing.battery_kwh >= 0
    assert real.backup_hours >= 0
    assert any("FAKE DATA" in w and "lifecycle" in w for w in real.warnings)
    assert any("SYNTHETIC" in w for w in real.warnings)
