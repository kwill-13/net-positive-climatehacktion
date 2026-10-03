"""Strategy D (rolling plan): every stage keeps the target through its own end."""

import pytest

from sunsafe import config
from sunsafe.energy.sizing import size_system
from sunsafe.lifecycle.degradation import GrowthSchedule
from sunsafe.lifecycle.strategy import rolling_plan
from sunsafe.load_profiles import village_profile

# Offline "sites": synthetic weather scaled for sunnier / cloudier places, different loads,
# chemistries, targets and growth paths.
SITES = {
    "sunny atoll, lithium 90%": (1.10, 300.0, "lithium", 0.90, 0.03),
    "cloudy island, lead-acid 95%": (0.85, 600.0, "lead_acid", 0.95, GrowthSchedule(0.09, 5, 0.03)),
    "mid, lithium 95%, 9% growth": (1.00, 450.0, "lithium", 0.95, 0.09),
}


def _sized_lookup(load_kw, pv_per_kw, target, chem, growth):
    cache = {}

    def sized(design_year, battery_year):
        key = (design_year, battery_year)
        if key not in cache:
            cache[key] = size_system(load_kw, pv_per_kw, target, chem, config.TOKELAU_DIESEL_PRICE_USD_PER_L,
                                     design_year=design_year, demand_growth=growth,
                                     battery_year=battery_year)
        return cache[key]
    return sized


@pytest.mark.parametrize("site", list(SITES))
@pytest.mark.parametrize("project_years", [10, 15, 25])
def test_rolling_plan_meets_target_every_year(site, project_years, pv_per_kw):
    scale, daily_kwh, chem, target, growth = SITES[site]
    load_kw, pv = village_profile(daily_kwh), pv_per_kw * scale
    sized = _sized_lookup(load_kw, pv, target, chem, growth)
    plans = [rolling_plan(k, sized, load_kw, pv, target, chem, config.TOKELAU_DIESEL_PRICE_USD_PER_L,
                          project_years, growth, merge_short_last=merge)
             for k in config.ROLLING_STAGE_YEARS for merge in (False, True)]
    plans = [p for p in plans if p is not None]
    assert plans                                    # 10 yrs with K=6 or 8 still has two stages
    for p in plans:
        assert len(p.years) == project_years
        assert p.meets_target_every_year, (p.name, min(y.renewable_share for y in p.years))
        assert [st.year for st in p.stages] == sorted({st.year for st in p.stages})
        for st in p.stages[1:]:                     # new battery from the stage's start year
            y = p.years[st.year - 1]
            assert y.battery_year == 1 and y.battery_kwh == pytest.approx(st.battery_installed_kwh)
            assert st.pv_added_kw >= 0 and st.capex_usd > 0


def test_rolling_plan_none_when_project_fits_one_stage(pv_per_kw, load_kw):
    sized = _sized_lookup(load_kw, pv_per_kw, 0.9, "lithium", 0.03)
    assert rolling_plan(10, sized, load_kw, pv_per_kw, 0.9, "lithium", 1.87, 10, 0.03) is None
