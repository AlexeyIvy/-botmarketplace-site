from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

STAGE = "SC001-B15-P1-IDENTITY-AUDIT-V0.2"
SOURCE_RUN = "20260920T210446Z"
AUDIT_ONLY = True

HERE = Path(__file__).resolve().parent
INPUT = HERE / "inputs"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def resolve_output_dir() -> Path:
    candidates: list[Path] = []
    for key in ("BOTMARKET_OUTPUT_DIR", "JOB_OUTPUT_DIR", "OUTPUT_DIR"):
        raw = os.environ.get(key)
        if raw:
            candidates.append(Path(raw))
    candidates.extend([Path("/output"), Path.cwd().parent / "output", Path.cwd() / "output"])
    seen: set[str] = set()
    for p in candidates:
        ps = str(p)
        if ps in seen:
            continue
        seen.add(ps)
        if p.exists() and p.is_dir() and os.access(p, os.W_OK):
            return p
    raise RuntimeError("No approved writable output directory found")


def write_json(out_dir: Path, name: str, obj: Any) -> None:
    (out_dir / name).write_text(
        json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_and_verify_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    policy = load_json(HERE / "bundle_policy.json")
    if policy.get("stage") != STAGE:
        raise RuntimeError("bundle policy stage mismatch")
    if policy.get("source_run") != SOURCE_RUN:
        raise RuntimeError("bundle policy source_run mismatch")
    if policy.get("audit_only") is not True:
        raise RuntimeError("audit_only must be true")

    verification: dict[str, Any] = {}
    for rel, spec in policy["input_integrity"].items():
        p = HERE / rel
        if not p.is_file():
            raise RuntimeError(f"missing input file: {rel}")
        row: dict[str, Any] = {"path": rel, "bytes": p.stat().st_size}
        if spec.get("sha256"):
            got = sha256_file(p)
            row["sha256"] = got
            if got != spec["sha256"]:
                raise RuntimeError(f"sha256 mismatch for {rel}")
        if spec.get("git_blob_sha1"):
            got = git_blob_sha1(p)
            row["git_blob_sha1"] = got
            if got != spec["git_blob_sha1"]:
                raise RuntimeError(f"git blob mismatch for {rel}")
        verification[rel] = row
    return policy, verification


def build_maps(net: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    omap: dict[str, dict[str, Any]] = {}
    bmap: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for n in net["networks"]:
        for alias in n["okx_aliases"]:
            if alias in omap:
                raise RuntimeError(f"duplicate OKX alias in registry: {alias}")
            omap[alias] = n
        for code in n["bybit_chain_codes"]:
            bmap[code].append(n)
    return omap, dict(bmap)


def canonical_contract(raw_value: Any, rule: str) -> tuple[str | None, str | None, str | None]:
    raw = "" if raw_value is None else str(raw_value)
    normalized = raw.strip()

    if not normalized:
        return None, None, None

    if rule in {"evm_address", "evm_address_or_native"}:
        if not re.fullmatch(r"0x[0-9a-fA-F]{40}", normalized):
            return None, None, "INVALID_EVM_ADDRESS"
        return "token", normalized.lower(), None

    if rule == "case_sensitive_exact":
        return "token", normalized, None

    if rule == "native_only_or_review":
        return None, None, "NONEMPTY_IDENTITY_UNSUPPORTED_BY_NATIVE_ONLY_RULE"

    return None, None, f"UNSUPPORTED_CONTRACT_RULE:{rule}"


def canonicalize_okx(
    row: dict[str, Any],
    omap: dict[str, dict[str, Any]],
    native_pairs: set[tuple[str, str]],
) -> dict[str, Any]:
    asset = str(row["coin"])
    alias = str(row["chain_alias_without_coin_prefix"])
    raw_contract = "" if row.get("contract_address_raw") is None else str(row.get("contract_address_raw"))
    out = {
        "venue": "OKX",
        "asset": asset,
        "raw_network": alias,
        "raw_chain": row.get("chain_raw"),
        "raw_contract": raw_contract,
        "source_mainNet": row.get("mainNet"),
    }

    n = omap.get(alias)
    if n is None:
        return {**out, "status": "UNRESOLVED_ALIAS", "reason": "OKX_ALIAS_NOT_IN_FROZEN_REGISTRY"}

    network_uid = n["network_uid"]
    out["network_uid"] = network_uid
    out["network_family"] = n["family"]
    out["contract_rule"] = n["contract_rule"]

    kind, ident, err = canonical_contract(raw_contract, n["contract_rule"])
    if err:
        return {**out, "status": "UNRESOLVED_IDENTITY", "reason": err}

    if kind is None and ident is None:
        if (network_uid, asset) not in native_pairs:
            return {**out, "status": "UNRESOLVED_IDENTITY", "reason": "EMPTY_WITHOUT_NATIVE_REGISTRY"}
        return {
            **out,
            "status": "ROW_CANONICAL",
            "identity_kind": "native",
            "representation_identity": f"native:{asset}",
        }

    return {
        **out,
        "status": "ROW_CANONICAL",
        "identity_kind": kind,
        "representation_identity": ident,
    }


def canonicalize_bybit(
    row: dict[str, Any],
    bmap: dict[str, list[dict[str, Any]]],
    native_pairs: set[tuple[str, str]],
) -> dict[str, Any]:
    asset = str(row["coin"])
    code = str(row["chain_raw"])
    chain_type = str(row.get("chainType") or "").strip()
    raw_contract = "" if row.get("contract_address_raw") is None else str(row.get("contract_address_raw"))
    out = {
        "venue": "BYBIT",
        "asset": asset,
        "raw_network": code,
        "raw_chain": code,
        "raw_chainType": row.get("chainType"),
        "raw_contract": raw_contract,
    }

    candidates = bmap.get(code, [])
    if not candidates:
        return {**out, "status": "UNRESOLVED_ALIAS", "reason": "BYBIT_CHAIN_CODE_NOT_IN_FROZEN_REGISTRY"}

    exact: list[dict[str, Any]] = []
    case_only: list[dict[str, Any]] = []
    for n in candidates:
        allowed = {str(x).strip() for x in n["bybit_chain_types"]}
        if chain_type in allowed:
            exact.append(n)
        elif chain_type.casefold() in {x.casefold() for x in allowed}:
            case_only.append(n)

    if len(exact) == 0:
        if len(case_only) == 1:
            n = case_only[0]
            return {
                **out,
                "status": "UNRESOLVED_METADATA_VARIANT",
                "reason": "BYBIT_CHAINTYPE_CASE_ONLY_VARIANT_NOT_FROZEN",
                "candidate_network_uid": n["network_uid"],
                "candidate_allowed_chain_types": n["bybit_chain_types"],
            }
        return {
            **out,
            "status": "UNRESOLVED_IDENTITY",
            "reason": "BYBIT_CHAINTYPE_NOT_ALLOWED_FOR_MAPPED_CODE",
            "candidate_network_uids": [n["network_uid"] for n in candidates],
        }

    if len(exact) > 1:
        return {
            **out,
            "status": "UNRESOLVED_ALIAS",
            "reason": "BYBIT_CHAIN_CODE_AMBIGUOUS_ACROSS_NETWORKS",
            "candidate_network_uids": [n["network_uid"] for n in exact],
        }

    n = exact[0]
    network_uid = n["network_uid"]
    out["network_uid"] = network_uid
    out["network_family"] = n["family"]
    out["contract_rule"] = n["contract_rule"]

    kind, ident, err = canonical_contract(raw_contract, n["contract_rule"])
    if err:
        return {**out, "status": "UNRESOLVED_IDENTITY", "reason": err}

    if kind is None and ident is None:
        if (network_uid, asset) not in native_pairs:
            return {**out, "status": "UNRESOLVED_IDENTITY", "reason": "EMPTY_WITHOUT_NATIVE_REGISTRY"}
        return {
            **out,
            "status": "ROW_CANONICAL",
            "identity_kind": "native",
            "representation_identity": f"native:{asset}",
        }

    return {
        **out,
        "status": "ROW_CANONICAL",
        "identity_kind": kind,
        "representation_identity": ident,
    }


def rep_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row["network_uid"]),
        str(row["identity_kind"]),
        str(row["representation_identity"]),
    )


