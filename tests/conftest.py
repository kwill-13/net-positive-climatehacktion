"""Shared fixtures. Use synthetic weather so tests run offline and deterministically."""

import pytest

from sunsafe.energy.solar import pv_output_per_kw, synthetic_tropical_weather
from sunsafe.load_profiles import village_profile


@pytest.fixture(scope="session")
def pv_per_kw():
    return pv_output_per_kw(synthetic_tropical_weather())


@pytest.fixture(scope="session")
def load_kw():
    return village_profile(600.0)  # kW hourly, 600 kWh/day


@pytest.fixture(scope="session")
def lead_acid_run():
    """
    One full run_sunsafe_detailed for a lead-acid site (slow, ~10 s, so shared).
    Offline (synthetic weather), and run_sunsafe_fake is patched to raise, to prove the
    real model never falls back to it.
    """
    from sunsafe import interface, model
    from sunsafe.interface import Inputs

    def _no_fake(*a, **k):
        raise AssertionError("run_sunsafe_fake must not be called")

    mp = pytest.MonkeyPatch()
    mp.setattr(model, "fetch_weather", lambda lat, lon: synthetic_tropical_weather())
    mp.setattr(interface, "run_sunsafe_fake", _no_fake)
    inputs = Inputs(site_name="Test atoll", latitude=-9.38, longitude=-171.24,
                    diesel_litres_per_day=200, diesel_price_per_litre=1.10,
                    renewable_target=0.90, battery_chemistry="lead_acid")
    try:
        results, comp = model.run_sunsafe_detailed(inputs)
    finally:
        mp.undo()
    return inputs, results, comp
