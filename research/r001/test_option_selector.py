from option_selector import OptionQuote, SelectionConfig, select_option

DAY = 86_400_000_000
T = 1_600_000_000_000_000

quotes = [
    OptionQuote("BTC-60D-10D-P", T, "put", 8000, T + 60 * DAY, 0.01, 0.011, 5, 5, -0.10, 10000),
    OptionQuote("BTC-90D-15D-P", T, "put", 7500, T + 90 * DAY, 0.02, 0.021, 5, 5, -0.151, 10000),
    OptionQuote("BTC-90D-25D-P", T, "put", 8500, T + 90 * DAY, 0.04, 0.041, 5, 5, -0.25, 10000),
    OptionQuote("BTC-90D-15D-C", T, "call", 12500, T + 90 * DAY, 0.02, 0.021, 5, 5, 0.149, 10000),
    OptionQuote("BTC-FUTURE-LOOKAHEAD-P", T + 1_000_000, "put", 7500, T + 90 * DAY, 0.001, 0.002, 5, 5, -0.150, 10000),
]

r = select_option(quotes, T, SelectionConfig())
assert r.quote.symbol == "BTC-90D-15D-P"
assert r.quote.ask_price == 0.021
assert r.delta_error < 0.002
assert r.dte_error == 0

# Stale quotes must not be selected.
try:
    select_option(quotes, T + 302_000_000, SelectionConfig(max_quote_age_seconds=300))
except ValueError:
    pass
else:
    raise AssertionError("Expected stale quote rejection")

print("option_selector tests: OK")