def classify_asset_rows(
    asset: str,
    ok_rows: list[dict[str, Any]],
    by_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    ok_can = [x for x in ok_rows if x["status"] == "ROW_CANONICAL"]
    by_can = [x for x in by_rows if x["status"] == "ROW_CANONICAL"]

    ok_keys = {rep_key(x) for x in ok_can}
    by_keys = {rep_key(x) for x in by_can}
    common = ok_keys & by_keys

    ok_network_identities: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    by_network_identities: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for x in ok_can:
        ok_network_identities[x["network_uid"]].add(rep_key(x))
    for x in by_can:
        by_network_identities[x["network_uid"]].add(rep_key(x))

    def finalize(row: dict[str, Any], own: str) -> dict[str, Any]:
        if row["status"] != "ROW_CANONICAL":
            return row
        key = rep_key(row)
        if key in common:
            return {**row, "status": "COMMON_PROVEN"}
        network = row["network_uid"]
        other_ids = by_network_identities[network] if own == "OKX" else ok_network_identities[network]
        if other_ids:
            return {
                **row,
                "status": "CONFLICTING_IDENTITY",
                "reason": "OTHER_VENUE_HAS_DIFFERENT_CANONICAL_IDENTITY_ON_SAME_NETWORK",
                "other_venue_keys": [list(x) for x in sorted(other_ids)],
            }
        return {**row, "status": "KNOWN_ONE_SIDED"}

    ok_final = [finalize(x, "OKX") for x in ok_rows]
    by_final = [finalize(x, "BYBIT") for x in by_rows]

    unresolved_statuses = {
        "UNRESOLVED_ALIAS",
        "UNRESOLVED_IDENTITY",
        "UNRESOLVED_METADATA_VARIANT",
        "CONFLICTING_IDENTITY",
    }
    unresolved = [x for x in ok_final + by_final if x["status"] in unresolved_statuses]

    if unresolved:
        asset_status = "IDENTITY_REVIEW"
    elif common:
        asset_status = "RESOLVED_CANDIDATE"
    else:
        asset_status = "IDENTITY_REVIEW_NO_COMMON_REPRESENTATION"

    common_rows = []
    for key in sorted(common):
        common_rows.append(
            {
                "asset": asset,
                "network_uid": key[0],
                "identity_kind": key[1],
                "representation_identity": key[2],
            }
        )

    summary = {
        "asset": asset,
        "status": asset_status,
        "common_proven_count": len(common),
        "common_proven": common_rows,
        "okx_status_counts": dict(sorted(Counter(x["status"] for x in ok_final).items())),
        "bybit_status_counts": dict(sorted(Counter(x["status"] for x in by_final).items())),
        "unresolved_reasons": sorted(
            {
                str(x.get("reason"))
                for x in unresolved
                if x.get("reason") is not None
            }
        ),
    }
    return ok_final, by_final, summary


def main() -> int:
    policy, verification = load_and_verify_inputs()

    final_builder = load_json(INPUT / "final_builder_manifest.json")
    if final_builder.get("source_run") != SOURCE_RUN:
        raise RuntimeError("final_builder_manifest source_run mismatch")
    if final_builder.get("price_data_used") is not False:
        raise RuntimeError("price firewall violated in source final_builder_manifest")
    if final_builder.get("transfer_status_used_for_selection") is not False:
        raise RuntimeError("transfer-status firewall violated in source final_builder_manifest")
    if final_builder.get("identity_review_assets") != 46:
        raise RuntimeError("expected exactly 46 v0.1 identity-review assets")

    identity_review = load_json(INPUT / "IDENTITY_REVIEW.json")
    if len(identity_review) != 46:
        raise RuntimeError("IDENTITY_REVIEW snapshot is not 46 assets")
    review_assets = [str(x["asset"]) for x in identity_review]
    if len(set(review_assets)) != 46:
        raise RuntimeError("duplicate asset in IDENTITY_REVIEW snapshot")
    review_set = set(review_assets)

    okx_source = load_json(INPUT / "okx_chain_identity_view.json")
    bybit_source = load_json(INPUT / "bybit_chain_identity_view.json")
    net = load_json(INPUT / "network_registry_v0.1.json")
    native = load_json(INPUT / "native_registry_v0.1.json")

    omap, bmap = build_maps(net)
    native_pairs = {(str(x["network_uid"]), str(x["native_asset"])) for x in native["rows"]}

    okx_rows_all: list[dict[str, Any]] = []
    bybit_rows_all: list[dict[str, Any]] = []
    case_summaries: list[dict[str, Any]] = []

    okx_by_asset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    bybit_by_asset: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in okx_source:
        asset = str(row["coin"])
        if asset in review_set or asset == "USDT":
            okx_by_asset[asset].append(canonicalize_okx(row, omap, native_pairs))

    for row in bybit_source:
        asset = str(row["coin"])
        if asset in review_set or asset == "USDT":
            bybit_by_asset[asset].append(canonicalize_bybit(row, bmap, native_pairs))

    for asset in review_assets:
        ok_final, by_final, summary = classify_asset_rows(
            asset,
            okx_by_asset.get(asset, []),
            bybit_by_asset.get(asset, []),
        )
        okx_rows_all.extend(ok_final)
        bybit_rows_all.extend(by_final)
        case_summaries.append(summary)

    q_ok, q_by, q_summary = classify_asset_rows(
        "USDT",
        okx_by_asset.get("USDT", []),
        bybit_by_asset.get("USDT", []),
    )

    global_counts = Counter(x["status"] for x in okx_rows_all + bybit_rows_all)
    asset_counts = Counter(x["status"] for x in case_summaries)
    quote_counts = Counter(x["status"] for x in q_ok + q_by)

    common_reps = [x for s in case_summaries for x in s["common_proven"]]
    known_one_sided = [
        x
        for x in okx_rows_all + bybit_rows_all
        if x["status"] == "KNOWN_ONE_SIDED"
    ]

    manifest = {
        "stage": STAGE,
        "source_run": SOURCE_RUN,
        "audit_only": True,
        "price_data_used": False,
        "transfer_status_used_for_selection": False,
        "review_assets_expected": 46,
        "review_assets_observed": len(case_summaries),
        "asset_status_counts": dict(sorted(asset_counts.items())),
        "representation_status_counts": dict(sorted(global_counts.items())),
        "common_proven_representations": len(common_reps),
        "known_one_sided_representations": len(known_one_sided),
        "quote_asset_status": q_summary["status"],
        "quote_representation_status_counts": dict(sorted(quote_counts.items())),
        "input_verification": verification,
        "result_status": "B15_P1_IDENTITY_AUDIT_V02_COMPLETE",
    }

    out_dir = resolve_output_dir()
    write_json(out_dir, "identity_audit_v02_manifest.json", manifest)
    write_json(out_dir, "identity_review_cases_v02.json", case_summaries)
    write_json(out_dir, "representation_disposition_okx.json", okx_rows_all)
    write_json(out_dir, "representation_disposition_bybit.json", bybit_rows_all)
    write_json(out_dir, "common_proven_representations_v02.json", common_reps)
    write_json(out_dir, "known_one_sided_representations_v02.json", known_one_sided)
    write_json(
        out_dir,
        "usdt_quote_audit_v02.json",
        {"summary": q_summary, "okx_rows": q_ok, "bybit_rows": q_by},
    )

    print("B15_P1_IDENTITY_AUDIT_V02_COMPLETE")
    print("review_assets =", len(case_summaries))
    print("asset_status_counts =", dict(sorted(asset_counts.items())))
    print("representation_status_counts =", dict(sorted(global_counts.items())))
    print("quote_asset_status =", q_summary["status"])
    print("quote_representation_status_counts =", dict(sorted(quote_counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
