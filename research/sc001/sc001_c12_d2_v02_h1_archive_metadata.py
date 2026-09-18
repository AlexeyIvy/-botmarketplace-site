from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

STAGE = "SC001-C12-D2-V0.2-H1-ARCHIVE-METADATA"
PASS = "C12_D2_V02_H1_ARCHIVE_METADATA_PASS"
REVIEW = "C12_D2_V02_H1_ARCHIVE_METADATA_REVIEW"

START = date(2025, 1, 1)
END = date(2025, 7, 1)
INST = "USDC-USDT"

OKX_DOMAINS = ("https://www.okx.com", "https://us.okx.com")
STATIC = "static.okx.com"

TIMEOUT = 60
MAX_JSON = 4_000_000
MIN_HTTP_GAP_SEC = 1.5
MAX_ATTEMPTS = 8
BACKOFF_BASE_SEC = 15
BACKOFF_MAX_SEC = 240

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-c12-d2-h1-archive-metadata-protocol-v0.2.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.16.json"
FREEZE = ROOT / "docs/research/sc001-c12-d2-v0.2-implementation-freeze-v0.1.json"

DATA_ROOT = Path(
    os.environ.get("SC001_DATA_ROOT", str(Path.home() / "sc001_data"))
).expanduser().resolve()

D1 = (
    DATA_ROOT / "SC001_C12_D1_SPOT_SEMANTICS"
    / "sc001_c12_d1_spot_trade_semantics_report_v0_1.json"
)

OUT_DIR = DATA_ROOT / "SC001_C12_D2_V02_H1_METADATA"
OUT = OUT_DIR / "sc001_c12_d2_v02_h1_archive_metadata_report_v0_1.json"
CHECKPOINT = OUT_DIR / "sc001_c12_d2_v02_checkpoint.json"

_last_http_monotonic = 0.0


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"missing JSON: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"JSON object expected: {path}")
    return obj


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def git_blob(path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "hash-object", str(path.relative_to(ROOT))],
        text=True,
    ).strip()


