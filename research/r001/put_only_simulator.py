"""R001-E003 minimal put-only portfolio simulator.

Research-only code. This module is deliberately small and auditable. It models
one BTC directional sleeve plus cash and long BTC inverse options purchased at
historical ask and liquidated/marked from historical quotes.

Important accounting convention for Deribit inverse BTC options:
- option quote prices are in BTC per 1 BTC option contract;
- USD premium at trade time = option_price_btc * BTC_index_usd * contracts;
- for pre-expiry MTM, USD option value uses the same conversion with a chosen
  executable/mark quote according to the experiment rule;
- expiry intrinsic USD per 1 contract is max(K-S,0) for a put; equivalent BTC
  settlement is intrinsic_usd / settlement_price.

The full historical E003 experiment still requires a multi-date options dataset.
This module provides the frozen accounting/state transition layer first.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PutContract:
    symbol: str
    strike_usd: float
    expiration_us: int


@dataclass
class PutPosition:
    contract: PutContract
    contracts: float
    entry_timestamp_us: int
    entry_ask_btc: float
    entry_underlying_usd: float
    premium_paid_usd: float


@dataclass
class PortfolioState:
    cash_usd: float
    btc_units: float
    put: Optional[PutPosition] = None
    total_option_premium_paid_usd: float = 0.0
    total_option_sale_proceeds_usd: float = 0.0
    total_option_expiry_proceeds_usd: float = 0.0


def option_price_usd(price_btc: float, underlying_usd: float, contracts: float = 1.0) -> float:
    if price_btc < 0 or underlying_usd <= 0 or contracts < 0:
        raise ValueError("invalid option price conversion inputs")
    return price_btc * underlying_usd * contracts


def put_intrinsic_usd(strike_usd: float, settlement_usd: float, contracts: float = 1.0) -> float:
    if strike_usd <= 0 or settlement_usd <= 0 or contracts < 0:
        raise ValueError("invalid put intrinsic inputs")
    return max(strike_usd - settlement_usd, 0.0) * contracts


def size_contracts_from_budget(
    budget_usd: float,
    ask_btc: float,
    underlying_usd: float,
    *,
    min_contract_increment: float = 0.1,
) -> float:
    """Return contracts affordable within budget, rounded DOWN to lot increment."""
    if budget_usd < 0:
        raise ValueError("budget_usd must be >= 0")
    if ask_btc <= 0 or underlying_usd <= 0:
        raise ValueError("ask and underlying must be positive")
    if min_contract_increment <= 0:
        raise ValueError("min_contract_increment must be positive")

    cost_per_contract = option_price_usd(ask_btc, underlying_usd)
    raw = budget_usd / cost_per_contract
    lots = int((raw + 1e-12) / min_contract_increment)
    return lots * min_contract_increment


def open_put(
    state: PortfolioState,
    *,
    contract: PutContract,
    decision_timestamp_us: int,
    ask_btc: float,
    underlying_usd: float,
    premium_budget_usd: float,
    fee_usd: float = 0.0,
    min_contract_increment: float = 0.1,
) -> PutPosition:
    if state.put is not None:
        raise ValueError("put position already open")
    contracts = size_contracts_from_budget(
        premium_budget_usd,
        ask_btc,
        underlying_usd,
        min_contract_increment=min_contract_increment,
    )
    if contracts <= 0:
        raise ValueError("premium budget cannot fund minimum option size")

    premium = option_price_usd(ask_btc, underlying_usd, contracts)
    total_debit = premium + fee_usd
    if total_debit > state.cash_usd + 1e-9:
        raise ValueError("insufficient cash")

    pos = PutPosition(
        contract=contract,
        contracts=contracts,
        entry_timestamp_us=decision_timestamp_us,
        entry_ask_btc=ask_btc,
        entry_underlying_usd=underlying_usd,
        premium_paid_usd=premium,
    )
    state.cash_usd -= total_debit
    state.total_option_premium_paid_usd += premium
    state.put = pos
    return pos


def close_put_at_bid(
    state: PortfolioState,
    *,
    bid_btc: float,
    underlying_usd: float,
    fee_usd: float = 0.0,
) -> float:
    if state.put is None:
        raise ValueError("no put position open")
    if bid_btc < 0:
        raise ValueError("bid must be >= 0")

    proceeds = option_price_usd(bid_btc, underlying_usd, state.put.contracts)
    net = max(proceeds - fee_usd, 0.0)
    state.cash_usd += net
    state.total_option_sale_proceeds_usd += proceeds
    state.put = None
    return net


def settle_put_at_expiry(
    state: PortfolioState,
    *,
    settlement_usd: float,
    fee_usd: float = 0.0,
) -> float:
    if state.put is None:
        raise ValueError("no put position open")

    proceeds = put_intrinsic_usd(
        state.put.contract.strike_usd,
        settlement_usd,
        state.put.contracts,
    )
    net = max(proceeds - fee_usd, 0.0)
    state.cash_usd += net
    state.total_option_expiry_proceeds_usd += proceeds
    state.put = None
    return net


def portfolio_nav_usd(
    state: PortfolioState,
    *,
    btc_usd: float,
    put_value_btc: Optional[float] = None,
) -> float:
    if btc_usd <= 0:
        raise ValueError("btc_usd must be positive")

    option_value = 0.0
    if state.put is not None:
        if put_value_btc is None:
            raise ValueError("put_value_btc required while put is open")
        option_value = option_price_usd(put_value_btc, btc_usd, state.put.contracts)

    return state.cash_usd + state.btc_units * btc_usd + option_value


def periodic_premium_budget_usd(nav_usd: float, annual_budget_pct: float, periods_per_year: int = 12) -> float:
    """Simple frozen E003 budget rule: annual NAV budget divided equally by cycles."""
    if nav_usd < 0 or annual_budget_pct < 0 or periods_per_year <= 0:
        raise ValueError("invalid premium budget inputs")
    return nav_usd * annual_budget_pct / periods_per_year
