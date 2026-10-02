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
