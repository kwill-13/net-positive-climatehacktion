import pytest

from sunsafe.lifecycle import finance as fin


def test_recommended_meets_target_every_year(lead_acid_run):
    inputs, _, comp = lead_acid_run
    assert comp.any_feasible
    rec = comp.recommended
    assert all(y.renewable_share >= inputs.renewable_target - 1e-9 for y in rec.years)
    feasible = [c for c in comp.candidates if c.meets_target_every_year]
    assert rec.npv_usd == min(c.npv_usd for c in feasible)


def test_every_candidate_checked_with_its_reinvestments(lead_acid_run):
    _, _, comp = lead_acid_run
    for c in comp.candidates:
        assert c.stages and c.stages[0].year == 1
        for st in c.stages[1:]:                       # replacement, upgrade, or rolling stage
            y = c.years[st.year - 1]
            assert y.battery_year == 1 and y.battery_kwh == pytest.approx(st.battery_installed_kwh)


def test_sinking_fund_covers_replacement_by_replacement_year(lead_acid_run):
    _, _, comp = lead_acid_run
    with_repl = [c for c in comp.candidates if c.replacement_year]
    assert with_repl
    rate = fin.config.PROJECT_DISCOUNT_RATE
    for c in with_repl:
        n = c.replacement_year - 1                 # deposits at end of years 1..n
        deposit = fin.sinking_fund_deposit(c.replacement_usd, n)
        balance = sum(deposit * (1 + rate) ** (n - k) for k in range(1, n + 1))
        assert balance >= c.replacement_usd - 1e-6


def test_om_fund_includes_sinking_fund(lead_acid_run):
    _, real, comp = lead_acid_run
    rec = comp.recommended
    expected = rec.annual_om_usd
    if rec.replacement_year:
        expected += fin.sinking_fund_deposit(rec.replacement_usd, rec.replacement_year - 1)
    assert real.finance.om_fund_per_year_usd == round(expected)


def test_replacement_price_declines():
    assert fin.replacement_cost_usd(100, "lithium", 1) == pytest.approx(100 * 600)
    assert fin.replacement_cost_usd(100, "lithium", 11) == pytest.approx(100 * 600 * 0.96 ** 10)


def test_npv_and_levelised_cost_simple_case():
    # capex 100, no O&M, 3 kWh/yr from the generator (1 litre at $1 + 3 x gen O&M), 2 years, 8%
    yearly = 1.0 + 3 * fin.config.GEN_OM_USD_PER_KWH
    npv = fin.lifetime_npv_usd(100, 0, [3, 3], 1.0)
    assert npv == pytest.approx(100 + yearly / 1.08 + yearly / 1.08 ** 2)
    assert fin.lifetime_npv_usd(100, 0, [3, 3], 1.0, rate=0.06) == pytest.approx(
        100 + yearly / 1.06 + yearly / 1.06 ** 2)
    assert fin.levelised_cost_per_kwh(npv, [10, 10]) == pytest.approx(
        npv / (10 / 1.08 + 10 / 1.08 ** 2))


def test_payback():
    assert fin.simple_payback_years(1000, 300, 100) == pytest.approx(5)
    assert fin.simple_payback_years(1000, 100, 100) == float("inf")


def test_economics_fixed_design():
    e = fin.economics(capex_usd=1000, annual_om=10, load_kwh_by_year=[300, 300],
                      gen_kwh_by_year=[30, 30], diesel_price=2.0)
    per_kwh_gen = 2.0 / fin.config.DIESEL_KWH_PER_LITRE + fin.config.GEN_OM_USD_PER_KWH
    assert e.annual_saving_year1_usd == pytest.approx(270 * per_kwh_gen)
    assert e.payback_years == pytest.approx(1000 / (270 * per_kwh_gen - 10))
    assert e.cost_per_kwh_diesel_usd == pytest.approx(per_kwh_gen)
    # Higher diesel price -> diesel-only cost rises faster than hybrid.
    e2 = fin.economics(1000, 10, [300, 300], [30, 30], 4.0)
    assert (e2.cost_per_kwh_diesel_usd - e.cost_per_kwh_diesel_usd
            > e2.cost_per_kwh_hybrid_usd - e.cost_per_kwh_hybrid_usd)


def test_staged_expansion_candidates_are_costed_and_checked(lead_acid_run):
    inputs, _, comp = lead_acid_run
    staged = [c for c in comp.candidates if c.name.startswith("C:")]
    assert staged
    for c in staged:
        y = c.replacement_year
        assert c.years[y - 2].pv_kw == pytest.approx(c.pv_kw)            # before the upgrade
        assert c.years[y - 1].pv_kw == pytest.approx(c.upgrade_pv_kw)    # from the upgrade year
        added_pv = (c.upgrade_pv_kw - c.pv_kw) * fin.config.PV_COST_USD_PER_KW
        assert c.replacement_usd == pytest.approx(
            added_pv + fin.replacement_cost_usd(c.upgrade_battery_kwh, inputs.battery_chemistry, y))
        assert c.om_by_year[y - 1] == pytest.approx(fin.annual_om_usd(c.upgrade_pv_kw, c.upgrade_battery_kwh))
        assert c.meets_target_every_year == (min(r.renewable_share for r in c.years)
                                             >= inputs.renewable_target - 1e-9)


def test_npv_accepts_om_by_year():
    flat = fin.lifetime_npv_usd(0, 10, [0, 0], 1.0)
    stepped = fin.lifetime_npv_usd(0, [10, 20], [0, 0], 1.0)
    assert stepped - flat == pytest.approx(10 / 1.08 ** 2)
