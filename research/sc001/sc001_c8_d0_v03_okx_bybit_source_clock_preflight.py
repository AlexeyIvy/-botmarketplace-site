from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

STAGE = "SC001-C8-D0-V0.3-OKX-BYBIT-SOURCE-CLOCK-PREFLIGHT"
PASS = "C8_D0_V03_SOURCE_CLOCK_PREFLIGHT_PASS"
REVIEW = "C8_D0_V03_SOURCE_CLOCK_PREFLIGHT_REVIEW"

FIXED_DATE = "2025-01-15"
DAY_START_MS = 1736899200000
DAY_END_MS = 1736985600000
PREV_DAY_START_MS = 1736812800000
PREV_DAY_END_MS = 1736899200000

OKX_DOMAINS = ("https://www.okx.com", "https://us.okx.com")
OKX_INST = "BTC-USDT-SWAP"
OKX_FAMILY = "BTC-USDT"
OKX_EXPECTED_ARCHIVE = "BTC-USDT-SWAP-trades-2025-01-15.zip"
OKX_ALLOWED_ARCHIVE_HOST = "static.okx.com"

BYBIT_API = "https://api.bybit.com"
BYBIT_SYMBOL = "BTCUSDT"
BYBIT_ARCHIVE_URL = (
    "https://public.bybit.com/trading/BTCUSDT/"
    "BTCUSDT2025-01-15.csv.gz"
)
BYBIT_EXPECTED_ARCHIVE = "BTCUSDT2025-01-15.csv.gz"
BYBIT_ALLOWED_ARCHIVE_HOST = "public.bybit.com"

