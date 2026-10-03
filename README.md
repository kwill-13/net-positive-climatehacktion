# net-positive-climatehacktion

**SunSafe** helps Pacific island energy officers plan diesel-to-solar mini-grids that still
work in year 15, and turns the plan into a funding case. Built for Climate Hack-tion
(COP31 electrification track).

## Getting started

Needs Python 3.11 (3.10 and 3.12 also work) and internet access for the first run.

```bash
git clone https://github.com/kwill-13/net-positive-climatehacktion.git
cd net-positive-climatehacktion
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

pytest                             # ~35 tests, ~10 s, runs offline
python scripts/run_tokelau.py      # validation against the real Tokelau system, ~15 s
python -m sunsafe.model            # one demo site through the real run_sunsafe()
```

The first run of `run_tokelau.py` (or `sunsafe.model`) downloads one year of hourly solar
and temperature data from [NASA POWER](https://power.larc.nasa.gov/). No API key is needed.
Responses are cached in `data/cache/` (gitignored), so later runs work offline. If the
download fails, the model falls back to a synthetic tropical profile and says so in its
output.

See [HANDOFF.md](HANDOFF.md) for how to call the model from your part.

## Repo map

| Path | What it does | Owner |
|---|---|---|
| `sunsafe/interface.py` | Contract between model and app: `Inputs`, `Results`, `run_sunsafe_fake` | shared (change only by agreement) |
| `sunsafe_interface.py` | Root shim that re-exports `sunsafe/interface.py` | shared |
| `sunsafe/config.py` | Every assumption: costs, efficiencies, battery params, fade, search bounds | energy model (William) |
| `sunsafe/energy/solar.py` | NASA POWER fetch + cache, PV output per kWp | energy model (William) |
| `sunsafe/energy/simulate.py` | Hourly solar/battery/diesel dispatch, `SimResult` | energy model (William) |
| `sunsafe/energy/sizing.py` | Cheapest PV + battery meeting a renewable target | energy model (William) |
| `sunsafe/energy/diesel.py` | Litres and cost from generator kWh | energy model (William) |
| `sunsafe/energy/backup.py` | Hours a full battery carries the critical load | energy model (William) |
| `sunsafe/model.py` | Real `run_sunsafe()`: energy parts real, others still fake | energy model (William) |
| `sunsafe/lifecycle/degradation.py` | Battery fade, PV derate, demand growth by year | lifecycle/finance (William) |
| `sunsafe/load_profiles.py` | Placeholder village load profile | data/validation teammate (to replace) |
| `scripts/run_tokelau.py` | Validation + sensitivity against Tokelau 2012 install | data/validation teammate |
| app (Streamlit) | User interface, calls `run_sunsafe` | app teammate |
| `tests/` | pytest suite (offline, synthetic weather) | everyone |
