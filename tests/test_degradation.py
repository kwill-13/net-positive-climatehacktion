import numpy as np
import pytest

from sunsafe.lifecycle.degradation import battery_capacity, capacity_factor, demand, pv_derate


def test_year_one_unchanged():
    assert capacity_factor("lead_acid", 1) == 1.0
    assert pv_derate(1) == 1.0
    np.testing.assert_array_equal(demand(1, np.ones(5)), np.ones(5))


def test_compounding():
    assert battery_capacity(15, 1000, "lead_acid") == pytest.approx(1000 * 0.94 ** 14)
    assert battery_capacity(8, 1000, "lithium") == pytest.approx(1000 * 0.975 ** 7)
    assert battery_capacity(3, 1000, "lithium", fade=0.10) == pytest.approx(810)
    assert demand(15, np.ones(3))[0] == pytest.approx(1.03 ** 14)
    assert pv_derate(11) == pytest.approx(0.995 ** 10)


def test_year_zero_rejected():
    with pytest.raises(ValueError):
        capacity_factor("lithium", 0)
