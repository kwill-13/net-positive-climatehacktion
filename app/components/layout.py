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
                plan=None, plan_key=None, model_error=None, map_last_click=None, map_last_obj=None,
                just_built=False)


def set_coords(lat, lon):
    """Set the site coordinates and the two coordinate inputs (keyed widgets) together."""
    s = st.session_state
    s.lat, s.lon = float(lat), float(lon)
    s.lat_in, s.lon_in = s.lat, s.lon


def apply_preset(p):
    """Copy a config.SITE_PRESETS entry into the form (growth and horizon are left as they are)."""
    s = st.session_state
    s.site_name = p["name"]
    set_coords(p["lat"], p["lon"])
    s.diesel_lpd, s.price = float(p["diesel_litres_per_day"]), float(p["diesel_price"])
    s.known_load = p["daily_load_kwh"] is not None
    if s.known_load:
        s.load_kwh = float(p["daily_load_kwh"])
    s.chem, s.target = p["chemistry"], int(round(p["target"] * 100))


def in_pacific(lat, lon):
    """Rough Pacific Islands box: 30S-25N, 130E eastward to 120W (across the date line)."""
    return -30.0 <= lat <= 25.0 and (lon >= 130.0 or lon <= -120.0)


def norm_lon(lon):
    """Longitude in -180..180 (map clicks on a repeated world copy come back outside that range)."""
    return ((float(lon) + 180.0) % 360.0) - 180.0


def fmt_coords(lat, lon):
    """'9.3800°S, 171.2400°W'."""
    return f"{abs(lat):.4f}°{'S' if lat < 0 else 'N'}, {abs(lon):.4f}°{'W' if lon < 0 else 'E'}"


PACIFIC_CENTRE = (-8.0, -175.0)    # lat, lon: map opens over the central Pacific


def island_map():
    """Folium map: light basemap over the Pacific, preset sites as clickable markers, world copies on so the
    map works across the date line. Markers are drawn on the world copies either side as well."""
    import folium
    # Esri light grey canvas: free, no API key (CARTO's basemaps now ask for one)
    m = folium.Map(location=PACIFIC_CENTRE, zoom_start=3, world_copy_jump=True, prefer_canvas=True,
                   tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
                   attr="Tiles &copy; Esri, HERE, Garmin, &copy; OpenStreetMap contributors", max_zoom=16)
    for label, p in PRESETS.items():
        for shift in (-360, 0, 360):
            folium.CircleMarker(location=(p["lat"], p["lon"] + shift), radius=7, weight=2, color="#5b4ea0",
                                fill=True, fill_color="#7b6fb0", fill_opacity=0.9, bubbling_mouse_events=False,
                                tooltip=f"{p['name']} · click to load").add_to(m)
    return m


def selected_marker():
    """The selected point, as a feature group st_folium can update without reloading the map."""
    import folium
    s = st.session_state
    fg = folium.FeatureGroup(name="selected")
    for shift in (-360, 0, 360):
        folium.Marker(location=(float(s.lat), float(s.lon) + shift), tooltip="Selected",
                      icon=folium.Icon(color="green", icon="map-marker", prefix="fa")).add_to(fg)
    return fg


def _preset_at(lat, lon):
    """The preset whose marker was clicked (markers sit on exact preset coordinates)."""
    for label, p in PRESETS.items():
        if abs(p["lat"] - lat) < 1e-4 and abs(norm_lon(p["lon"]) - norm_lon(lon)) < 1e-4:
            return label
    return None


def handle_map_result(result):
    """Apply a new click from st_folium once (its last click persists across reruns): a preset marker loads
    that preset; anywhere else sets the coordinates (4 decimals). Only the form changes; the model does not
    run. Returns True if something changed."""
    s = st.session_state
    if not result:
        return False
    obj, clk = result.get("last_object_clicked"), result.get("last_clicked")
    if obj and obj != s.get("map_last_obj"):
        s.map_last_obj = obj
        s.map_last_click = clk      # a marker click is not also a map click
        label = _preset_at(float(obj["lat"]), float(obj["lng"]))
        if label:
            s["_preset_next"] = label      # the dropdown takes it on the rerun, before it is drawn
            apply_preset(PRESETS[label])
            return True
    if clk and clk != s.get("map_last_click"):
        s.map_last_click = clk
        lat, lon = round(float(clk["lat"]), 4), round(norm_lon(clk["lng"]), 4)
        if _preset_at(lat, lon) is None:
            set_coords(lat, lon)
            s.site_name = f"Site at {lat:.1f}, {lon:.1f}"
            return True
    return False


PACIFIC_NOTE = "Defaults (freight, demand growth) are set for Pacific islands; adjust them for other sites."

# ---------------------------------------------------------------- styling ---

