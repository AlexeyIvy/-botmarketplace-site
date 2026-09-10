"""Safe Android/Pydroid retry wrapper for frozen R003-E003 forward tracker.

Purpose:
- preserve the last valid canonical forward snapshot when Binance returns transient
  HTTP 418/429 or another source error;
- run the already frozen causality-hotfix launcher in a staging folder;
- promote staging results to the canonical folder only after a successful PASS run.

No strategy, inception, funding, hedge, cost, rebalance, or benchmark rule changes.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

DOWNLOAD = Path("/storage/emulated/0/Download")
CANONICAL = DOWNLOAD / "R003_E003_FORWARD"
STAGING = DOWNLOAD / "R003_E003_FORWARD_STAGING"

BASE_HOTFIX_COMMIT = "4aef73ff696821d762e0822c012459078f7b8a33"
BASE_HOTFIX_URL = (
    "https://raw.githubusercontent.com/AlexeyIvy/-botmarketplace-site/"
    + BASE_HOTFIX_COMMIT
    + "/research/r003/r003_e003_forward_paper_mobile_causality_hotfix.py"
)

EXPECTED = [
    "r003_e003_run_state.json",
    "r003_e003_source_audit.json",
    "r003_e003_forward_hourly_nav.csv",
    "r003_e003_metrics.csv",
    "r003_e003_margin.csv",
    "r003_e003_funding_events.csv",
    "r003_e003_monthly.csv",
    "r003_e003_safe_hurdle_daily.csv",
    "r003_e003_summary.md",
]


def fetch_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": "r003-e003-safe-retry/0.1"})
    with urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def main() -> None:
    CANONICAL.mkdir(parents=True, exist_ok=True)
    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("R003-E003 SAFE RETRY WRAPPER")
    print("Frozen causality hotfix commit:", BASE_HOTFIX_COMMIT)
    print("Canonical folder:", CANONICAL)
    print("Staging folder:", STAGING)
    print("Canonical snapshot is replaced only after a successful PASS run.")
    print("=" * 72)

    try:
        source = fetch_text(BASE_HOTFIX_URL)
        old = 'OUTDIR = DOWNLOAD / "R003_E003_FORWARD"'
        new = 'OUTDIR = DOWNLOAD / "R003_E003_FORWARD_STAGING"'
        if source.count(old) != 1:
            raise RuntimeError("Safe-wrapper OUTDIR anchor mismatch; refusing to execute")
        source = source.replace(old, new, 1)

        local = STAGING / "r003_e003_causality_hotfix_staged_launcher.py"
        local.write_text(source, encoding="utf-8")
        ns = {"__name__": "__main__", "__file__": str(local)}
        exec(compile(source, str(local), "exec"), ns)

    except HTTPError as exc:
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        print("\nBINANCE HTTP ERROR:", exc.code, exc.reason)
        if retry_after:
            print("Retry-After header:", retry_after)
        if exc.code in (418, 429):
            print("Do NOT retry repeatedly. Binance is rate-limiting / temporarily banning this IP.")
            print("The previous canonical R003 snapshot has NOT been replaced by this wrapper.")
        raise

    state_path = STAGING / "r003_e003_run_state.json"
    if not state_path.exists():
        raise RuntimeError("Staging run finished without r003_e003_run_state.json")

    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("status") != "PASS":
        print("Staging status is not PASS:", state.get("status"))
        print("Canonical snapshot remains unchanged.")
        return

    missing = [name for name in EXPECTED if not (STAGING / name).exists()]
    if missing:
        raise RuntimeError(f"Successful staging state but missing expected outputs: {missing}")

    for name in EXPECTED:
        shutil.copy2(STAGING / name, CANONICAL / name)

    print("\nSAFE RETRY FINISHED")
    print("Staging PASS promoted to canonical R003_E003_FORWARD.")
    print("Upload the 9 canonical result files from:", CANONICAL)


if __name__ == "__main__":
    main()
