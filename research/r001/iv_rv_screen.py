"""R001 E004-S IV/RV screening on monthly Deribit options + daily Bybit BTC data.

Research-only. Uses strictly backward-looking RV features: at a 12:00 UTC monthly
decision, the current UTC daily candle is excluded and RV ends on the prior day.
"""

import argparse
import math
import numpy as np
import pandas as pd


def parse_expiry(code):
    return pd.to_datetime(code, format="%d%b%y", utc=True) + pd.Timedelta(hours=8)


def load_options(path):
    df = pd.read_csv(path)
    df["decision_dt"] = pd.to_datetime(df["decision_time"], utc=True)
    df["expiry_dt"] = df["expiry_code"].map(parse_expiry)
    df["dte"] = (df["expiry_dt"] - df["decision_dt"]).dt.total_seconds() / 86400
    df["spread_rel"] = (df["best_ask_price"] - df["best_bid_price"]) / df["best_ask_price"]
    return df


def select_puts(df, target_delta=0.15):
    out = []
    for dt in sorted(df["decision_dt"].unique()):
        g = df[(df["decision_dt"] == dt) & (df["option_type"] == "put")].copy()
        g = g[(g["best_bid_price"] > 0) & (g["best_ask_price"] > 0) & g["delta"].notna()]
        h = g[(g["dte"] >= 60) & (g["dte"] <= 120)].copy()
        fallback = False
        if h.empty:
            h = g[(g["dte"] >= 45) & (g["dte"] <= 150)].copy()
            fallback = True
        if h.empty:
            continue
        h["dte_err"] = (h["dte"] - 90).abs()
        h["delta_err"] = (h["delta"].abs() - target_delta).abs()
        h = h.sort_values(["dte_err", "delta_err", "spread_rel", "instrument_name"])
        r = h.iloc[0].copy()
        r["fallback"] = fallback
        out.append(r)
    return pd.DataFrame(out).reset_index(drop=True)


def load_btc(path):
    b = pd.read_csv(path)
    b["date"] = pd.to_datetime(b["date_utc"], utc=True)
    b = b.sort_values("date").reset_index(drop=True)
    b["logret"] = np.log(b["close"]).diff()
    for n in (20, 60):
        b[f"rv{n}"] = b["logret"].rolling(n).std(ddof=1) * math.sqrt(365) * 100
    return b


def enrich(selected, options, btc):
    s = selected.copy().sort_values("decision_dt").reset_index(drop=True)
    rv20, rv60 = [], []
    for _, r in s.iterrows():
        prev_day = r["decision_dt"].normalize() - pd.Timedelta(days=1)
        q = btc[btc["date"] == prev_day]
        rv20.append(float(q.iloc[0]["rv20"]) if not q.empty else np.nan)
        rv60.append(float(q.iloc[0]["rv60"]) if not q.empty else np.nan)
    s["rv20"] = rv20
    s["rv60"] = rv60
    s["iv_rv20"] = s["mark_iv"] / s["rv20"]
    s["iv_rv60"] = s["mark_iv"] / s["rv60"]

    for col in ("mark_iv", "iv_rv20", "iv_rv60"):
        med = []
        for i in range(len(s)):
            hist = s[col].iloc[max(0, i - 24):i].dropna()
            med.append(hist.median() if len(hist) >= 12 else np.nan)
        s[col + "_prior24_med"] = med

    s["iv50"] = s["mark_iv_prior24_med"].notna() & (s["mark_iv"] <= s["mark_iv_prior24_med"])
    s["ratio60_50"] = s["iv_rv60_prior24_med"].notna() & (s["iv_rv60"] <= s["iv_rv60_prior24_med"])
    s["spread10"] = s["spread_rel"] <= 0.10

    s["next_underlying"] = s["underlying_price"].shift(-1)
    s["btc_ret"] = s["next_underlying"] / s["underlying_price"] - 1

    exit_bid, exit_underlying = [], []
    for i, r in s.iterrows():
        if i == len(s) - 1:
            exit_bid.append(np.nan)
            exit_underlying.append(np.nan)
            continue
        next_dt = s.loc[i + 1, "decision_dt"]
        q = options[(options["decision_dt"] == next_dt) & (options["instrument_name"] == r["instrument_name"])]
        if q.empty:
            exit_bid.append(0.0)
            exit_underlying.append(float(s.loc[i + 1, "underlying_price"]))
        else:
            x = q.iloc[0]
            exit_bid.append(max(0.0, float(x["best_bid_price"] if pd.notna(x["best_bid_price"]) else 0.0)))
            exit_underlying.append(float(x["underlying_price"]))
    s["exit_bid"] = exit_bid
    s["exit_underlying"] = exit_underlying
    s["entry_usd"] = s["best_ask_price"] * s["underlying_price"]
    s["exit_usd"] = s["exit_bid"] * s["exit_underlying"]
    s["option_ret"] = s["exit_usd"] / s["entry_usd"] - 1
    return s


def simulate(s, mask, annual_budget=0.005, btc_weight=0.15, start=None, end=None):
    idx = list(range(len(s) - 1))
    if start is not None:
        start_dt = pd.Timestamp(start, tz="UTC") + pd.Timedelta(hours=12)
        idx = [i for i in idx if s.loc[i, "decision_dt"] >= start_dt]
    if end is not None:
        end_dt = pd.Timestamp(end, tz="UTC") + pd.Timedelta(hours=12)
        idx = [i for i in idx if s.loc[i + 1, "decision_dt"] <= end_dt]
    nav = 100000.0
    curve = [nav]
    option_pnl = 0.0
    purchases = 0
    for i in idx:
        r = s.loc[i]
        base_pnl = nav * btc_weight * r["btc_ret"]
        op = 0.0
        if bool(mask.iloc[i]):
            budget = nav * annual_budget / 12
            op = budget * r["option_ret"]
            option_pnl += op
            purchases += 1
        nav += base_pnl + op
        curve.append(nav)
    years = (s.loc[idx[-1] + 1, "decision_dt"] - s.loc[idx[0], "decision_dt"]).days / 365.25
    cagr = (nav / 100000.0) ** (1 / years) - 1
    a = np.asarray(curve)
    maxdd = np.min(a / np.maximum.accumulate(a) - 1)
    return cagr, maxdd, option_pnl, purchases


def main():
    p = argparse.ArgumentParser()
    p.add_argument("options_csv")
    p.add_argument("btc_csv")
    args = p.parse_args()

    options = load_options(args.options_csv)
    btc = load_btc(args.btc_csv)
    s = enrich(select_puts(options), options, btc)

    rules = {
        "baseline": pd.Series(False, index=s.index),
        "iv50_spread": s["iv50"] & s["spread10"],
        "iv50_ratio60_50_spread": s["iv50"] & s["ratio60_50"] & s["spread10"],
        "iv50_rv60_le_1_25_spread": s["iv50"] & (s["iv_rv60"] <= 1.25) & s["spread10"],
        "iv50_rv20_le_1_25_spread": s["iv50"] & (s["iv_rv20"] <= 1.25) & s["spread10"],
    }

    print("selected months:", len(s), "fallback:", int(s["fallback"].sum()))
    for period in [(None, None), ("2019-10-01", "2022-12-01"), ("2023-01-01", "2026-09-01")]:
        print("\nperiod", period)
        for name, mask in rules.items():
            print(name, simulate(s, mask, 0.005, 0.15, *period))


if __name__ == "__main__":
    main()
