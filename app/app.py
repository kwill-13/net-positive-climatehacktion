"""SunSafe app entry point: page config and navigation. Run from the repo root: streamlit run app/app.py"""
import streamlit as st

st.set_page_config(page_title="SunSafe", page_icon="☀️", layout="wide")

from components.layout import pages  # noqa: E402  (after set_page_config)

st.navigation(pages()).run()
