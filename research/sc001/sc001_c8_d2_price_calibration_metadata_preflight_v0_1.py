from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C8-D2-PRICE-CALIBRATION-METADATA-PREFLIGHT-V0.1"
PASS = "C8_D2_PRICE_CALIBRATION_METADATA_PASS"
REVIEW = "C8_D2_PRICE_CALIBRATION_METADATA_REVIEW"

FIXED_DATE = "2025-01-20"
DAY_START_MS = 1737331200000
DAY_END_MS = 1737417600000

OKX_DOMAINS = ("https://www.okx.com", "https://us.okx.com")
OKX_INST = "BTC-USDT-SWAP"
OKX_FAMILY = "BTC-USDT"
OKX_D = "BTC-USDT-SWAP-trades-2025-01-20.zip"
OKX_D1 = "BTC-USDT-SWAP-trades-2025-01-21.zip"
OKX_HOST = "static.okx.com"

BYBIT_URL = "https://public.bybit.com/trading/BTCUSDT/BTCUSDT2025-01-20.csv.gz"
BYBIT_FILE = "BTCUSDT2025-01-20.csv.gz"
BYBIT_HOST = "public.bybit.com"

TIMEOUT = 60
RETRIES = 3
MAX_JSON_BYTES = 4_000_000
MAX_FILE_BYTES = 350 * 1024 * 1024
MAX_TOTAL_BYTES = 700 * 1024 * 1024

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c8-d2-price-calibration-metadata-preflight-protocol-v0.1.md"
FREEZE = ROOT / "docs/research/sc001-c8-d2-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()
D1E_REPORT = (
    DATA_ROOT / "SC001_C8_D1E_STRICT_COACTIVE_1S"
    / "sc001_c8_d1e_strict_coactive_1s_report_v0_1.json"
)
OUT_DIR = DATA_ROOT / "SC001_C8_D2_PRICE_CALIBRATION_METADATA"
OUT = OUT_DIR / "sc001_c8_d2_price_calibration_metadata_report_v0_1.json"


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def git_blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "hash-object", str(path.relative_to(ROOT))],
        text=True,
    ).strip()