def require_freeze() -> None:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_C12_D2_V02_RUN":
        fail("freeze status mismatch")
    if fr.get("runner_git_blob_sha") != git_blob(Path(__file__).resolve()):
        fail("runner identity mismatch")
    if fr.get("protocol_git_blob_sha") != git_blob(PROTOCOL):
        fail("protocol identity mismatch")
    if fr.get("contamination_registry_git_blob_sha") != git_blob(REGISTRY):
        fail("registry identity mismatch")
    if int(fr.get("required_archive_count", 0)) != 182:
        fail("archive count mismatch")
    if float(fr.get("min_http_gap_sec", -1)) != MIN_HTTP_GAP_SEC:
        fail("HTTP gap mismatch")
    if int(fr.get("max_attempts", 0)) != MAX_ATTEMPTS:
        fail("retry budget mismatch")

    for k in (
        "historical_trade_body_authorized",
        "peg_deviation_authorized",
        "reversion_outcome_authorized",
        "threshold_selection_authorized",
        "strategy_signal_authorized",
        "pnl_authorized",
        "promotional_alpha_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"firewall mismatch {k}")

    d1 = load_json(D1)
    if d1.get("status") != "C12_D1_SPOT_TRADE_SEMANTICS_PASS":
        fail("D1 not PASS")


def walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


def day_ms(d: date) -> tuple[int, int]:
    dt = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
    begin = int(dt.timestamp() * 1000)
    return begin, begin + 86_400_000


def trusted(url: str, basename: str) -> bool:
    p = urllib.parse.urlparse(url)
    return (
        p.scheme == "https"
        and (p.hostname or "").lower() == STATIC
        and Path(p.path).name == basename
    )


def pace() -> None:
    global _last_http_monotonic
    now = time.monotonic()
    wait = MIN_HTTP_GAP_SEC - (now - _last_http_monotonic)
    if wait > 0:
        time.sleep(wait)
    _last_http_monotonic = time.monotonic()


def backoff_seconds(exc: urllib.error.HTTPError, attempt: int) -> int:
    ra = exc.headers.get("Retry-After") if exc.headers is not None else None
    if ra is not None:
        try:
            n = int(ra)
            if n > 0:
                return min(max(n, BACKOFF_BASE_SEC), BACKOFF_MAX_SEC)
        except Exception:
            pass
    return min(BACKOFF_BASE_SEC * (2 ** (attempt - 1)), BACKOFF_MAX_SEC)


def open_with_backoff(req_factory, label: str, read_cap: int | None = None):
    last = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            pace()
            req = req_factory()
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
                headers = dict(resp.headers.items())
                raw = None
                if read_cap is not None:
                    raw = resp.read(read_cap + 1)
                    if len(raw) > read_cap:
                        fail(f"{label} response cap exceeded")
            return status, final, headers, raw

        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code != 429:
                if attempt >= MAX_ATTEMPTS:
                    break
                time.sleep(min(5 * attempt, 30))
                continue

            wait = backoff_seconds(exc, attempt)
            print(
                f"RATE_LIMIT {label} attempt={attempt}/{MAX_ATTEMPTS} "
                f"sleep={wait}s",
                flush=True,
            )
            time.sleep(wait)

        except Exception as exc:
            last = exc
            if attempt < MAX_ATTEMPTS:
                wait = min(5 * attempt, 30)
                print(
                    f"RETRY {label} attempt={attempt}/{MAX_ATTEMPTS} "
                    f"sleep={wait}s error={type(exc).__name__}",
                    flush=True,
                )
                time.sleep(wait)

    raise RuntimeError(
        f"{label} failed after {MAX_ATTEMPTS} attempts: "
        f"{type(last).__name__}: {last}"
    )


def resolve(d: date) -> tuple[str, str]:
    ds = d.isoformat()
    basename = f"{INST}-trades-{ds}.zip"
    begin, end = day_ms(d)

    payload = {
        "module": "1",
        "instType": "SPOT",
        "instQueryParam": {"instIdList": [INST]},
        "dateQuery": {
            "dateAggrType": "daily",
            "begin": str(begin),
            "end": str(end - 1),
        },
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    last = None

    for domain in OKX_DOMAINS:
        def make_req(domain=domain):
            return urllib.request.Request(
                domain
                + "/priapi/v5/broker/public/trade-data/download-link?t="
                + str(int(time.time() * 1000)),
                data=body,
                method="POST",
                headers={
                    "User-Agent": "BotMarketplace-SC001-C12-D2-v0.2",
                    "Accept": "application/json,*/*",
                    "Content-Type": "application/json",
                    "Referer": "https://www.okx.com/historical-data",
                },
            )

        try:
            status, final, _headers, raw = open_with_backoff(
                make_req,
                f"resolve {ds} {domain}",
                MAX_JSON,
            )
            if status != 200:
                fail(f"metadata HTTP {status} {ds}")

            host = (urllib.parse.urlparse(final).hostname or "").lower()
            if host not in {"www.okx.com", "us.okx.com"}:
                fail(f"unexpected metadata host {host}")

            obj = json.loads(raw.decode("utf-8"))
            if str(obj.get("code")) != "0":
                fail(f"metadata code mismatch {ds}: {obj.get('code')}")

            found = []
            for node in walk(obj.get("data")):
                if not isinstance(node, dict):
                    continue
                fn = node.get("filename") or node.get("fileName")
                u = node.get("url")
                if (
                    fn == basename
                    and isinstance(u, str)
                    and trusted(u, basename)
                    and u not in found
                ):
                    found.append(u)

            if len(found) == 1:
                return basename, found[0]
            if len(found) > 1:
                fail(f"multiple exact URLs {ds}")

            last = RuntimeError(f"exact archive missing {ds}")

        except Exception as exc:
            last = exc

    raise RuntimeError(
        f"resolve failed {ds}: {type(last).__name__}: {last}"
    )


def head(url: str, basename: str) -> int:
    def make_req():
        return urllib.request.Request(
            url,
            method="HEAD",
            headers={
                "User-Agent": "BotMarketplace-SC001-C12-D2-v0.2",
                "Referer": "https://www.okx.com/historical-data",
            },
        )

    status, final, headers, _raw = open_with_backoff(
        make_req,
        f"HEAD {basename}",
        None,
    )

    if status != 200:
        fail(f"HEAD HTTP {status}: {basename}")
    if not trusted(final, basename):
        fail(f"HEAD identity mismatch: {basename}")

    cl = headers.get("Content-Length")
    if not cl or not cl.isdigit() or int(cl) <= 0:
        fail(f"invalid Content-Length: {basename}")

    return int(cl)


def expected_dates() -> list[date]:
    out = []
    d = START
    while d <= END:
        out.append(d)
        d += timedelta(days=1)
    if len(out) != 182:
        fail(f"internal date-count mismatch: {len(out)}")
    return out


def load_checkpoint() -> dict[str, dict]:
    if not CHECKPOINT.exists():
        return {}

    obj = load_json(CHECKPOINT)
    if obj.get("stage") != STAGE or obj.get("version") != "0.2":
        fail("checkpoint stage/version mismatch")
    if obj.get("source_window") != "2025-01-01_to_2025-07-01":
        fail("checkpoint window mismatch")

    rows = obj.get("verified") or []
    if not isinstance(rows, list):
        fail("checkpoint verified list invalid")

    expected = {d.isoformat() for d in expected_dates()}
    out = {}

    for row in rows:
        if not isinstance(row, dict):
            fail("checkpoint row invalid")
        ds = row.get("date")
        fn = row.get("filename")
        size = row.get("content_length")

        if ds not in expected:
            fail(f"checkpoint unexpected date {ds}")
        if fn != f"{INST}-trades-{ds}.zip":
            fail(f"checkpoint filename mismatch {ds}")
        if not isinstance(size, int) or size <= 0:
            fail(f"checkpoint size invalid {ds}")
        if ds in out:
            fail(f"checkpoint duplicate date {ds}")

        out[ds] = {
            "date": ds,
            "filename": fn,
            "content_length": size,
        }

    return out


def save_checkpoint(rows_by_date: dict[str, dict]) -> None:
    ordered = [rows_by_date[d.isoformat()] for d in expected_dates() if d.isoformat() in rows_by_date]

    atomic_json(
        CHECKPOINT,
        {
            "stage": STAGE,
            "version": "0.2",
            "source_window": "2025-01-01_to_2025-07-01",
            "verified_count": len(ordered),
            "verified": ordered,
        },
    )


def main() -> int:
    try:
        require_freeze()
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        verified = load_checkpoint()

        if verified:
            print(
                f"C12-D2 v0.2 RESUME checkpoint_verified={len(verified)}/182",
                flush=True,
            )
        else:
            print("C12-D2 v0.2 START fresh", flush=True)

        dates = expected_dates()

        for i, d in enumerate(dates, start=1):
            ds = d.isoformat()

            if ds in verified:
                if i == 1 or i % 10 == 0 or i == len(dates):
                    print(f"C12-D2 v0.2 [{i}/182] {ds} CHECKPOINT", flush=True)
                continue

            print(f"C12-D2 v0.2 [{i}/182] {ds}", flush=True)

            basename, url = resolve(d)
            size = head(url, basename)

            verified[ds] = {
                "date": ds,
                "filename": basename,
                "content_length": size,
            }
            save_checkpoint(verified)

            print(
                f"PASS {ds} bytes={size} checkpoint={len(verified)}/182",
                flush=True,
            )

        ordered = [verified[d.isoformat()] for d in dates]

        if len(ordered) != 182:
            fail(f"final archive count mismatch: {len(ordered)}")

        report = {
            "stage": STAGE,
            "version": "0.2",
            "status": PASS,
            "target_window": "2025-01-01_to_2025-06-30",
            "source_archive_window": "2025-01-01_to_2025-07-01",
            "archives": ordered,
            "archive_count": len(ordered),
            "combined_head_content_length": sum(
                x["content_length"] for x in ordered
            ),
            "request_policy": {
                "min_http_gap_sec": MIN_HTTP_GAP_SEC,
                "max_attempts": MAX_ATTEMPTS,
                "backoff_base_sec": BACKOFF_BASE_SEC,
                "backoff_max_sec": BACKOFF_MAX_SEC,
                "checkpoint_resume": True,
            },
            "historical_trade_body_downloaded": False,
            "historical_trade_body_opened": False,
            "peg_deviation_calculated": False,
            "reversion_outcome_calculated": False,
            "threshold_selected": False,
            "strategy_signal_calculated": False,
            "pnl_calculated": False,
            "promotional_alpha_accessed": False,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }

        atomic_json(OUT, report)

        print(PASS)
        print("archives_verified =", len(ordered), "/ 182")
        print(
            "combined_HEAD_content_length =",
            report["combined_head_content_length"],
        )
        print("historical trade body downloaded/opened = False / False")
        print("peg deviation/reversion/threshold/signal/PnL = False")
        print("promotional alpha accessed = False")
        print("report =", OUT)
        return 0

    except Exception as exc:
        print(REVIEW)
        print("error =", f"{type(exc).__name__}: {exc}")
        print(
            "checkpoint =",
            CHECKPOINT,
            "(safe to resume with same frozen v0.2 runner)",
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
