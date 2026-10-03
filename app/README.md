# SunSafe app (Streamlit)
Planning tool for Pacific island mini-grids. Lives in `app/`; imports the model only in
`app/components/layout.py` (`run_sunsafe_detailed`, plus `sunsafe.lifecycle.finance` for the cost-vs-price
curve). If the model cannot be imported or a run fails, the app shows the error and no results.

Run from the repo root: `pip install -r requirements.txt` then `streamlit run app/app.py`.

Pages:
1. **Your island:** click the map (1° grid over the Pacific, or a preset dot) or type lat/lon; presets come
   from `config.SITE_PRESETS`. Main inputs, demand growth (default 9% for 5 years, then 3%), and an
   Advanced expander. "Build my plan" runs the model once (cached) and opens the plan.
2. **Your plan:** decision cards (build now, upgrades from `Results.plan_stages`, set aside per year), then
   charts, each captioned with the decision it supports: renewable share by year, strategy NPVs, battery vs
   demand, cost per kWh vs diesel price (incl. island-paid cost), fuel-shock replay and backup hours, exports.
3. **How we know it works:** Tokelau validation, `docs/sensitivity.md` findings, sources, placeholders.

Charts use Altair and the map uses pydeck (both ship with Streamlit). `layout.stretch()` handles the
full-width argument on old (1.39) and new Streamlit.
