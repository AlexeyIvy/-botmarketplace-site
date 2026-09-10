"""Android/Pydroid launcher for frozen R003-E003 with technical causality + pandas hotfixes.

This does NOT change the frozen strategy, inception, costs, funding sign, hedge,
rebalance cadence, or evidence thresholds. It downloads the exact frozen economic
engine commit and applies only implementation fixes:
1) normalize merge_asof datetime units for pandas compatibility;
2) attribute each realized funding event to the first fully closed common hourly
   bar whose close is at/after the funding timestamp, while using only the latest
   causally available prior mark close as fallback when Binance does not publish
   a valid funding mark;
3) include a funding event in a snapshot only when funding_time <= latest closed
   common bar.

These changes prevent a funding event such as 16:00:00 UTC from being credited
inside the 15:00-15:59:59.999 bar, i.e. one millisecond before the event occurs.
"""
from pathlib import Path
import sys
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
OUTDIR = DOWNLOAD / "R003_E003_FORWARD"
BASE_ENGINE_COMMIT = "cfc001400008ee4d63a27ad6821dda5cb9354f3e"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + BASE_ENGINE_COMMIT
    + "/research/r003/r003_e003_forward_paper_v0_2.py"
)
ENGINE_FILE = OUTDIR / "r003_e003_forward_paper_v0_2_causality_hotfix.py"

OLD_ALIGN = '''def align_funding(funding, common):
    if funding.empty or common.empty:
        return pd.DataFrame(columns=["funding_time", "funding_rate", "published_mark_price", "rate_type", "open_time", "close_time", "mark_close", "funding_mark"])
    base = common[["open_time", "close_time", "mark_close"]].sort_values("close_time")
    x = pd.merge_asof(funding.sort_values("funding_time"), base, left_on="funding_time", right_on="close_time", direction="backward", allow_exact_matches=True)
    x["funding_mark"] = x["published_mark_price"]
    bad = x["funding_mark"].isna() | (x["funding_mark"] <= 0)
    x.loc[bad, "funding_mark"] = x.loc[bad, "mark_close"]
    return x.dropna(subset=["open_time", "funding_mark"]).reset_index(drop=True)
'''

NEW_ALIGN = '''def align_funding(funding, common):
    if funding.empty or common.empty:
        return pd.DataFrame(columns=["funding_time", "funding_rate", "published_mark_price", "rate_type", "open_time", "close_time", "mark_close", "funding_mark"])
    funding = funding.copy().sort_values("funding_time").reset_index(drop=True)
    funding["funding_time"] = funding["funding_time"].astype("datetime64[ns, UTC]")

    # Application row: first CLOSED common hourly bar whose close is not before
    # the funding timestamp. Example: a 16:00 funding event belongs to the
    # 16:00-16:59:59.999 accounting row, never to the 15:00 row.
    app = common[["open_time", "close_time", "mark_close"]].copy().sort_values("close_time")
    app["close_time"] = app["close_time"].astype("datetime64[ns, UTC]")
    x = pd.merge_asof(
        funding,
        app,
        left_on="funding_time",
        right_on="close_time",
        direction="forward",
        allow_exact_matches=True,
    )

    # Fallback funding mark must be causal: if Binance does not publish a valid
    # funding mark, use the latest common mark close at/before funding_time.
    causal = common[["close_time", "mark_close"]].copy().sort_values("close_time")
    causal["close_time"] = causal["close_time"].astype("datetime64[ns, UTC]")
    causal = causal.rename(columns={"close_time": "causal_close_time", "mark_close": "causal_mark_close"})
    back = pd.merge_asof(
        funding[["funding_time"]],
        causal,
        left_on="funding_time",
        right_on="causal_close_time",
        direction="backward",
        allow_exact_matches=True,
    )

    x["funding_mark"] = x["published_mark_price"]
    bad = x["funding_mark"].isna() | (x["funding_mark"] <= 0)
    x.loc[bad, "funding_mark"] = back.loc[bad, "causal_mark_close"].to_numpy()
    return x.dropna(subset=["open_time", "close_time", "funding_mark"]).reset_index(drop=True)
'''

OLD_FA = '''    fa = funding_aligned[(funding_aligned["funding_time"] > init_close) & (funding_aligned["close_time"] <= z["close_time"].iloc[-1])].copy()
'''
NEW_FA = '''    fa = funding_aligned[(funding_aligned["funding_time"] > init_close) & (funding_aligned["funding_time"] <= z["close_time"].iloc[-1])].copy()
'''

OLD_TREASURY = '''    p = path[["close_time"]].copy().sort_values("close_time").reset_index(drop=True)
    t = treasury[["quote_date", "effective_time", "rate_pct"]].copy().sort_values("effective_time")
    m = pd.merge_asof(p, t, left_on="close_time", right_on="effective_time", direction="backward", allow_exact_matches=True)
'''
NEW_TREASURY = '''    p = path[["close_time"]].copy().sort_values("close_time").reset_index(drop=True)
    t = treasury[["quote_date", "effective_time", "rate_pct"]].copy().sort_values("effective_time")
    p["close_time"] = p["close_time"].astype("datetime64[ns, UTC]")
    t["effective_time"] = t["effective_time"].astype("datetime64[ns, UTC]")
    m = pd.merge_asof(p, t, left_on="close_time", right_on="effective_time", direction="backward", allow_exact_matches=True)
'''


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print("=" * 72)
    print("R003-E003 FORWARD - FUNDING CAUSALITY + PANDAS HOTFIX")
    print("Frozen economic engine commit:", BASE_ENGINE_COMMIT)
    print("Persistent output folder:", OUTDIR)
    print("Inception and all economic rules remain unchanged.")
    print("=" * 72)

    req = Request(ENGINE_URL, headers={"User-Agent": "r003-forward-causality-hotfix/0.1"})
    with urlopen(req, timeout=60) as resp:
        source = resp.read().decode("utf-8")

    anchors = [(OLD_ALIGN, "align_funding"), (OLD_FA, "funding snapshot filter"), (OLD_TREASURY, "Treasury merge")]
    for old, name in anchors:
        if source.count(old) != 1:
            raise RuntimeError(f"{name} hotfix anchor mismatch; refusing to execute")

    source = source.replace(OLD_ALIGN, NEW_ALIGN, 1)
    source = source.replace(OLD_FA, NEW_FA, 1)
    source = source.replace(OLD_TREASURY, NEW_TREASURY, 1)
    ENGINE_FILE.write_text(source, encoding="utf-8")

    sys.argv = [str(ENGINE_FILE), "--outdir", str(OUTDIR)]
    ns = {"__name__": "__main__", "__file__": str(ENGINE_FILE)}
    exec(compile(source, str(ENGINE_FILE), "exec"), ns)

    print()
    print("RUN FINISHED")
    print("Forward record preserved from the original fixed boundary.")
    print("Upload result files from:", OUTDIR)


if __name__ == "__main__":
    main()
