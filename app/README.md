# SunSafe app (Streamlit)
Frontend for the SunSafe model. Lives in `app/`; imports the model only in `app/components/layout.py`
(`from sunsafe.model import run_sunsafe`, with `sunsafe.interface` types). If the model cannot be
imported or a run fails, the app shows the error (sidebar and Site Setup) and no results.

Run from the repo root: `pip install -r requirements.txt` then `streamlit run app/app.py`.
Results carry the model's warnings (placeholders still in use); the app shows them under "Model notes and assumptions".