TIMEOUT = 45
RETRIES = 3
MAX_RESPONSE_BYTES = 4_000_000

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c8-d0-okx-bybit-source-clock-semantics-protocol-v0.3.md"
FREEZE = ROOT / "docs/research/sc001-c8-d0-v0.3-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_C8_D0_V03_SOURCE_CLOCK"
OUT = OUT_DIR / "sc001_c8_d0_v03_source_clock_preflight_v0_1.json"


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
        fail(f"missing required JSON: {path}")
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
    if fr.get("status") != "FROZEN_BEFORE_C8_D0_V03_RUN":
        fail("C8-D0 freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("C8-D0 runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("C8-D0 protocol identity mismatch")
    if fr.get("fixed_date") != FIXED_DATE:
        fail("C8-D0 fixed date mismatch")
    if fr.get("okx_instrument") != OKX_INST:
        fail("C8-D0 OKX instrument mismatch")
    if fr.get("bybit_symbol") != BYBIT_SYMBOL:
        fail("C8-D0 Bybit symbol mismatch")
    for key in (
        "historical_archive_body_authorized",
        "cross_venue_price_comparison_authorized",
        "cross_venue_return_authorized",
        "dislocation_authorized",
        "lag_authorized",
        "leader_selection_authorized",
        "strategy_signal_authorized",
        "pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(key) is not False:
            fail(f"C8-D0 firewall mismatch: {key}")
    return fr


def request_json(url: str, expected_family: str) -> tuple[dict, str, int]:
    last: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C8-D0-v0.3",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_RESPONSE_BYTES + 1)
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()

            if len(raw) > MAX_RESPONSE_BYTES:
                fail(f"response cap exceeded: {expected_family}")
            if status != 200:
                fail(f"HTTP {status}: {expected_family}")

            obj = json.loads(raw.decode("utf-8"))
            if not isinstance(obj, dict):
                fail(f"JSON object expected: {expected_family}")
            return obj, final, len(raw)
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(
        f"request failed {expected_family}: {type(last).__name__}: {last}"
    )


def plausible_ms(ts: object) -> bool:
    try:
        x = int(str(ts))
    except Exception:
        return False
    return 946684800000 <= x < 4102444800000


def okx_json(path: str, params: dict[str, str]) -> tuple[dict, str, int]:
    query = urllib.parse.urlencode(params)
    last: Exception | None = None
    for domain in OKX_DOMAINS:
        try:
            obj, final, nbytes = request_json(
                domain + path + ("?" + query if query else ""),
                "OKX",
            )
            if str(obj.get("code")) != "0":
                fail(f"OKX code mismatch: {obj.get('code')}")
            host = (urllib.parse.urlparse(final).hostname or "").lower()
            if host not in {"www.okx.com", "us.okx.com"}:
                fail(f"unexpected OKX final host: {host}")
            return obj, final, nbytes
        except Exception as exc:
            last = exc
            continue
    raise RuntimeError(f"OKX request failed: {type(last).__name__}: {last}")


def bybit_json(path: str, params: dict[str, str]) -> tuple[dict, str, int]:
    url = BYBIT_API + path + "?" + urllib.parse.urlencode(params)
    obj, final, nbytes = request_json(url, "Bybit")
    if int(obj.get("retCode", -1)) != 0:
        fail(f"Bybit retCode mismatch: {obj.get('retCode')}")
    host = (urllib.parse.urlparse(final).hostname or "").lower()
    if host not in {"api.bybit.com"}:
        fail(f"unexpected Bybit final host: {host}")
    return obj, final, nbytes


def okx_instrument() -> dict:
    obj, final, nbytes = okx_json(
        "/api/v5/public/instruments",
        {"instType": "SWAP", "instId": OKX_INST},
    )
    rows = obj.get("data") or []
    if len(rows) != 1 or not isinstance(rows[0], dict):
        fail(f"OKX instrument row mismatch count={len(rows)}")
    r = rows[0]

    checks = {
        "inst_id_exact": r.get("instId") == OKX_INST,
        "inst_type_swap": r.get("instType") == "SWAP",
        "ct_type_linear": r.get("ctType") == "linear",
        "settle_usdt": r.get("settleCcy") == "USDT",
        "uly_btc_usdt": r.get("uly") == OKX_FAMILY,
        "state_live": r.get("state") == "live",
    }
    return {
        "checks": checks,
        "pass": all(checks.values()),
        "uly": r.get("uly"),
        "ct_val_ccy": r.get("ctValCcy"),
        "response_bytes": nbytes,
        "final_host": urllib.parse.urlparse(final).hostname,
    }


def bybit_instrument() -> dict:
    obj, final, nbytes = bybit_json(
        "/v5/market/instruments-info",
        {"category": "linear", "symbol": BYBIT_SYMBOL},
    )
    result = obj.get("result") or {}
    rows = result.get("list") or []
    if len(rows) != 1 or not isinstance(rows[0], dict):
        fail(f"Bybit instrument row mismatch count={len(rows)}")
    r = rows[0]

    checks = {
        "symbol_exact": r.get("symbol") == BYBIT_SYMBOL,
        "linear_perpetual": r.get("contractType") == "LinearPerpetual",
        "base_btc": r.get("baseCoin") == "BTC",
        "quote_usdt": r.get("quoteCoin") == "USDT",
        "settle_usdt": r.get("settleCoin") == "USDT",
        "status_trading": r.get("status") == "Trading",
    }
    return {
        "checks": checks,
        "pass": all(checks.values()),
        "launch_time_ms": r.get("launchTime"),
        "response_bytes": nbytes,
        "final_host": urllib.parse.urlparse(final).hostname,
    }


def okx_trade_clock() -> dict:
    obj, final, nbytes = okx_json(
        "/api/v5/market/history-trades",
        {"instId": OKX_INST, "type": "2", "limit": "10"},
    )
    rows = obj.get("data") or []
    if not rows:
        fail("OKX current public trade schema returned no rows")

    required = {"instId", "tradeId", "side", "px", "sz", "ts"}
    row_checks = []
    for r in rows:
        if not isinstance(r, dict):
            fail("OKX trade row non-object")
        keys_ok = required.issubset(r)
        ts_ok = plausible_ms(r.get("ts"))
        inst_ok = r.get("instId") == OKX_INST
        side_ok = r.get("side") in {"buy", "sell"}
        row_checks.append(keys_ok and ts_ok and inst_ok and side_ok)

    return {
        "row_count": len(rows),
        "timestamp_unit": "unix_milliseconds",
        "required_fields": sorted(required),
        "pass": all(row_checks),
        "response_bytes": nbytes,
        "final_host": urllib.parse.urlparse(final).hostname,
    }


def bybit_trade_clock() -> dict:
    obj, final, nbytes = bybit_json(
        "/v5/market/recent-trade",
        {"category": "linear", "symbol": BYBIT_SYMBOL, "limit": "10"},
    )
    result = obj.get("result") or {}
    rows = result.get("list") or []
    if not rows:
        fail("Bybit current public trade schema returned no rows")

    required = {"execId", "symbol", "price", "size", "side", "time"}
    row_checks = []
    for r in rows:
        if not isinstance(r, dict):
            fail("Bybit trade row non-object")
        keys_ok = required.issubset(r)
        ts_ok = plausible_ms(r.get("time"))
        symbol_ok = r.get("symbol") == BYBIT_SYMBOL
        side_ok = r.get("side") in {"Buy", "Sell"}
        row_checks.append(keys_ok and ts_ok and symbol_ok and side_ok)

    return {
        "row_count": len(rows),
        "timestamp_unit": "unix_milliseconds",
        "required_fields": sorted(required),
        "pass": all(row_checks),
        "response_bytes": nbytes,
        "final_host": urllib.parse.urlparse(final).hostname,
    }


def walk_nodes(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk_nodes(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk_nodes(value)


def trusted_okx_archive(url: str) -> bool:
    try:
        p = urllib.parse.urlparse(url)
        return (
            p.scheme == "https"
            and (p.hostname or "").lower() == OKX_ALLOWED_ARCHIVE_HOST
            and Path(p.path).name == OKX_EXPECTED_ARCHIVE
        )
    except Exception:
        return False


def okx_archive_metadata() -> dict:
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

    attempts: list[dict] = []
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    for domain in OKX_DOMAINS:
        url = (
            domain
            + "/priapi/v5/broker/public/trade-data/download-link"
            + "?t="
            + str(int(time.time() * 1000))
        )
        last: Exception | None = None

        for attempt in range(1, RETRIES + 1):
            try:
                req = urllib.request.Request(
                    url,
                    data=body,
                    method="POST",
                    headers={
                        "User-Agent": "BotMarketplace-SC001-C8-D0-v0.3",
                        "Accept": "application/json,*/*",
                        "Content-Type": "application/json",
                        "Referer": "https://www.okx.com/historical-data",
                    },
                )
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    raw = resp.read(MAX_RESPONSE_BYTES + 1)
                    status = int(getattr(resp, "status", 200))
                    final = resp.geturl()

                if len(raw) > MAX_RESPONSE_BYTES:
                    fail("OKX priapi metadata response cap exceeded")
                if status != 200:
                    fail(f"OKX priapi HTTP {status}")

                parsed = urllib.parse.urlparse(final)
                if (
                    parsed.scheme != "https"
                    or (parsed.hostname or "").lower()
                    not in {"www.okx.com", "us.okx.com"}
                ):
                    fail(f"unexpected OKX priapi final host: {parsed.hostname}")

                obj = json.loads(raw.decode("utf-8"))
                if not isinstance(obj, dict) or str(obj.get("code")) != "0":
                    fail(
                        f"OKX priapi code mismatch: "
                        f"{obj.get('code') if isinstance(obj, dict) else None}"
                    )

                found: list[str] = []
                for node in walk_nodes(obj.get("data")):
                    if not isinstance(node, dict):
                        continue
                    fn = node.get("filename") or node.get("fileName")
                    u = node.get("url")
                    if (
                        fn == OKX_EXPECTED_ARCHIVE
                        and isinstance(u, str)
                        and trusted_okx_archive(u)
                        and u not in found
                    ):
                        found.append(u)

                attempts.append(
                    {
                        "domain": domain,
                        "http_status": status,
                        "response_bytes": len(raw),
                        "exact_trusted_url_count": len(found),
                    }
                )

                if not found:
                    break

                if len(found) != 1:
                    fail(
                        f"OKX priapi exact archive resolution count={len(found)} "
                        f"expected={OKX_EXPECTED_ARCHIVE}"
                    )

                size, final_url = head_exact(
                    found[0],
                    OKX_ALLOWED_ARCHIVE_HOST,
                    OKX_EXPECTED_ARCHIVE,
                    "OKX historical archive",
                )

                return {
                    "filename": OKX_EXPECTED_ARCHIVE,
                    "content_length": size,
                    "host": urllib.parse.urlparse(final_url).hostname,
                    "resolver": "priapi_trade_data_download_link",
                    "selected_domain": domain,
                    "attempts": attempts,
                    "pass": True,
                }

            except Exception as exc:
                last = exc
                if attempt < RETRIES:
                    time.sleep(float(attempt))
                    continue
                attempts.append(
                    {
                        "domain": domain,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

    fail(
        "OKX exact historical archive unresolved via frozen priapi resolver "
        f"expected={OKX_EXPECTED_ARCHIVE}; attempts={attempts}"
    )


def head_exact(
    url: str,
    allowed_host: str,
    expected_basename: str,
    label: str,
) -> tuple[int, str]:
    last: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": "BotMarketplace-SC001-C8-D0/0.1"},
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
                cl = resp.headers.get("Content-Length")
            p = urllib.parse.urlparse(final)
            if status != 200:
                fail(f"{label} HEAD HTTP {status}")
            if p.scheme != "https" or (p.hostname or "").lower() != allowed_host:
                fail(f"{label} HEAD host mismatch: {p.hostname}")
            if Path(p.path).name != expected_basename:
                fail(f"{label} basename mismatch: {Path(p.path).name}")
            if not cl or not cl.isdigit() or int(cl) <= 0:
                fail(f"{label} invalid Content-Length")
            return int(cl), final
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"{label} HEAD failed: {type(last).__name__}: {last}")


def bybit_archive_metadata() -> dict:
    size, final = head_exact(
        BYBIT_ARCHIVE_URL,
        BYBIT_ALLOWED_ARCHIVE_HOST,
        BYBIT_EXPECTED_ARCHIVE,
        "Bybit historical archive",
    )
    return {
        "filename": BYBIT_EXPECTED_ARCHIVE,
        "content_length": size,
        "host": urllib.parse.urlparse(final).hostname,
        "pass": True,
    }


def main() -> int:
    require_freeze()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    checks: dict[str, dict] = {}
    errors: list[str] = []

    for name, fn in (
        ("okx_instrument", okx_instrument),
        ("bybit_instrument", bybit_instrument),
        ("okx_current_trade_clock", okx_trade_clock),
        ("bybit_current_trade_clock", bybit_trade_clock),
        ("okx_historical_archive", okx_archive_metadata),
        ("bybit_historical_archive", bybit_archive_metadata),
    ):
        print(f"C8-D0 {name} ...", flush=True)
        try:
            rec = fn()
            checks[name] = rec
            if rec.get("pass") is not True:
                errors.append(f"{name}: semantic checks did not pass")
                print(f"REVIEW {name}", flush=True)
            else:
                print(f"PASS {name}", flush=True)
        except Exception as exc:
            msg = f"{name}: {type(exc).__name__}: {exc}"
            errors.append(msg)
            checks[name] = {"pass": False, "error": msg}
            print(f"REVIEW {msg}", flush=True)

    status = PASS if not errors and len(checks) == 6 else REVIEW

    report = {
        "stage": STAGE,
        "version": "0.3",
        "status": status,
        "venue_pair": ["OKX", "BYBIT"],
        "instrument_pair": [OKX_INST, BYBIT_SYMBOL],
        "fixed_historical_qualification_date": FIXED_DATE,
        "checks": checks,
        "errors": errors,
        "historical_archive_body_downloaded": False,
        "historical_archive_body_opened": False,
        "cross_venue_price_compared": False,
        "cross_venue_return_calculated": False,
        "dislocation_calculated": False,
        "lag_calculated": False,
        "leader_selected": False,
        "strategy_signal_calculated": False,
        "pnl_calculated": False,
        "promotional_alpha_accessed": False,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    atomic_json(OUT, report)

    print(status)
    print("checks_passed =", sum(1 for x in checks.values() if x.get("pass") is True), "/ 6")
    print("historical archive body downloaded/opened = False / False")
    print("cross-venue price/return/dislocation/lag = False")
    print("leader/signal/PnL selected or calculated = False")
    print("promotional alpha accessed = False")
    print("report =", OUT)

    return 0 if status == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
