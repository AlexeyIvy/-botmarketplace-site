from put_only_simulator import (
    PortfolioState,
    PutContract,
    close_put_at_bid,
    open_put,
    option_price_usd,
    periodic_premium_budget_usd,
    portfolio_nav_usd,
    put_intrinsic_usd,
    settle_put_at_expiry,
    size_contracts_from_budget,
)


def test_option_price_conversion():
    assert round(option_price_usd(0.046, 9035.37), 6) == round(415.62702, 6)


def test_budget_sizing_rounds_down_to_0_1_contracts():
    # $100k NAV, 2% annual premium budget, monthly cycle => $166.67.
    budget = periodic_premium_budget_usd(100_000, 0.02, 12)
    qty = size_contracts_from_budget(budget, 0.046, 9035.37, min_contract_increment=0.1)
    assert qty == 0.4
    assert option_price_usd(0.046, 9035.37, qty) <= budget


def test_open_mark_close_put_at_bid():
    state = PortfolioState(cash_usd=90_000, btc_units=10_000 / 9035.37)
    contract = PutContract("BTC-26JUN20-7000-P", 7000, 1593158400000000)
    budget = periodic_premium_budget_usd(100_000, 0.02, 12)

    pos = open_put(
        state,
        contract=contract,
        decision_timestamp_us=1583064000000000,
        ask_btc=0.046,
        underlying_usd=9035.37,
        premium_budget_usd=budget,
    )
    assert pos.contracts == 0.4
    assert state.total_option_premium_paid_usd > 0

    nav = portfolio_nav_usd(state, btc_usd=9035.37, put_value_btc=0.043)
    assert nav < 100_000  # immediate bid/ask spread drag

    net = close_put_at_bid(state, bid_btc=0.043, underlying_usd=9035.37)
    assert net > 0
    assert state.put is None


def test_put_expiry_intrinsic_and_settlement():
    assert put_intrinsic_usd(7000, 5000, 0.4) == 800

    state = PortfolioState(cash_usd=99_000, btc_units=0)
    contract = PutContract("BTC-26JUN20-7000-P", 7000, 1593158400000000)
    state.put = open_put(
        PortfolioState(cash_usd=1_000, btc_units=0),
        contract=contract,
        decision_timestamp_us=1,
        ask_btc=0.01,
        underlying_usd=10_000,
        premium_budget_usd=100,
        min_contract_increment=0.1,
    )

    # Use a fresh state carrying the position for explicit settlement test.
    pos = state.put
    state = PortfolioState(cash_usd=0, btc_units=0, put=pos)
    proceeds = settle_put_at_expiry(state, settlement_usd=5000)
    assert proceeds == 2000  # 1 contract * ($7000-$5000)
    assert state.put is None
