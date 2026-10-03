# SunSafe app (Streamlit)
Frontend for the SunSafe model. Lives in `app/`; reads only `sunsafe/interface.py` (`Inputs`, `Results`, `run_sunsafe`).
Run from the repo root: `pip install streamlit pandas` then `streamlit run app/app.py`.
The model team swaps `run_sunsafe` in `sunsafe/interface.py`; the app needs no changes if field names stay the same.
Only `app/components/layout.py` imports the model. Results containing a warning with "FAKE" show the DEMO banner.
