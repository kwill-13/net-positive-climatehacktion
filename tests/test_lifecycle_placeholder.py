import numpy as np
import pytest

from sunsafe.lifecycle_placeholder import capacity_factor, faded_capacity_kwh, grown_load


def test_year_one_unchanged():
    assert capacity_factor("lead_acid", 1) == 1.0
    np.testing.assert_array_equal(grown_load(np.ones(5), 1), np.ones(5))


def test_compounding():
    assert faded_capacity_kwh(1000, "lead_acid", 15) == pytest.approx(1000 * 0.94 ** 14)
    assert faded_capacity_kwh(1000, "lithium", 8) == pytest.approx(1000 * 0.975 ** 7)
    assert grown_load(np.ones(3), 15)[0] == pytest.approx(1.03 ** 14)


def test_year_zero_rejected():
    with pytest.raises(ValueError):
        capacity_factor("lithium", 0)
