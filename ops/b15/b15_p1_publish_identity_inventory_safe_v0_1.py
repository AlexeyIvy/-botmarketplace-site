from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

SOURCE_ROOT = Path("/home/botmarket/sc001_data/B15_P1_IDENTITY_INVENTORY_V01")
REPO_ROOT = Path(__file__).resolve().parents[2]
DEST_ROOT = REPO_ROOT / "docs/research/artifacts/b15-p1-identity-inventory"

REQUIRED_SAFE = (
    "okx_spot_usdt_markets.json",
    "bybit_spot_usdt_markets.json",
    "okx_chain_identity_view.json",
    "bybit_chain_identity_view.json",
    "common_base_candidates.json",
    "chain_alias_census.json",
    "recent_bybit_new_crypto_spot_listings.json",
    "recent_bybit_spot_delistings.json",
)

EXPECTED_STATUS = "B15_P1_NONPRICE_IDENTITY_INVENTORY_PROBE_PASS"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def latest_run() -> Path:
    runs = sorted(
        p for p in SOURCE_ROOT.iterdir()
        if p.is_dir() and p.name.endswith("Z")
    )
    if not runs:
        fail(f"no run directories under {SOURCE_ROOT}")
    return runs[-1]


def load_manifest(run: Path) -> dict:
    path = run / "run_manifest.json"
    if not path.exists():
        fail(f"missing manifest: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail("manifest must be object")
    if obj.get("status") != EXPECTED_STATUS:
        fail(f"run is not PASS: {obj.get('status')}")
    if obj.get("price_endpoints_called") is not False:
        fail("price firewall invariant failed")
    if obj.get("order_endpoints_called") is not False:
        fail("order firewall invariant failed")
    if obj.get("transfer_endpoints_called") is not False:
        fail("transfer firewall invariant failed")
    if obj.get("withdraw_endpoints_called") is not False:
        fail("withdraw firewall invariant failed")
    if obj.get("secret_values_printed") is not False:
        fail("secret-print invariant failed")
    return obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="")
    args = ap.parse_args()

    run = SOURCE_ROOT / args.run_id if args.run_id else latest_run()
    if not run.is_dir():
        fail(f"run not found: {run}")

    manifest = load_manifest(run)
    safe = run / "safe"
    if not safe.is_dir():
        fail(f"safe directory missing: {safe}")

    dest = DEST_ROOT / run.name
    if dest.exists():
        fail(f"destination already exists: {dest}")
    dest.mkdir(parents=True)

    copied = []
    for name in REQUIRED_SAFE:
        src = safe / name
        if not src.exists():
            fail(f"required safe artifact missing: {src}")
        shutil.copy2(src, dest / name)
        copied.append(name)

    # Copy only the manifest from run root. Never copy raw/.
    shutil.copy2(run / "run_manifest.json", dest / "run_manifest.json")
    copied.append("run_manifest.json")

    marker = {
        "status": "SAFE_REVIEW_EXPORT_ONLY",
        "source_run_id": run.name,
        "source_status": manifest.get("status"),
        "raw_api_responses_exported": False,
        "credentials_exported": False,
        "files": copied,
    }
    (dest / "SAFE_EXPORT.json").write_text(
        json.dumps(marker, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("B15_P1_SAFE_IDENTITY_EXPORT_PASS")
    print("source_run =", run)
    print("destination =", dest)
    print("raw_api_responses_exported = False")
    print("credentials_exported = False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
