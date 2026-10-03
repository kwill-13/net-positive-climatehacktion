import pytest

from sunsafe.lifecycle.degradation import battery_capacity
from sunsafe.lifecycle.projection import run_years


def test_no_replacement_fades_every_year(load_kw, pv_per_kw):
    ys = run_years(200, 800, load_kw, pv_per_kw, "lead_acid", years=6)
    assert [y.year for y in ys] == [1, 2, 3, 4, 5, 6]
    assert [y.battery_year for y in ys] == [1, 2, 3, 4, 5, 6]
    for y in ys:
        assert y.battery_kwh == pytest.approx(battery_capacity(y.year, 800, "lead_acid"))
    assert ys[0].renewable_share > ys[-1].renewable_share


def test_replacement_resets_capacity_in_that_year(load_kw, pv_per_kw):
    ys = run_years(200, 800, load_kw, pv_per_kw, "lead_acid", years=10, replace_battery_in=[7])
    assert ys[5].battery_kwh == pytest.approx(battery_capacity(6, 800, "lead_acid"))
    assert ys[6].battery_year == 1 and ys[6].battery_kwh == pytest.approx(800)
    assert ys[9].battery_kwh == pytest.approx(battery_capacity(4, 800, "lead_acid"))
    # Replacing beats not replacing in the same year (demand growth can still pull the share
    # below the previous year's, so compare like years).
    never = run_years(200, 800, load_kw, pv_per_kw, "lead_acid", years=10)
    assert ys[6].renewable_share > never[6].renewable_share


def test_demand_grows(load_kw, pv_per_kw):
    ys = run_years(200, 800, load_kw, pv_per_kw, "lithium", years=3, growth=0.10)
    assert ys[0].demand_kwh_per_day == pytest.approx(600)
    assert ys[2].demand_kwh_per_day == pytest.approx(600 * 1.21)


def test_staged_upgrade_changes_pv_and_installs_new_battery(load_kw, pv_per_kw):
    ys = run_years(150, 500, load_kw, pv_per_kw, "lead_acid", years=8,
                   upgrade_in=5, upgrade_pv_kw=250, upgrade_battery_kwh=900)
    assert [y.pv_kw for y in ys] == [150] * 4 + [250] * 4
    assert ys[3].battery_kwh == pytest.approx(battery_capacity(4, 500, "lead_acid"))
    assert ys[4].battery_year == 1 and ys[4].battery_kwh == pytest.approx(900)
    no_upgrade = run_years(150, 500, load_kw, pv_per_kw, "lead_acid", years=8)
    assert ys[4].renewable_share > no_upgrade[4].renewable_share
