# net-positive-climatehacktion

**SunSafe** helps Pacific island energy officers plan diesel-to-solar mini-grids that still
work in their final year (10-25 year projects), and turns the plan into a funding case: what to build
now, when to upgrade, what it costs and who pays. Built for Climate Hack-tion (COP31 electrification track).

## Getting started

Needs Python 3.11 (3.10 and 3.12 also work) and internet access for the first run.

```bash
git clone https://github.com/kwill-13/net-positive-climatehacktion.git
cd net-positive-climatehacktion
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

pytest                             # 70 tests, ~45 s, runs offline
python scripts/run_tokelau.py      # validation against the real Tokelau systems, ~45 s
python -m sunsafe.model            # one demo site through the real run_sunsafe(), ~10 s
streamlit run app/app.py           # the app (Streamlit 1.45+), opens in the browser
```

Other scripts: `python scripts/run_sensitivity.py` (growth, O&M and who-pays tables in
`docs/sensitivity.md`, ~50 s) and `python scripts/run_pacific_presets.py` (strategy table for the
Pacific presets at 15/20/25 years, ~3-4 min).

The first run of `run_tokelau.py` (or `sunsafe.model`) downloads one year of hourly solar
and temperature data from [NASA POWER](https://power.larc.nasa.gov/). No API key is needed.
Responses are cached in `data/cache/` (gitignored), so later runs work offline. If the
download fails, the model falls back to a synthetic tropical profile and says so in its
output.

See [HANDOFF.md](HANDOFF.md) for how to call the model from your part, and
[SOURCES.md](SOURCES.md) for every reference figure and its source.

## Repo map

| Path | What it does | Owner |
|---|---|---|
| `sunsafe/interface.py` | Contract between model and app: `Inputs`, `Results` (data definitions only) | shared (change only by agreement) |
| `sunsafe_interface.py` | Root shim: re-exports `sunsafe/interface.py` and `sunsafe.model.run_sunsafe` | shared |
| `sunsafe/config.py` | Every assumption: costs, efficiencies, battery params, fade, search bounds, site presets | energy model (William) |
| `sunsafe/energy/solar.py` | NASA POWER fetch + cache, PV output per kWp | energy model (William) |
| `sunsafe/energy/simulate.py` | Hourly solar/battery/diesel dispatch, `SimResult` | energy model (William) |
| `sunsafe/energy/sizing.py` | Cheapest PV + battery meeting a renewable target | energy model (William) |
| `sunsafe/energy/diesel.py` | Litres and cost from generator kWh | energy model (William) |
| `sunsafe/energy/backup.py` | Hours a full battery carries the critical load | energy model (William) |
| `sunsafe/energy/headroom.py` | Surplus solar by month, new loads that fit, electricity share | energy model (William) |
| `sunsafe/hours.py` | Month index for 8760-hour arrays | energy model (William) |
| `sunsafe/model.py` | Real `run_sunsafe()`: every Results field from the model | William |
| `sunsafe/lifecycle/degradation.py` | Battery fade, PV derate, demand growth by year (constant or a schedule) | lifecycle/finance (William) |
| `sunsafe/lifecycle/projection.py` | `run_years()`: a design run forward year by year | lifecycle/finance (William) |
| `sunsafe/lifecycle/strategy.py` | Strategies A build big, B battery replacement, C staged expansion, D rolling plan; recommendation | lifecycle/finance (William) |
| `sunsafe/lifecycle/finance.py` | O&M, replacement, NPV, levelised cost, payback, fuel shock | lifecycle/finance (William) |
| `sunsafe/load_profiles.py` | Placeholder village load profile | data/validation teammate (to replace) |
| `scripts/run_tokelau.py` | Validation + sensitivity against the Tokelau 2012 install and 2020 upgrade; output in `tokelau_output.txt` | data/validation teammate |
| `scripts/run_sensitivity.py`, `docs/sensitivity.md` | Growth, O&M and island-paid cost sensitivity (Fakaofo, 15 years) | William |
| `scripts/run_pacific_presets.py` | Recommended strategy for the Pacific presets at 15/20/25 years | William |
| `app/app.py`, `app/views/` | Streamlit app: navigation and the four pages (Home, Your island, Your plan, How we know it works) | app teammate |
| `app/components/` | `layout.py` (the only model import: cached run, presets, map, shared UI), `charts.py` (Altair charts) | app teammate |
| `app/exports/proposal.py` | Funding proposal (HTML with charts) and community one-pager | app teammate |
| `tests/` | pytest suite (offline, synthetic weather) | everyone |