GREEN = "#2e7d32"   # the plan green (charts and theme)
CSS = """<style>
:root{--g:#2e7d32;--g-soft:#e8f2e9;--ink:#2b2b2b;--muted:#6b6b6b;--line:#e3e0d8;--card:#fff}
.block-container{padding-top:1.25rem;padding-bottom:3rem;max-width:1180px}
h1{font-size:1.9rem!important;font-weight:700!important;letter-spacing:-.01em;margin:.2rem 0 .1rem!important;padding:0!important}
h3{font-size:1.15rem!important;margin:.6rem 0 .2rem!important}
#MainMenu,footer,[data-testid="stDecoration"]{display:none!important}
[data-testid="stSidebar"]{background:#f3f1ec}
[data-testid="stCaptionContainer"],.stCaption{color:var(--muted)!important}
[data-testid="stVerticalBlockBorderWrapper"]{background:var(--card);border-radius:14px}
div[data-baseweb="input"],div[data-baseweb="input"] input,div[data-baseweb="select"]>div{background:#fff!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink)}
.ss-header{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px 16px;padding:2px 0 12px;margin-bottom:10px;border-bottom:1px solid var(--line)}
.ss-brand{display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 10px}
.ss-brand b{font-size:1.2rem;color:var(--g);letter-spacing:-.01em}.ss-brand span{color:var(--muted);font-size:.86rem}
.ss-steps{display:flex;flex-wrap:wrap;gap:6px}
.ss-step{display:inline-flex;align-items:center;gap:7px;padding:4px 12px 4px 5px;border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--muted);font-size:.8rem;white-space:nowrap}
.ss-step i{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:#efede7;color:#777;font-style:normal;font-size:.72rem;font-weight:700}
.ss-step.on{border-color:var(--g);color:var(--ink);font-weight:600}.ss-step.on i{background:var(--g);color:#fff}
.ss-step.done i{background:var(--g-soft);color:var(--g)}
.q{color:var(--muted);font-size:1.02rem;margin:0 0 16px}
.ss-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr));gap:12px;margin:4px 0 14px}
.card{border:1px solid var(--line);border-radius:14px;padding:16px 18px;background:#fff;margin-bottom:8px;box-sizing:border-box;white-space:normal;overflow-wrap:break-word;word-break:normal}
.ss-grid .card{margin:0;height:100%}
.card.out{border-top:4px solid var(--g)}.card.inp{border-top:4px solid #7b6fb0}
.card small,.tag{color:var(--muted);letter-spacing:.08em;text-transform:uppercase;font-size:.72rem;font-weight:600}
.tag.inp{color:#7b6fb0}.tag.out{color:var(--g)}
.card h2{margin:6px 0 2px;color:var(--g);font-size:clamp(1.15rem,2.2vw,1.65rem);line-height:1.2;font-weight:700;padding:0}
.card .sub{color:var(--muted);font-size:.9rem;margin-top:6px}
.card ul{margin:8px 0 0;padding-left:18px;color:var(--ink);font-size:.92rem}
.ss-summary{border:1px solid var(--line);border-radius:14px;background:#fff;padding:12px 16px;margin:4px 0 12px}
.ss-summary b{font-size:1.02rem;margin-right:8px}
.pill{display:inline-block;padding:3px 11px;margin:6px 6px 0 0;border:1px solid var(--line);border-radius:999px;font-size:.8rem;color:#555;background:#faf9f6}
.notice{background:#fff7e0;border:1px solid #ecd48a;border-radius:10px;padding:8px 14px;margin:6px 0 12px;font-size:.88rem;color:#5a4a10}
.ss-coords{color:var(--muted);font-size:.88rem;margin:6px 2px 0}.ss-coords b{color:var(--ink)}
.ss-table{width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed;font-size:.9rem;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#fff}
.ss-table th{background:#f6f4ef;color:var(--muted);font-weight:600;text-align:left;font-size:.8rem;padding:8px 10px;border-bottom:1px solid var(--line)}
.ss-table td{padding:8px 10px;vertical-align:top;border-bottom:1px solid #efece5;overflow-wrap:break-word}
.ss-table tr:last-child td{border-bottom:none}.ss-table td:first-child{font-weight:600}
@media (max-width:1000px){.ss-table colgroup,.ss-table thead{display:none}
.ss-table,.ss-table tbody,.ss-table tr,.ss-table td{display:block;width:100%;box-sizing:border-box}
.ss-table tr{padding:6px 0;border-bottom:1px solid var(--line)}.ss-table tr:last-child{border-bottom:none}
.ss-table td{border:none;padding:3px 12px}
.ss-table td[data-label]:not(:first-child)::before{content:attr(data-label);display:block;color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;margin-top:4px}}
.stMarkdown table:not(.ss-table){border-collapse:collapse;font-size:.88rem;width:100%}
.stMarkdown table:not(.ss-table) th{background:#f6f4ef;color:var(--muted);font-weight:600}
.stMarkdown table:not(.ss-table) th,.stMarkdown table:not(.ss-table) td{border:1px solid #ebe8e1!important;padding:6px 10px!important}
.ss-hero{padding:18px 0 6px}.ss-hero h3{font-size:1.35rem!important;font-weight:600!important;margin:0 0 8px!important}
.ss-hero p{color:var(--muted);font-size:1.02rem;max-width:760px}
</style>"""

