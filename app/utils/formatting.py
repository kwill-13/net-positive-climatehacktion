CO2_KG_PER_LITRE_DIESEL = 2.68  # standard combustion factor; app-side conversion only
MONTHS = ["01 Jan", "02 Feb", "03 Mar", "04 Apr", "05 May", "06 Jun",
          "07 Jul", "08 Aug", "09 Sep", "10 Oct", "11 Nov", "12 Dec"]

def money(x): return f"${x:,.0f}"
def years(x): return "Never (savings don't cover O&M)" if x == float("inf") else f"{x:.1f} years"
def pct(x): return f"{x * 100:.0f}%"
def tco2(litres): return litres * CO2_KG_PER_LITRE_DIESEL / 1000


def battery(kwh, usable_fraction):
    """Battery size, nominal and usable: '1,717 kWh (859 kWh usable)'."""
    return f"{kwh:,.0f} kWh ({kwh * usable_fraction:,.0f} kWh usable)"


def short_strategy(name):
    """Model strategy name without its size detail: 'C: expand in year 9 (+94 kWp, ...)' -> 'C: expand in year 9'."""
    return name.split(" (")[0]
