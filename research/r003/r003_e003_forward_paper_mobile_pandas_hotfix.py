"""Android/Pydroid launcher for frozen R003-E003 forward paper with pandas datetime-unit compatibility hotfix.

Economic/research semantics are unchanged. The launcher downloads the exact frozen
engine commit and only normalizes merge_asof key dtypes to datetime64[ns, UTC]
so pandas builds that preserve API millisecond precision do not reject merges
against nanosecond/microsecond Treasury timestamps.
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
ENGINE_FILE = OUTDIR / "r003_e003_forward_paper_v0_2_pandas_hotfix.py"

OLD_FUNDING = '''    base = common[["open_time", "close_time", "mark_close"]].sort_values("close_time")
    x = pd.merge_asof(funding.sort_values("funding_time"), base, left_on="funding_time", right_on="close_time", direction="backward", allow_exact_matches=True)
'''
NEW_FUNDING = '''    funding = funding.copy()
    base = common[["open_time", "close_time", "mark_close"]].copy().sort_values("close_time")
    funding["funding_time"] = funding["funding_time"].astype("datetime64[ns, UTC]")
    base["close_time"] = base["close_time"].astype("datetime64[ns, UTC]")
    x = pd.merge_asof(funding.sort_values("funding_time"), base, left_on="funding_time", right_on="close_time", direction="backward", allow_exact_matches=True)
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
    print("R003-E003 FORWARD PAPER TRACKER - PANDAS COMPATIBILITY HOTFIX")
    print("Frozen economic engine commit:", BASE_ENGINE_COMMIT)
    print("Persistent output folder:", OUTDIR)
    print("Only merge-key datetime units are normalized; research rules are unchanged.")
    print("=" * 72)

    req = Request(ENGINE_URL, headers={"User-Agent": "r003-forward-mobile-pandas-hotfix/0.1"})
    with urlopen(req, timeout=60) as resp:
        source = resp.read().decode("utf-8")

    if source.count(OLD_FUNDING) != 1:
        raise RuntimeError("Funding hotfix anchor mismatch; refusing to execute modified engine")
    if source.count(OLD_TREASURY) != 1:
        raise RuntimeError("Treasury hotfix anchor mismatch; refusing to execute modified engine")

    source = source.replace(OLD_FUNDING, NEW_FUNDING, 1)
    source = source.replace(OLD_TREASURY, NEW_TREASURY, 1)
    ENGINE_FILE.write_text(source, encoding="utf-8")

    sys.argv = [str(ENGINE_FILE), "--outdir", str(OUTDIR)]
    ns = {"__name__": "__main__", "__file__": str(ENGINE_FILE)}
    exec(compile(source, str(ENGINE_FILE), "exec"), ns)

    print()
    print("RUN FINISHED")
    print("Upload result files from:", OUTDIR)
    print("You may omit the .py engine copy.")


if __name__ == "__main__":
    main()
