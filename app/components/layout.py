"""Shared UI helpers. The ONLY place the app imports the model (sunsafe.model, sunsafe.lifecycle)
and its contract (sunsafe.interface). Pages read the plan bundle built by run_plan()."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root -> `import sunsafe`

import importlib
import streamlit as st
from streamlit.errors import StreamlitAPIException
from dataclasses import asdict

from sunsafe import config
from sunsafe.interface import Inputs
from utils.formatting import battery

MODEL_IMPORT_ERROR = None
try:
    from sunsafe.model import PLACEHOLDER_WARNINGS, run_sunsafe_detailed
    from sunsafe.lifecycle import finance as fin
    from sunsafe.lifecycle import degradation as _deg      # read-only: pv_derate
    from sunsafe.energy import solar as _solar              # read-only: cached weather -> PV yield
    from sunsafe import load_profiles as _lp                # read-only: overnight share of demand
    from sunsafe.lifecycle.degradation import GrowthSchedule
except Exception as e:  # show the reason in the sidebar; the app cannot run analyses
    MODEL_IMPORT_ERROR = repr(e)
    run_sunsafe_detailed = fin = GrowthSchedule = _deg = _solar = _lp = None
    PLACEHOLDER_WARNINGS = []

# Streamlit (including Streamlit Cloud after a git push) re-runs page scripts but keeps modules
# outside app/ imported, so a model update could leave old `sunsafe` code in memory (e.g. a page
# asking an old `config` for a new setting). init() calls _refresh_model_if_changed() on every
# run: when any sunsafe/*.py file changes it reloads the package in place (so `config` objects
# held by pages see the new values), re-binds the model functions and clears cached results.
_SUNSAFE_DIR = Path(__file__).resolve().parents[2] / "sunsafe"
_RELOAD_ORDER = [  # dependencies first
    "sunsafe.config", "sunsafe.hours", "sunsafe.interface", "sunsafe.load_profiles",
    "sunsafe.energy.diesel", "sunsafe.energy.solar", "sunsafe.energy.simulate",
    "sunsafe.energy.backup", "sunsafe.energy.headroom", "sunsafe.lifecycle.degradation",
    "sunsafe.energy.sizing", "sunsafe.lifecycle.projection", "sunsafe.lifecycle.finance",
    "sunsafe.lifecycle.strategy", "sunsafe.model",
]


def _model_mtime():
    return max(p.stat().st_mtime for p in _SUNSAFE_DIR.rglob("*.py"))


_MODEL_MTIME = _model_mtime()


def _refresh_model_if_changed():
    """Reload the sunsafe package if its source changed since it was imported. Returns True if reloaded."""
    global _MODEL_MTIME, Inputs, run_sunsafe_detailed, fin, GrowthSchedule, PLACEHOLDER_WARNINGS
    global MODEL_IMPORT_ERROR
    current = _model_mtime()
    if current == _MODEL_MTIME:
        return False
    _MODEL_MTIME = current
    try:
        for name in _RELOAD_ORDER:
            if name in sys.modules:
                importlib.reload(sys.modules[name])
            else:
                importlib.import_module(name)
        Inputs = sys.modules["sunsafe.interface"].Inputs
        run_sunsafe_detailed = sys.modules["sunsafe.model"].run_sunsafe_detailed
        PLACEHOLDER_WARNINGS = sys.modules["sunsafe.model"].PLACEHOLDER_WARNINGS
        fin = sys.modules["sunsafe.lifecycle.finance"]
        GrowthSchedule = sys.modules["sunsafe.lifecycle.degradation"].GrowthSchedule
        MODEL_IMPORT_ERROR = None
    except Exception as e:  # keep the app up and say why
        MODEL_IMPORT_ERROR = repr(e)
        run_sunsafe_detailed = None
    _run_cached.clear()
    st.session_state.plan = None   # results from the old model would be stale
    return True


# ------------------------------------------------------------------ presets ---

def _preset_label(p):
    """Short dropdown label; the detail (validation site vs illustrative inputs) is in the caption."""
    return f"{p['name']} · {'illustrative' if p['illustrative'] else 'validation'}"


PRESETS = {_preset_label(p): p for p in config.SITE_PRESETS}
_FIRST = config.SITE_PRESETS[0]   # Fakaofo, Tokelau: the validation site

DEFAULTS = dict(site_name=_FIRST["name"], lat=_FIRST["lat"], lon=_FIRST["lon"],
                diesel_lpd=float(_FIRST["diesel_litres_per_day"]), price=_FIRST["diesel_price"],
                known_load=_FIRST["daily_load_kwh"] is not None,
                load_kwh=float(_FIRST["daily_load_kwh"] or 600.0), critical_kw=5.0,
                target=int(round(_FIRST["target"] * 100)), chem=_FIRST["chemistry"],
                g_fast=9.0, g_years=5, g_steady=3.0, years=15,
                plan=None, plan_key=None, model_error=None, last_click=None)


def apply_preset(p):
    """Copy a config.SITE_PRESETS entry into the form (growth and horizon are left as they are)."""
    s = st.session_state
    s.site_name, s.lat, s.lon = p["name"], float(p["lat"]), float(p["lon"])
    s.diesel_lpd, s.price = float(p["diesel_litres_per_day"]), float(p["diesel_price"])
    s.known_load = p["daily_load_kwh"] is not None
    if s.known_load:
        s.load_kwh = float(p["daily_load_kwh"])
    s.chem, s.target = p["chemistry"], int(round(p["target"] * 100))


def in_pacific(lat, lon):
    """Rough Pacific Islands box: 30S-25N, 130E eastward to 120W (across the date line)."""
    return -30.0 <= lat <= 25.0 and (lon >= 130.0 or lon <= -120.0)


def wrap_lon(lon):
    """Map longitudes as 0-360, so the Pacific is not split at the date line."""
    return lon + 360 if lon < 0 else lon


def unwrap_lon(lon):
    return lon - 360 if lon > 180 else lon


def handle_map_click(event):
    """Apply a new click on the Your island map once (the selection persists across reruns).
    A preset dot applies that preset; a grid dot sets the coordinates. Returns True if applied."""
    s = st.session_state
    sel = getattr(event, "selection", None) or {}
    objects = sel.get("objects", {}) if hasattr(sel, "get") else {}
    picked = next(((layer, objs[0]) for layer, objs in objects.items() if objs and layer != "here"), None)
    if not picked:
        return False
    layer, obj = picked
    click = (layer, round(float(obj["lat"]), 4), round(float(obj["lon"]), 4))
    if click == s.last_click:
        return False
    s.last_click = click
    if layer == "presets" and obj.get("label") in PRESETS:
        apply_preset(PRESETS[obj["label"]])
    else:
        s.lat, s.lon = float(obj["lat"]), float(unwrap_lon(float(obj["lon"])))
        s.site_name = f"Site at {s.lat:.1f}, {s.lon:.1f}"
    return True


PACIFIC_NOTE = "Defaults (freight, demand growth) are set for Pacific islands; adjust them for other sites."

# ---------------------------------------------------------------- styling ---

CSS = """<style>
.stApp{background:#faf9f6}
.block-container{padding-top:2rem;max-width:1200px}
h1{font-size:2rem!important;letter-spacing:-.01em;margin-bottom:0}
h2,h3{color:#2b2b2b}
[data-testid="stWidgetLabel"] p,label,.stMarkdown,.stCaption{color:#2b2b2b!important}
div[data-baseweb="input"],div[data-baseweb="input"] input,div[data-baseweb="select"]>div{background:#fff!important;color:#2b2b2b!important;-webkit-text-fill-color:#2b2b2b}
[data-testid="stSidebar"]{background:#f0eee8}
[data-testid="stMetric"]{background:#fff;border:1px solid #e0ddd5;border-radius:12px;padding:12px 16px}
[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border-radius:14px}
.card{border:1px solid #e0ddd5;border-radius:12px;padding:14px 18px;background:#fff;margin-bottom:8px}
.card.out{border-left:5px solid #1f6f66}.card.inp{border-left:5px solid #7b6fb0}
.card small,.tag{color:#777;letter-spacing:.08em;text-transform:uppercase;font-size:.72rem;font-weight:600}
.tag.inp{color:#7b6fb0}.tag.out{color:#1f6f66}
.card{white-space:normal;overflow-wrap:break-word;word-break:normal}
.card h2{margin:2px 0 0;color:#1f6f66;font-size:clamp(1.15rem,2.3vw,1.8rem);line-height:1.2}
.card .sub{color:#555;font-size:.9rem;margin-top:4px}
.card ul{margin:6px 0 0;padding-left:18px;color:#2b2b2b}
.notice{background:#fff4d6;border:1px solid #e6c766;border-radius:8px;padding:8px 14px;margin-bottom:12px;font-size:.88rem;color:#5a4a10}
.pills{margin:6px 0 14px}.pill{display:inline-block;padding:3px 12px;margin:0 6px 6px 0;border:1px solid #d6d2c7;border-radius:999px;font-size:.78rem;color:#777;background:#fff}
.pill.on{background:#1f6f66;color:#fff;border-color:#1f6f66}
.q{color:#555;font-size:1.02rem;margin:2px 0 14px}
#MainMenu,footer{visibility:hidden}
</style>"""

TEAL, RED, GREY, AMBER, PURPLE = "#1f6f66", "#c0504d", "#9a9a9a", "#b5651d", "#7b6fb0"
STEPS = ["1 Your island", "2 Your plan", "3 How we know it works"]
PAGE_ISLAND = "pages/1_Your_island.py"
PAGE_PLAN = "pages/2_Your_plan.py"
PAGE_CHECKS = "pages/3_How_we_know_it_works.py"


def init(title, question=None, step=None):
    st.set_page_config(page_title="SunSafe", layout="wide")
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)
    if _refresh_model_if_changed():
        st.toast("Model updated: cached results cleared. Build the plan again on Your island.")
    st.markdown(CSS, unsafe_allow_html=True)
    s = st.session_state
    plan = s.plan
    tag = ("● Model not loaded" if MODEL_IMPORT_ERROR else "● Plan ready" if plan else "● Ready")
    st.sidebar.markdown("### SUNSAFE\nPlanning Pacific island mini-grids\n\n" + tag)
    st.sidebar.caption(f"Plan for: {plan['results'].inputs.site_name}" if plan
                       else f"Current island: {s.site_name}")
    if s.model_error:
        st.sidebar.error(f"Last run failed: {s.model_error}")
    if MODEL_IMPORT_ERROR:
        st.sidebar.error(f"Model not loaded: {MODEL_IMPORT_ERROR}")
    if plan and step == 1 and s.plan_key != current_key():
        st.warning("Inputs changed since this plan was built. Go to **Your island** and click "
                   "*Build my plan* to update it.")
    if step is not None:
        st.markdown('<div class="pills">' + "".join(
            f'<span class="pill{" on" if i == step else ""}">{n}</span>' for i, n in enumerate(STEPS)) + "</div>",
            unsafe_allow_html=True)
    st.title(title)
    if question:
        st.markdown(f'<div class="q">{question}</div>', unsafe_allow_html=True)


def stretch(element, *args, **kwargs):
    """Call a Streamlit element full-width: `width="stretch"` on newer Streamlit, else the older
    `use_container_width=True` (deprecated in new versions, the only option on 1.39)."""
    try:
        return element(*args, width="stretch", **kwargs)
    except (TypeError, StreamlitAPIException):
        return element(*args, use_container_width=True, **kwargs)


def beats_diesel(breakeven, curve, diesel_curve):
    """Plain phrase for where a hybrid cost line beats diesel on the USD 1.00-3.50/L chart."""
    if breakeven is not None:
        return f"above ${breakeven:.2f}/L"
    return ("at no price up to $3.50/L" if curve[-1] > diesel_curve[-1]
            else "at every price from $1.00/L")


def card(label, value, sub=None, html_body=None):
    body = f'<div class="sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="card out"><small>{label}</small><h2>{value}</h2>{body}{html_body or ""}</div>',
                unsafe_allow_html=True)


# ------------------------------------------------------------ model calls ---

def growth_tuple():
    """(fast %/yr, fast years, steady %/yr) from the form."""
    s = st.session_state
    return (float(s.g_fast), int(s.g_years), float(s.g_steady))


def growth_label(g):
    fast, n, steady = g
    if n == 0 or fast == steady:
        return f"{steady:g}%/yr"
    return f"{fast:g}% for {n} years, then {steady:g}%"


def build_inputs():
    s = st.session_state
    fast, n, steady = growth_tuple()
    return Inputs(site_name=s.site_name, latitude=float(s.lat), longitude=float(s.lon),
                  diesel_litres_per_day=float(s.diesel_lpd), diesel_price_per_litre=float(s.price),
                  daily_load_kwh=float(s.load_kwh) if s.known_load else None,
                  critical_load_kw=float(s.critical_kw), renewable_target=s.target / 100,
                  battery_chemistry=s.chem,
                  # Inputs carries one constant rate; a schedule is passed separately (run_plan).
                  demand_growth_per_year=(steady if n == 0 else fast) / 100,
                  project_years=int(s.years))


def current_key():
    return (asdict(build_inputs()), growth_tuple())


FAMILIES = [("A", "Build big"), ("B", "Replace battery once"), ("C", "Expand once"),
            ("D", "Expand in stages")]
PRICE_GRID = [round(1.00 + 0.05 * i, 2) for i in range(51)]   # USD/L, 1.00-3.50


def _crossing(prices, a, b):
    """Diesel price where line a meets line b (both linear in price); None if outside the grid."""
    g0, g1 = a[0] - b[0], a[-1] - b[-1]
    if g0 == g1 or g0 * g1 > 0:
        return None
    return prices[0] + (prices[-1] - prices[0]) * g0 / (g0 - g1)


@st.cache_data(show_spinner=False)
def _run_cached(inputs_dict, growth):
    """One model run plus everything the plan page needs (cached on inputs + growth)."""
    fast, n, steady = growth
    g = steady / 100 if (n == 0 or fast == steady) else GrowthSchedule(fast / 100, n, steady / 100)
    inputs = Inputs(**inputs_dict)
    results, comp = run_sunsafe_detailed(inputs, growth=g)
    rec = comp.recommended

    # c. strategies: best (lowest NPV) of each family that meets the target every year
    strategies = []
    for letter, label in FAMILIES:
        fam = [c for c in comp.candidates if c.name.startswith(letter)]
        ok = [c for c in fam if c.meets_target_every_year]
        best = min(ok or fam, key=lambda c: c.npv_usd) if fam else None
        if best is not None:
            strategies.append(dict(letter=letter, label=label, name=best.name, npv=best.npv_usd,
                                   feasible=bool(ok), recommended=best is rec))
    a = next((x for x in strategies if x["letter"] == "A" and x["feasible"]), None)
    saving_vs_a = 1 - rec.npv_usd / a["npv"] if a else None

    # b./d. per-year data: the plan (with reinvestments) vs never reinvested
    usable = 1 - config.BATTERY[inputs.battery_chemistry]["min_soc"]
    years = [dict(year=y.year, share_plan=ly.share_funded_year_15, share_without=ly.share_funded_day_one,
                  usable_plan=y.battery_kwh * usable, usable_without=ly.battery_capacity_kwh,
                  demand=y.demand_kwh_per_day, pv_kw=y.pv_kw)
             for y, ly in zip(rec.years, results.lifecycle)]

    # Night coverage: usable battery / overnight demand (18:00-06:00 share of the daily profile).
    day = _lp.village_profile(1.0)[:24]
    night_share = float(day[18:].sum() + day[:6].sum()) / float(day.sum())
    # Solar output / demand: installed kWp x site yield (NASA weather, already cached) x PV derate.
    yield_kwh_per_kwp = float(_solar.pv_output_per_kw(_solar.fetch_weather(inputs.latitude, inputs.longitude)).sum())
    pv_without = results.plan_stages[0].pv_added_kw if results.plan_stages else rec.pv_kw
    for row, y in zip(years, rec.years):
        night = row["demand"] * night_share
        row["night_plan"] = 100 * row["usable_plan"] / night
        row["night_without"] = 100 * row["usable_without"] / night
        solar = yield_kwh_per_kwp * _deg.pv_derate(y.year)
        row["solar_plan"] = 100 * y.pv_kw * solar / y.load_kwh
        row["solar_without"] = 100 * pv_without * solar / y.load_kwh

    # Fund: the yearly set-aside = O&M (spent) + a deposit saved toward the first upgrade
    # (finance.sinking_fund_deposit), earning the model's discount rate. The same deposit is assumed to
    # continue after the first upgrade; later upgrades are compared with what has built up by then.
    rate = config.PROJECT_DISCOUNT_RATE
    deposit = (fin.sinking_fund_deposit(rec.replacement_usd, rec.replacement_year - 1)
               if rec.replacement_year and rec.replacement_year > 1 else 0.0)
    costs_by_year = {st_.year: st_.capex_usd for st_ in rec.stages[1:]}
    balance, fund, upgrades = 0.0, [], []
    for y in range(1, inputs.project_years + 1):
        if y in costs_by_year:                      # paid at the start of the year
            cost = costs_by_year[y]
            upgrades.append(dict(year=y, cost=cost, available=balance, shortfall=max(cost - balance, 0.0)))
            balance = max(balance - cost, 0.0)
        balance = balance * (1 + rate) + deposit    # end of year: interest + deposit
        fund.append(dict(year=y, balance=balance))

    # e. cost per kWh vs diesel price, the plan fixed (costs are linear in price: no re-sizing)
    loads = [y.load_kwh for y in rec.years]
    gens = [y.gen_kwh for y in rec.years]

    def per_kwh(price, capex):
        npv = fin.lifetime_npv_usd(capex, rec.om_by_year, gens, price, rec.replacement_year,
                                   rec.replacement_usd, extra_costs=rec.extra_investments)
        return fin.levelised_cost_per_kwh(npv, loads)

    diesel = [fin.levelised_cost_per_kwh(fin.lifetime_npv_usd(0.0, 0.0, loads, p), loads) for p in PRICE_GRID]
    full = [per_kwh(p, rec.capex_usd) for p in PRICE_GRID]
    island = [per_kwh(p, 0.0) for p in PRICE_GRID]
    price = inputs.diesel_price_per_litre
    at_price = dict(diesel=fin.levelised_cost_per_kwh(fin.lifetime_npv_usd(0.0, 0.0, loads, price), loads),
                    full=per_kwh(price, rec.capex_usd), island=per_kwh(price, 0.0))
    return dict(results=results, growth_label=growth_label(growth), rec_name=rec.name,
                rec_letter=rec.name[0], any_feasible=comp.any_feasible, strategies=strategies,
                saving_vs_a=saving_vs_a, years=years,
                upgrade_years=[st_.year for st_ in results.plan_stages[1:]],
                prices=PRICE_GRID, cost_diesel=diesel, cost_full=full, cost_island=island,
                breakeven_full=_crossing(PRICE_GRID, full, diesel),
                breakeven_island=_crossing(PRICE_GRID, island, diesel), at_price=at_price,
                usable_fraction=usable,
                night_share=night_share, fund=fund, fund_upgrades=upgrades, fund_deposit=deposit,
                om_year1=rec.annual_om_usd, discount_rate=rate)


# Tokelau validation case (scripts/run_tokelau.py inputs), run with the current engine (A-D).
VALIDATION_INPUTS = dict(site_name="Fakaofo, Tokelau (validation case)", latitude=-9.38, longitude=-171.24,
                         diesel_litres_per_day=200.0, diesel_price_per_litre=config.TOKELAU_DIESEL_PRICE_USD_PER_L,
                         daily_load_kwh=600.0, critical_load_kw=5.0, renewable_target=0.95,
                         battery_chemistry="lead_acid", demand_growth_per_year=0.09, project_years=15)
VALIDATION_GROWTH = (9.0, 0, 9.0)   # constant 9%/yr


def run_validation_case():
    """The validation inputs through the current engine; cached (same cache as any plan). None if it fails."""
    if run_sunsafe_detailed is None:
        return None
    try:
        return _run_cached(dict(VALIDATION_INPUTS), VALIDATION_GROWTH)
    except Exception as e:
        st.session_state.model_error = repr(e)
        return None


def run_plan():
    """Call the model; never crash the UI. Returns the plan bundle, or None (reason in model_error)."""
    s = st.session_state
    s.model_error = None
    if run_sunsafe_detailed is None:
        s.model_error = f"model not loaded ({MODEL_IMPORT_ERROR})"
        return None
    try:
        inputs_dict, growth = current_key()
        plan = _run_cached(inputs_dict, growth)
        s.plan_key = (inputs_dict, growth)
        return plan
    except Exception as e:
        s.model_error = repr(e)
        return None


def require_plan():
    plan = st.session_state.plan
    if plan is None:
        st.info("No plan yet: go to **Your island** and click *Build my plan*.")
        st.page_link(PAGE_ISLAND, label="Go to Your island", icon="➡️")
        st.stop()
    return plan


def placeholder_notes():
    return list(PLACEHOLDER_WARNINGS)


def usable_fraction(plan):
    """Usable share of nominal battery kWh (1 - minimum state of charge) for this plan's chemistry."""
    return plan.get("usable_fraction",
                    1 - config.BATTERY[plan["results"].inputs.battery_chemistry]["min_soc"])


def describe_stage(stage, chemistry, usable):
    """One plain line for a later PlanStage; battery shown nominal and usable."""
    chem = chemistry.replace("_", "-")
    batt = battery(stage.battery_installed_kwh, usable)
    if stage.pv_added_kw > 0.5:
        what = f"add {stage.pv_added_kw:,.0f} kWp solar + new {chem} battery, {batt}"
    else:
        what = f"replace the {chem} battery, {batt}"
    return f"Year {stage.year}: {what} (about ${stage.capex_usd / 1e6:,.2f}M)"
