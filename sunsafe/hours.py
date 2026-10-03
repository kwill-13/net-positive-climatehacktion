"""Calendar helpers for 8760-hour arrays (non-leap year, hour 0 = 1 Jan 00:00)."""

import numpy as np

DAYS_IN_MONTH = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
MONTH_OF_HOUR = np.repeat(np.arange(12), DAYS_IN_MONTH * 24)   # 0 = Jan ... 11 = Dec


def monthly_sum(hourly: np.ndarray) -> np.ndarray:
    """
    Sum an 8760 hourly series by calendar month.

    Args:
        hourly: shape (8760,), e.g. kW per hour (= kWh).

    Returns:
        np.ndarray shape (12,), Jan-Dec totals (e.g. kWh per month).
    """
    return np.bincount(MONTH_OF_HOUR, weights=np.asarray(hourly, dtype=float), minlength=12)
