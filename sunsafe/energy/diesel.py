"""Diesel generator fuel use and cost."""

from sunsafe import config


def litres_from_kwh(gen_kwh: float, kwh_per_litre: float = config.DIESEL_KWH_PER_LITRE) -> float:
    """
    Fuel burned to generate a given amount of electricity.

    Args:
        gen_kwh: electricity from the generator, kWh.
        kwh_per_litre: generator efficiency, kWh electric per litre (constant; no part-load curve).

    Returns:
        Diesel, litres.
    """
    return gen_kwh / kwh_per_litre


def diesel_cost(litres: float, price_per_litre: float) -> float:
    """
    Cost of fuel.

    Args:
        litres: diesel, litres.
        price_per_litre: delivered price incl. freight, USD/litre.

    Returns:
        Cost, USD.
    """
    return litres * price_per_litre