def require_freeze() -> dict:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_C8_D2_RUN":
        fail("C8-D2 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C8-D2 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C8-D2 protocol identity mismatch")
    if fr.get("fixed_date") != FIXED_DATE:
        fail("C8-D2 fixed date mismatch")
    if fr.get("representation") != "STRICT_COACTIVE_1S_NO_CARRY_FORWARD":
        fail("C8-D2 representation mismatch")

    for k in (
        "historical_archive_body_authorized",
        "cross_venue_price_comparison_authorized",
        "cross_venue_return_authorized",
        "raw_spread_authorized",
        "dislocation_authorized",
        "lag_authorized",
        "strategy_signal_authorized",
        "pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"C8-D2 firewall mismatch: {k}")
    return fr


def require_d1e() -> dict:
    rep = load_json(D1E_REPORT)
    if rep.get("status") != "C8_D1E_STRICT_COACTIVE_1S_PASS":
        fail("C8-D1E parent not exact PASS")
    if rep.get("representation") != "STRICT_COACTIVE_1S_NO_CARRY_FORWARD":
        fail("C8-D1E representation mismatch")
    if rep.get("failed_gates") != []:
        fail("C8-D1E parent failed_gates not empty")
    for k in (
        "cross_venue_price_compared",
        "cross_venue_return_calculated",
        "dislocation_calculated",
        "lag_calculated",
        "leader_selected",
        "strategy_signal_calculated",
        "pnl_calculated",
        "promotional_alpha_accessed",
    ):
        if rep.get(k) is not False:
            fail(f"C8-D1E parent firewall mismatch: {k}")
    return rep


def trusted_url(url: str, host: str, basename: str) -> bool:
    try:
        p = urllib.parse.urlparse(url)
        return (
            p.scheme == "https"
            and (p.hostname or "").lower() == host
            and Path(p.path).name == basename
        )
    except Exception:
        return False


def walk_nodes(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk_nodes(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_nodes(v)


def resolve_okx_files() -> dict[str, str]:
    payload = {
        "module": "1",
        "instType": "SWAP",
        "instQueryParam": {"instFamilyList": [OKX_FAMILY]},
        "dateQuery": {
            "dateAggrType": "daily",
            "begin": str(DAY_START_MS),
            "end": str(DAY_END_MS - 1),
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    expected = {OKX_D, OKX_D1}

    last = None
    for domain in OKX_DOMAINS:
        url = domain + "/priapi/v5/broker/public/trade-data/download-link?t=" + str(int(time.time()*1000))
        try:
            req = urllib.request.Request(
                url,
                data=body,
                method="POST",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C8-D2/0.1",
                    "Accept": "application/json,*/*",
                    "Content-Type": "application/json",
                    "Referer": "https://www.okx.com/historical-data",
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_JSON_BYTES + 1)
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()

            if len(raw) > MAX_JSON_BYTES:
                fail("OKX metadata response cap exceeded")
            if status != 200:
                fail(f"OKX metadata HTTP {status}")
            p = urllib.parse.urlparse(final)
            if p.scheme != "https" or (p.hostname or "").lower() not in {"www.okx.com", "us.okx.com"}:
                fail(f"unexpected OKX metadata final host: {p.hostname}")

            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict) or str(obj.get("code")) != "0":
                fail(f"OKX metadata code mismatch: {obj.get('code') if isinstance(obj, dict) else None}")

            found: dict[str, str] = {}
            for node in walk_nodes(obj.get("data")):
                if not isinstance(node, dict):
                    continue
                fn = node.get("filename") or node.get("fileName")
                u = node.get("url")
                if (
                    fn in expected
                    and isinstance(u, str)
                    and trusted_url(u, OKX_HOST, str(fn))
                ):
                    prev = found.get(str(fn))
                    if prev is not None and prev != u:
                        fail(f"conflicting OKX URLs for {fn}")
                    found[str(fn)] = u

            if set(found) == expected:
                return found

            last = RuntimeError(f"missing exact OKX files: found={sorted(found)}")

        except Exception as exc:
            last = exc
            continue

    raise RuntimeError(f"OKX exact metadata resolution failed: {type(last).__name__}: {last}")


def head_exact(url: str, host: str, basename: str) -> int:
    last = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": "BotMarketplace-SC001-C8-D2/0.1"},
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
                cl = resp.headers.get("Content-Length")

            if status != 200:
                fail(f"HEAD HTTP {status}: {basename}")
            if not trusted_url(final, host, basename):
                fail(f"HEAD identity mismatch: {basename}")
            if not cl or not cl.isdigit() or int(cl) <= 0:
                fail(f"invalid Content-Length: {basename}")
            size = int(cl)
            if size > MAX_FILE_BYTES:
                fail(f"file exceeds per-file cap: {basename} {size}")
            return size
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))

    raise RuntimeError(f"HEAD failed {basename}: {type(last).__name__}: {last}")


def main() -> int:
    try:
        require_freeze()
        require_d1e()
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        print("C8-D2 resolve OKX D/D+1 metadata", flush=True)
        okx = resolve_okx_files()

        print("C8-D2 HEAD OKX D", flush=True)
        okx_d_size = head_exact(okx[OKX_D], OKX_HOST, OKX_D)

        print("C8-D2 HEAD OKX D+1", flush=True)
        okx_d1_size = head_exact(okx[OKX_D1], OKX_HOST, OKX_D1)

        print("C8-D2 HEAD Bybit D", flush=True)
        bybit_size = head_exact(BYBIT_URL, BYBIT_HOST, BYBIT_FILE)

        total = okx_d_size + okx_d1_size + bybit_size
        if total > MAX_TOTAL_BYTES:
            fail(f"combined archive size cap exceeded: {total}")

        report = {
            "stage": STAGE,
            "version": "0.1",
            "status": PASS,
            "fixed_date": FIXED_DATE,
            "selection_rule": "first Monday after 2025-01-15 engineering day",
            "representation": "STRICT_COACTIVE_1S_NO_CARRY_FORWARD",
            "files": [
                {
                    "venue": "OKX",
                    "role": "D",
                    "filename": OKX_D,
                    "content_length": okx_d_size,
                    "host": OKX_HOST,
                },
                {
                    "venue": "OKX",
                    "role": "D+1_SOURCE_SUPPORT",
                    "filename": OKX_D1,
                    "content_length": okx_d1_size,
                    "host": OKX_HOST,
                },
                {
                    "venue": "BYBIT",
                    "role": "D",
                    "filename": BYBIT_FILE,
                    "content_length": bybit_size,
                    "host": BYBIT_HOST,
                },
            ],
            "combined_content_length": total,
            "historical_archive_body_downloaded": False,
            "historical_archive_body_opened": False,
            "cross_venue_price_compared": False,
            "cross_venue_return_calculated": False,
            "raw_spread_calculated": False,
            "dislocation_calculated": False,
            "lag_calculated": False,
            "strategy_signal_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        atomic_json(OUT, report)

        print(PASS)
        print("OKX_D_bytes =", okx_d_size)
        print("OKX_D1_bytes =", okx_d1_size)
        print("Bybit_D_bytes =", bybit_size)
        print("combined_bytes =", total)
        print("historical archive body downloaded/opened = False / False")
        print("cross-venue price/return/raw-spread/dislocation/lag = False")
        print("signal/PnL/promotional alpha = False")
        print("report =", OUT)
        return 0

    except Exception as exc:
        fail_rep = {
            "stage": STAGE,
            "version": "0.1",
            "status": REVIEW,
            "error": f"{type(exc).__name__}: {exc}",
            "historical_archive_body_downloaded": False,
            "historical_archive_body_opened": False,
            "cross_venue_price_compared": False,
            "cross_venue_return_calculated": False,
            "raw_spread_calculated": False,
            "dislocation_calculated": False,
            "lag_calculated": False,
            "strategy_signal_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
        }
        try:
            atomic_json(OUT, fail_rep)
        except Exception:
            pass

        print(REVIEW)
        print("error =", fail_rep["error"])
        print("report =", OUT)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
