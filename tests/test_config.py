import pytest

from sunsafe import config


def test_tokelau_diesel_price_matches_its_derivation():
    # mean Apia retail (WST/L) x WST->USD x freight markup to Tokelau
    wst = [p for _, p in config.FUEL_SHOCK_APIA_WST_PER_L]
    derived = sum(wst) / len(wst) * config.WST_TO_USD * config.TOKELAU_DIESEL_FREIGHT_MARKUP
    assert config.TOKELAU_DIESEL_PRICE_USD_PER_L == pytest.approx(derived, abs=0.005)


def test_diesel_price_scenarios_bracket_default():
    assert (config.TOKELAU_DIESEL_PRICE_LOW_USD_PER_L
            < config.TOKELAU_DIESEL_PRICE_USD_PER_L
            < config.TOKELAU_DIESEL_PRICE_HIGH_USD_PER_L)
