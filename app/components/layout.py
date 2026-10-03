"""Shared UI helpers. The ONLY place the app touches the model contract (sunsafe.interface)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root -> `import sunsafe`

import streamlit as st
from sunsafe.interface import Inputs, run_sunsafe_fake

MODEL_IMPORT_ERROR = None
try:
    from sunsafe.model import run_sunsafe
except Exception as e:  # show the reason instead of silently using the fake model
    MODEL_IMPORT_ERROR = repr(e)
    from sunsafe.interface import run_sunsafe

DEFAULTS = dict(site_name="Fakaofo (test)", lat=-9.38, lon=-171.24, diesel_lpd=200.0, price=1.10,
                known_load=False, load_kwh=600.0, critical_kw=5.0, target=90, chem="lithium",
                growth=3.0, years=15, results=None)
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
.out{border-left:5px solid #1f6f66}.inp{border-left:5px solid #7b6fb0}
.card small,.tag{color:#777;letter-spacing:.08em;text-transform:uppercase;font-size:.72rem;font-weight:600}
.tag.inp{color:#7b6fb0}.tag.out{color:#1f6f66}
.card h2{margin:2px 0 0;color:#1f6f66;font-size:1.8rem}
.demo{background:#fff4d6;border:1px solid #e6c766;border-radius:8px;padding:8px 14px;margin-bottom:12px;font-size:.88rem;color:#5a4a10}
.pills{margin:6px 0 14px}.pill{display:inline-block;padding:3px 12px;margin:0 6px 6px 0;border:1px solid #d6d2c7;border-radius:999px;font-size:.78rem;color:#777;background:#fff}
.pill.on{background:#1f6f66;color:#fff;border-color:#1f6f66}
.q{color:#555;font-size:1.02rem;margin:2px 0 14px}
#MainMenu,footer{visibility:hidden}
</style>"""


STEPS = ["1 Setup", "2 System", "3 Lifecycle", "4 Financials", "5 Electrification", "6 Funding case"]


def init(title, question=None, step=None):
    st.set_page_config(page_title="SunSafe", layout="wide")
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)
    st.markdown(CSS, unsafe_allow_html=True)
    s = st.session_state
    r = s.results
    fake = r is not None and any("FAKE" in w for w in r.warnings)
    placeholders = r is not None and not fake and any("PLACEHOLDER" in w for w in r.warnings)
    tag = ("● **DEMO MODE**" if fake else "● Model connected (placeholder inputs)" if placeholders
           else "● Model connected" if r else "● Ready")
    st.sidebar.markdown("### SUNSAFE\n" + tag)
    st.sidebar.caption(f"Current site: {s.site_name}")
    if MODEL_IMPORT_ERROR:
        st.sidebar.error(f"Real model not loaded: {MODEL_IMPORT_ERROR}")
    if fake:
        st.markdown('<div class="demo">DEMO MODE — Illustrative data. Real model outputs are not connected yet.</div>',
                    unsafe_allow_html=True)
    elif placeholders:
        st.markdown('<div class="demo">Real model connected. Some assumptions (costs, battery fade, load shape, '
                    'fuel path) are still placeholders. See "Model notes and assumptions".</div>',
                    unsafe_allow_html=True)
    if step is not None:
        st.markdown('<div class="pills">' + "".join(
            f'<span class="pill{" on" if i == step else ""}">{n}</span>' for i, n in enumerate(STEPS)) + "</div>",
            unsafe_allow_html=True)
    st.title(title)
    if question:
        st.markdown(f'<div class="q">{question}</div>', unsafe_allow_html=True)


def card(label, value):
    st.markdown(f'<div class="card out"><small>{label}</small><h2>{value}</h2></div>', unsafe_allow_html=True)


def build_inputs():
    s = st.session_state
    return Inputs(site_name=s.site_name, latitude=s.lat, longitude=s.lon,
                  diesel_litres_per_day=s.diesel_lpd, diesel_price_per_litre=s.price,
                  daily_load_kwh=s.load_kwh if s.known_load else None,
                  critical_load_kw=s.critical_kw, renewable_target=s.target / 100,
                  battery_chemistry=s.chem, demand_growth_per_year=s.growth / 100,
                  project_years=int(s.years))


def run_analysis():
    """Call the model; never crash the UI. Falls back to the fake model on any error."""
    inputs = build_inputs()
    try:
        return run_sunsafe(inputs)
    except Exception:
        res = run_sunsafe_fake(inputs)
        res.warnings.append("FAKE DATA: the model raised an error, showing the fake model instead.")
        return res


def require_results():
    r = st.session_state.results
    if r is None:
        st.info("Run the analysis first: go to **Site Setup** and click *Run SunSafe Analysis*.")
        st.stop()
    notes = [w for w in r.warnings if "FAKE" not in w]
    if notes:
        with st.expander(f"Model notes and assumptions ({len(notes)})"):
            for w in notes:
                st.markdown(f"- {w}")
    return r
