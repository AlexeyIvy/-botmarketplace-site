"""Tests for Tardis Deribit options-chain normalization.

The example below is based on the public Tardis options_chain documentation
preview for Deribit. It is a schema/normalization audit fixture, not evidence
of strategy profitability.
"""

from io import StringIO

from tardis_options_adapter import iter_csv, validate_required_fields


CSV_FIXTURE = """exchange,symbol,timestamp,local_timestamp,type,strike_price,expiration,open_interest,last_price,bid_price,bid_amount,bid_iv,ask_price,ask_amount,ask_iv,mark_price,mark_iv,underlying_index,underlying_price,delta,gamma,vega,theta,rho
deribit,BTC-9JUN20-9875-P,1591574399413000,1591574400196008,put,9875,1591689600000000,0.1,0.0295,0.0205,15.0,55.91,0.0235,15.0,68.94,0.02210436,62.89,SYN.BTC-9JUN20,9756.36,-0.61752,0.00103,2.24964,-53.05655,-0.22796
"""


def test_documented_tardis_row_normalizes() -> None:
    rows = list(iter_csv(StringIO(CSV_FIXTURE)))
    assert len(rows) == 1
    row = rows[0]
    assert row["exchange"] == "deribit"
    assert row["symbol"] == "BTC-9JUN20-9875-P"
    assert row["type"] == "put"
    assert row["timestamp"] == 1591574399413000
    assert row["expiration"] == 1591689600000000
    assert row["strike_price"] == 9875.0
    assert row["bid_price"] == 0.0205
    assert row["ask_price"] == 0.0235
    assert row["underlying_price"] == 9756.36
    assert row["delta"] == -0.61752
    validate_required_fields(rows)


def test_empty_optional_numeric_fields_become_none() -> None:
    fixture = """exchange,symbol,timestamp,local_timestamp,type,strike_price,expiration,bid_price,ask_price,underlying_price,delta\nderibit,BTC-X-P,1,2,put,10000,3,,,,\n"""
    row = list(iter_csv(StringIO(fixture)))[0]
    assert row["bid_price"] is None
    assert row["ask_price"] is None
    assert row["underlying_price"] is None
    assert row["delta"] is None
