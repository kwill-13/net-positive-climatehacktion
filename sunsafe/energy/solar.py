"""
Solar resource and PV output.

`fetch_weather` gets one year of hourly GHI and air temperature from NASA POWER
(cached on disk), and `pv_output_per_kw` turns it into kW of output per kW installed.
"""

import json
import logging

import numpy as np
import pandas as pd
import requests

from sunsafe import config

log = logging.getLogger(__name__)

NASA_FILL_VALUE = -999.0  # NASA POWER marks missing data with -999


def _cache_path(lat: float, lon: float, year: int):
    return config.CACHE_DIR / f"nasa_power_{lat:.3f}_{lon:.3f}_{year}.json"


def _download(lat: float, lon: float, year: int) -> dict:
    """Raw NASA POWER hourly JSON for one point and year (from cache if present)."""
    path = _cache_path(lat, lon, year)
    if path.exists():
        return json.loads(path.read_text())

    params = {
        "parameters": config.NASA_POWER_PARAMETERS,
        "community": config.NASA_POWER_COMMUNITY,
        "latitude": lat,
        "longitude": lon,
        "start": f"{year}0101",
        "end": f"{year}1231",
        "format": "JSON",
        "time-standard": config.NASA_POWER_TIME_STANDARD,
    }
    resp = requests.get(config.NASA_POWER_HOURLY_URL, params=params,
                        timeout=config.NASA_POWER_TIMEOUT_S)
    resp.raise_for_status()
    data = resp.json()
    data["properties"]["parameter"]  # fail here (KeyError) rather than cache a bad response
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data


def _parse(data: dict) -> pd.DataFrame:
    """NASA POWER JSON -> hourly DataFrame (ghi_w_m2, temp_c), Feb 29 dropped, gaps filled."""
    p = data["properties"]["parameter"]
    df = pd.DataFrame({
        "ghi_w_m2": pd.Series(p["ALLSKY_SFC_SW_DWN"], dtype=float),
        "temp_c": pd.Series(p["T2M"], dtype=float),
    })
    df.index = pd.to_datetime(df.index, format="%Y%m%d%H")
    df = df.sort_index()
    df = df[~((df.index.month == 2) & (df.index.day == 29))]
    df = df.replace(NASA_FILL_VALUE, np.nan)
    n_missing = int(df.isna().sum().sum())
    if n_missing:
        log.warning("NASA POWER: %d missing values, filled by interpolation", n_missing)
        df = df.interpolate(limit_direction="both")
    df["ghi_w_m2"] = df["ghi_w_m2"].clip(lower=0.0)
    if len(df) != config.HOURS_PER_YEAR:
        raise ValueError(f"expected {config.HOURS_PER_YEAR} hours, got {len(df)}")
    return df


def synthetic_tropical_weather(year: int = config.WEATHER_YEAR) -> pd.DataFrame:
    """
    Made-up but plausible tropical weather, used only when NASA POWER is unreachable.

    GHI: half-sine from 06:00 to 18:00 local solar time, ~5.5 kWh/m2/day on average,
    with a fixed-seed day-to-day cloudiness factor (0.55-1.15). Temp: 27 degC +/- 1.5 degC.

    Returns:
        DataFrame, 8760 rows, columns ghi_w_m2 (W/m2) and temp_c (degC),
        with df.attrs["source"] = "synthetic".
    """
    rng = np.random.default_rng(42)
    hours = np.arange(24)
    shape = np.clip(np.sin(np.pi * (hours + 0.5 - 6) / 12), 0, None)  # hour-centred, 06-18
    cloud = rng.uniform(0.55, 1.15, size=365)
    peak = 5500.0 / (shape.sum() * cloud.mean())      # W/m2, so the year averages 5.5 kWh/m2/day
    ghi = (cloud[:, None] * peak * shape[None, :]).ravel()
    temp = (27.0 + 1.5 * np.sin(2 * np.pi * (hours - 9) / 24))[None, :].repeat(365, 0).ravel()
    index = pd.date_range(f"{year}-01-01", periods=8784, freq="h")
    index = index[~((index.month == 2) & (index.day == 29))][: config.HOURS_PER_YEAR]
    df = pd.DataFrame({"ghi_w_m2": ghi, "temp_c": temp}, index=index)
    df.attrs["source"] = "synthetic"
    return df


def fetch_weather(lat: float, lon: float, year: int = config.WEATHER_YEAR) -> pd.DataFrame:
    """
    One year of hourly weather for a point, from NASA POWER (community RE, local solar time).

    Responses are cached in data/cache/ by lat/lon/year. Feb 29 is dropped so the result
    is always 8760 rows. If the request fails, falls back to `synthetic_tropical_weather`
    and logs a warning; check df.attrs["source"] ("nasa_power" or "synthetic").

    Args:
        lat: latitude, decimal degrees (south negative).
        lon: longitude, decimal degrees (west negative).
        year: calendar year of data.

    Returns:
        DataFrame indexed by local-solar-time hour, 8760 rows:
        ghi_w_m2 (global horizontal irradiance, W/m2), temp_c (2 m air temperature, degC).
    """
    try:
        df = _parse(_download(lat, lon, year))
        df.attrs["source"] = "nasa_power"
        return df
    except Exception as exc:  # network, HTTP, bad JSON, wrong length: all fall back
        log.warning("NASA POWER fetch failed for (%s, %s, %s): %s. "
                    "USING SYNTHETIC TROPICAL WEATHER.", lat, lon, year, exc)
        return synthetic_tropical_weather(year)


def pv_output_per_kw(weather: pd.DataFrame) -> np.ndarray:
    """
    Hourly PV output per kW installed, horizontal array (fine near the equator).

    output = GHI/1000 x derate x (1 - 0.004 x (cell_temp - 25)),
    cell_temp = air_temp + 0.03 x GHI. Coefficients in config.py.

    Args:
        weather: DataFrame with ghi_w_m2 (W/m2) and temp_c (degC), as from fetch_weather.

    Returns:
        np.ndarray, shape (8760,), kW AC per kW DC installed (equivalently kWh/kW per hour).
    """
    ghi = weather["ghi_w_m2"].to_numpy(dtype=float)
    temp = weather["temp_c"].to_numpy(dtype=float)
    cell_temp = temp + config.PV_CELL_TEMP_RISE_PER_W_M2 * ghi
    temp_factor = 1.0 - config.PV_TEMP_COEFF_PER_C * (cell_temp - config.PV_STC_CELL_TEMP_C)
    out = ghi / config.PV_STC_IRRADIANCE_W_M2 * config.PV_DERATE * temp_factor
    return np.clip(out, 0.0, None)
