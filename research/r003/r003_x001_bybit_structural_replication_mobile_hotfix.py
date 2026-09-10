"""Android/Pydroid compatibility launcher for frozen R003-X001 Bybit replication.

Technical hotfix only: the frozen research engine and economic/statistical rules remain
at commit c411a1a92f5682f2a5af33871c22064311c4cb86. This launcher normalizes
pandas timezone-aware datetime precision before merge_asof because newer Android/Pydroid
pandas may preserve API milliseconds on one side and microseconds on the other.
"""
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import json

DOWNLOAD = Path("/storage/emulated/0/Download")
WORKSPACE = DOWNLOAD / "R003_X001_BYBIT"
ENGINE_COMMIT = "c411a1a92f5682f2a5af33871c22064311c4cb86"
ENGINE_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + ENGINE_COMMIT
    + "/research/r003/r003_x001_bybit_structural_replication.py"
)
ENGINE_FILE = WORKSPACE / "r003_x001_bybit_structural_replication_v0_1.py"


def main():
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    print("=" * 72)
    print("R003-X001 BYBIT STRUCTURAL FUNDING REPLICATION — PYDROID HOTFIX")
    print("Frozen research engine commit:", ENGINE_COMMIT)
    print("Persistent workspace:", WORKSPACE)
    print("Existing snapshot/checkpoints will be reused.")
    print("=" * 72)

    req = Request(ENGINE_URL, headers={"User-Agent": "r003-x001-bybit-mobile-hotfix/0.1"})
    with urlopen(req, timeout=60) as r:
        ENGINE_FILE.write_bytes(r.read())

    source = ENGINE_FILE.read_text(encoding="utf-8")
    ns = {"__name__": "r003_x001_frozen_engine", "__file__": str(ENGINE_FILE)}
    exec(compile(source, str(ENGINE_FILE), "exec"), ns)

    pd = ns["pd"]

    def merge_state_compat(f, idx):
        left = f.copy()
        right = idx[["close_time", "close", "running_ath", "drawdown"]].copy()

        # pandas 3.x / some Android builds can keep API timestamps at ms precision
        # while Timedelta-derived close_time becomes us precision. merge_asof requires
        # exactly matching dtypes, so normalize both to nanoseconds without changing time.
        left["funding_time"] = pd.to_datetime(left["funding_time"], utc=True).astype(
            "datetime64[ns, UTC]"
        )
        right["close_time"] = pd.to_datetime(right["close_time"], utc=True).astype(
            "datetime64[ns, UTC]"
        )

        return pd.merge_asof(
            left.sort_values("funding_time"),
            right.sort_values("close_time"),
            left_on="funding_time",
            right_on="close_time",
            direction="backward",
            allow_exact_matches=True,
        )

    ns["merge_state"] = merge_state_compat

    try:
        ns["run"](WORKSPACE)
    except Exception as exc:
        out = WORKSPACE / "results"
        out.mkdir(parents=True, exist_ok=True)
        state = {
            "status": "SOURCE_OR_ENGINE_ERROR",
            "engine_version": ns.get("VERSION", "0.1"),
            "protocol": ns.get("PROTOCOL"),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "technical_launcher": "pydroid-datetime-hotfix-v0.1",
            "frozen_engine_commit": ENGINE_COMMIT,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        (out / "r003_x001_bybit_run_state.json").write_text(
            json.dumps(state, indent=2), encoding="utf-8"
        )
        print("RUN FAILED:", type(exc).__name__, str(exc))
        print("Existing checkpoints are preserved; re-run after correction.")
        raise

    print()
    print("RUN FINISHED")
    print("Upload the 8 result files from:", WORKSPACE / "results")
    print("Do not upload checkpoint, snapshot, instrument-info or .py files.")


if __name__ == "__main__":
    main()
