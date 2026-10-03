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
   charts from `components/charts.py`: investment timeline, renewable share by year (plan vs without
   reinvestment), battery night cover vs overnight demand, fund balance vs upgrade costs beside cost per kWh
   (diesel / full hybrid / island-paid), fuel shock; strategy NPVs and the diesel-price breakeven sit in
   "Alternatives we considered". Each chart title states the finding with numbers from the run.
3. **How we know it works:** Tokelau validation, `docs/sensitivity.md` findings, sources, placeholders.

The funding proposal export is one HTML file with the same charts (vega-embed from the jsDelivr CDN, so it
needs internet to display; print to PDF from a browser). Chart conventions: year axes 1..project years, line
names at the line ends (no legends), plan green / without reinvestment grey / diesel amber.

Charts use Altair and the map uses pydeck (both ship with Streamlit). `layout.stretch()` handles the
full-width argument on old (1.39) and new Streamlit.
