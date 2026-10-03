import pytest

from sunsafe.lifecycle import finance as fin


def test_recommended_meets_target_every_year(lead_acid_run):
    inputs, _, comp = lead_acid_run
    assert comp.any_feasible
    rec = comp.recommended
    assert all(y.renewable_share >= inputs.renewable_target - 1e-9 for y in rec.years)
    feasible = [c for c in comp.candidates if c.meets_target_every_year]
    assert rec.npv_usd == min(c.npv_usd for c in feasible)


def test_every_candidate_checked_with_its_replacement(lead_acid_run):
    _, _, comp = lead_acid_run
    for c in comp.candidates:
        if c.replacement_year:
            y = c.years[c.replacement_year - 1]
            assert y.battery_year == 1 and y.battery_kwh == pytest.approx(c.battery_kwh)


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
    # capex 100, no O&M, 1 litre/yr at $1 for 2 years, 8%
    npv = fin.lifetime_npv_usd(100, 0, [1, 1], 1.0)
    assert npv == pytest.approx(100 + 1 / 1.08 + 1 / 1.08 ** 2)
    assert fin.levelised_cost_per_kwh(npv, [10, 10]) == pytest.approx(
        npv / (10 / 1.08 + 10 / 1.08 ** 2))


def test_payback():
    assert fin.simple_payback_years(1000, 300, 100) == pytest.approx(5)
    assert fin.simple_payback_years(1000, 100, 100) == float("inf")