TEAL, RED, GREY, AMBER, PURPLE = "#1f6f66", "#c0504d", "#9a9a9a", "#b5651d", "#7b6fb0"
STEPS = ["Your island", "Your plan", "How we know it works"]
PAGE_HOME = "views/home.py"
PAGE_ISLAND = "views/island.py"
PAGE_PLAN = "views/plan.py"
PAGE_CHECKS = "views/checks.py"


def pages():
    """st.navigation pages; url paths keep the earlier links working."""
    return [st.Page(PAGE_HOME, title="Home", icon=":material/home:", default=True),
            st.Page(PAGE_ISLAND, title="1 Your island", icon=":material/location_on:", url_path="Your_island"),
            st.Page(PAGE_PLAN, title="2 Your plan", icon=":material/insights:", url_path="Your_plan"),
            st.Page(PAGE_CHECKS, title="3 How we know it works", icon=":material/verified:",
                    url_path="How_we_know_it_works")]


def _header(step):
    s = st.session_state
    done = lambda i: i < (step if step is not None else 0) or (i == 0 and s.plan is not None)
    steps = "".join(
        f'<span class="ss-step{" on" if i == step else " done" if done(i) else ""}">'
        f'<i>{"&#10003;" if done(i) and i != step else i + 1}</i>{n}</span>' for i, n in enumerate(STEPS))
    st.markdown(f'<div class="ss-header"><div class="ss-brand"><b>SunSafe</b><span>Planning Pacific island '
                f'mini-grids</span></div><div class="ss-steps">{steps}</div></div>', unsafe_allow_html=True)


def init(title, question=None, step=None):
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)
    if _refresh_model_if_changed():
        st.toast("Model updated: cached results cleared. Build the plan again on Your island.")
    st.markdown(CSS, unsafe_allow_html=True)
    s = st.session_state
    plan = s.plan
    tag = ("● Model not loaded" if MODEL_IMPORT_ERROR else "● Plan ready" if plan else "● Ready")
    st.sidebar.markdown(tag)
    st.sidebar.caption(f"Plan for: {plan['results'].inputs.site_name}" if plan
                       else f"Current island: {s.site_name}")
    if s.model_error:
        st.sidebar.error(f"Last run failed: {s.model_error}")
    if MODEL_IMPORT_ERROR:
        st.sidebar.error(f"Model not loaded: {MODEL_IMPORT_ERROR}")
    _header(step)
    if plan and step == 1 and s.plan_key != current_key():
        st.warning("Inputs changed since this plan was built. Go to **Your island** and click "
                   "*Build my plan* to update it.")
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


def card_html(label, value, sub=None, html_body=None):
    body = f'<div class="sub">{sub}</div>' if sub else ""
    return f'<div class="card out"><small>{label}</small><h2>{value}</h2>{body}{html_body or ""}</div>'


def card(label, value, sub=None, html_body=None):
    st.markdown(card_html(label, value, sub, html_body), unsafe_allow_html=True)


def card_grid(cards):
    """Cards in an equal-height grid that wraps to one column in a narrow window."""
    st.markdown('<div class="ss-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)


def summary(title_html, pills):
    st.markdown(f'<div class="ss-summary"><b>{title_html}</b> ' +
                " ".join(f'<span class="pill">{p}</span>' for p in pills) + "</div>", unsafe_allow_html=True)


def html_table(columns, widths=None):
    """A wrapping table (no index, fixed column widths) from {header: [cells]}."""
    import html as _h
    heads = list(columns)
    widths = widths or [100 / len(heads)] * len(heads)
    rows = zip(*columns.values())
    cols = "".join(f'<col style="width:{w}%">' for w in widths)
    head = "".join(f"<th>{_h.escape(h)}</th>" for h in heads)
    body = "".join("<tr>" + "".join(f'<td data-label="{_h.escape(h)}">{_h.escape(str(c))}</td>'
                                    for h, c in zip(heads, r)) + "</tr>" for r in rows)   # labels: narrow layout
    st.markdown(f'<table class="ss-table"><colgroup>{cols}</colgroup><thead><tr>{head}</tr></thead>'
                f"<tbody>{body}</tbody></table>", unsafe_allow_html=True)


def download(col, label, data, file_name, mime=None, primary=False):
    """Full-width download button with a download icon (icon and type need newer Streamlit; dropped if absent)."""
    kw = dict(mime=mime) if mime else {}
    for extra in (dict(type="primary" if primary else "secondary", icon=":material/download:"),
                  dict(type="primary" if primary else "secondary"), {}):
        try:
            return stretch(col.download_button, label, data, file_name, **kw, **extra)
        except TypeError:
            continue


def go_button(label, page, key, primary=False):
    """A button that opens another page (instead of an arrow link)."""
    if stretch(st.button, label, key=key, type="primary" if primary else "secondary"):
        st.switch_page(page)


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
        with st.container(border=True):
            st.markdown("No plan yet: go to **Your island** and click *Build my plan*.")
            go_button("Go to Your island", PAGE_ISLAND, key="empty_go", primary=True)
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
