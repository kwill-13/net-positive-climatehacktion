import numpy as np
import pytest

from sunsafe.energy import headroom as hr


def test_surplus_by_month_sums_to_total():
    x = np.ones(8760)
    months = hr.surplus_by_month(x)
    assert len(months) == 12 and sum(months) == pytest.approx(8760)
    assert months[1] == pytest.approx(28 * 24)


def test_suggested_loads_fit_leanest_month():
    surplus = [31 * 25.0] * 12                      # 25 kWh/day every month (Feb: more per day)
    picked = hr.suggest_new_loads(surplus, [("a", 8), ("b", 12), ("c", 15)])
    assert picked == [("a", 8), ("b", 12)]          # 20 fits, adding 15 would not


def test_electricity_share():
    assert hr.electricity_share(600, 1800) == pytest.approx(0.25)
    assert hr.electricity_share(600, 1800, 35) == pytest.approx(635 / 2400)
