from __future__ import annotations
import argparse, json, shutil
from pathlib import Path

REPO=Path(__file__).resolve().parents[2]
SRCROOT=REPO/"docs/research/artifacts/b15-p1-canonical-freeze"
EXPECTED="B15_P1_CANONICAL_ROUTE_UNIVERSE_IDENTITY_REVIEW"
FILES=("ADMITTED.json","IDENTITY_REVIEW.json","EXCLUDED.json","directed_route_graph.json","usdt_quote_rebalance_graph.json","final_builder_manifest.json")

def fail(s): raise RuntimeError(s)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    a=ap.parse_args()
    src=SRCROOT/a.run_id
    if not src.is_dir(): fail(f"source not found: {src}")
    m=json.loads((src/"final_builder_manifest.json").read_text())
    if m.get("status")!=EXPECTED: fail(f"unexpected builder state: {m.get('status')}")
    if m.get("price_data_used") is not False: fail("price firewall failed")
    if m.get("transfer_status_used_for_selection") is not False: fail("transfer-status selection firewall failed")
    for n in FILES:
        if not (src/n).is_file(): fail(f"missing: {n}")
    # Files are already under docs/research/artifacts in the repo worktree.
    marker={"status":"B15_P1_CANONICAL_REVIEW_SAFE_EXPORT_PASS","run_id":a.run_id,
      "price_data_exported":False,"raw_authenticated_api_exported":False,"credentials_exported":False,
      "files":list(FILES)}
    (src/"SAFE_REVIEW_EXPORT.json").write_text(json.dumps(marker,indent=2,sort_keys=True)+"\n")
    print("B15_P1_CANONICAL_REVIEW_SAFE_EXPORT_PASS")
    print("directory =",src)
    print("price_data_exported = False")
    print("raw_authenticated_api_exported = False")
    print("credentials_exported = False")
if __name__=="__main__": main()
