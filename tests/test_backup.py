import math

import pytest

from sunsafe.energy.backup import backup_hours


def test_lead_acid_usable_half():
    # 100 kWh x (1 - 0.5) x sqrt(0.80) / 5 kW
    assert backup_hours(100, "lead_acid", 5.0) == pytest.approx(50 * math.sqrt(0.8) / 5)


def test_lithium_beats_lead_acid_same_nominal():
    assert backup_hours(100, "lithium", 5.0) > backup_hours(100, "lead_acid", 5.0)


def test_zero_battery_zero_hours():
    assert backup_hours(0, "lithium", 5.0) == 0.0


def test_zero_critical_load_rejected():
    with pytest.raises(ValueError):
        backup_hours(100, "lithium", 0.0)
