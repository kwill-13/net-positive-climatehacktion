# SunSafe app (Streamlit)
Planning tool for Pacific island mini-grids. Lives in `app/`; imports the model only in
`app/components/layout.py` (`run_sunsafe_detailed`, plus `sunsafe.lifecycle.finance` for the cost-vs-price
curve). If the model cannot be imported or a run fails, the app shows the error and no results.

Run from the repo root: `pip install -r requirements.txt` then `streamlit run app/app.py` (Streamlit 1.45+).

Structure:
- `app.py`: page config and `st.navigation` (Home, 1 Your island, 2 Your plan, 3 How we know it works).
- `views/`: the four pages. `components/layout.py`: model call, presets, map, shared UI (header and stepper,
  cards, tables, one CSS block). `components/charts.py`: the Altair charts and their shared theme.
  `exports/proposal.py`: funding proposal (HTML with the same charts) and community one-pager.

Pages:
1. **Your island:** click map (folium via streamlit-folium; exact coordinates, preset markers load a preset,
   works across the date line), presets from `config.SITE_PRESETS`, inputs in cards, "Build my plan".
2. **Your plan:** summary, decision cards, each chart in its own card with its caption, exports card;
   strategy NPVs and the diesel-price breakeven sit in "Alternatives we considered".
3. **How we know it works:** Tokelau validation (live, cached), `docs/sensitivity.md` findings, sources,
   placeholders.

Theme: `.streamlit/config.toml` (plan green #2e7d32, minimal toolbar). Chart conventions: year axes 1..project
years, line names at the line ends, plan green / never upgraded grey / diesel amber.
