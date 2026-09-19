from __future__ import annotations

import bisect
import csv
import hashlib
import io
import json
import math
import os
import statistics
import subprocess
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

STAGE = "SC001-B13A-FUNDING-DIFFERENTIAL-STRUCTURAL-PREFLIGHT-V0.1"
SURVIVE = "B13A_STRUCTURAL_PREFLIGHT_SURVIVE"
REJECT = "B13A_REJECT_STRUCTURAL"
DEFER = "B13A_DEFER_SOURCE_OR_SAMPLE"

SYMBOLS = ("BTC","ETH","SOL","DOGE","ORDI","FIL","UNI","XRP","LTC","OP","BCH","SUI")
START_MS = int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)
END_MS_EXCL = int(datetime(2025,7,1,tzinfo=timezone.utc).timestamp()*1000)

# OKX monthly historical archives use UTC+8 calendar-month boundaries.
ARCHIVE_BEGIN_MS = int(datetime(2024,12,31,16,tzinfo=timezone.utc).timestamp()*1000)
ARCHIVE_END_MS = int(datetime(2025,7,1,16,tzinfo=timezone.utc).timestamp()*1000)

MATCH_TOLERANCE_MS = 5 * 60 * 1000
STRUCTURAL_BURDEN_BPS = 40.0
QUALIFYING_DIFF_BPS = 50.0

MIN_SOURCE_ELIGIBLE = 8
MIN_MATCH_MONTHS = 4
MIN_MATCHED_TOTAL = 500
MIN_QUALIFYING = 12
MIN_QUAL_DATES = 8
MIN_QUAL_MONTHS = 3
MIN_QUAL_SYMBOLS = 4
MAX_SINGLE_SYMBOL_QUAL_SHARE = 0.50

OKX_BASE = "https://www.okx.com"
OKX_STATIC = "static.okx.com"
BYBIT_BASE = "https://api.bybit.com"
TIMEOUT = 60
RETRIES = 4
MAX_JSON = 5_000_000
MAX_OKX_FILE = 20 * 1024 * 1024
MAX_OKX_TOTAL = 250 * 1024 * 1024
MAX_BYBIT_PAGES_PER_SYMBOL = 40
CHUNK = 1024 * 1024

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/research/sc001-b13a-funding-differential-structural-preflight-v0.1.md"
SEMANTICS = ROOT / "docs/research/sc001-b13a-funding-source-sign-semantics-freeze-v0.1.md"
REGISTRY = ROOT / "docs/research/sc001-contamination-registry-v0.22.json"
UNIVERSE = ROOT / "docs/research/sc001-first-generation-multi-asset-universe-freeze-v1.0.json"
FREEZE = ROOT / "docs/research/sc001-b13a-funding-differential-implementation-freeze-v0.1.json"

DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR = DATA_ROOT / "SC001_B13A_FUNDING_PREFLIGHT"
OKX_ARCH = OUT_DIR / "okx_archives"
OUT = OUT_DIR / "sc001_b13a_funding_differential_structural_preflight_v0_1.json"

def fail(msg: str) -> None:
    raise RuntimeError(msg)

def load_json(path: Path) -> dict:
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
        ["git","-C",str(ROOT),"hash-object",str(path.relative_to(ROOT))],
        text=True,
    ).strip()

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8*1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def finite_decimal(text: str) -> Decimal:
    try:
        x = Decimal(str(text).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid decimal: {text!r}") from exc
    if not x.is_finite():
        raise ValueError(f"non-finite decimal: {text!r}")
    return x

def require_freeze() -> None:
    fr = load_json(FREEZE)
    if fr.get("status") != "FROZEN_BEFORE_B13A_STRUCTURAL_PREFLIGHT_RUN":
        fail("freeze status mismatch")
    expected = {
        "runner_git_blob_sha": git_blob(Path(__file__).resolve()),
        "protocol_git_blob_sha": git_blob(PROTOCOL),
        "source_semantics_git_blob_sha": git_blob(SEMANTICS),
        "contamination_registry_git_blob_sha": git_blob(REGISTRY),
        "universe_git_blob_sha": git_blob(UNIVERSE),
    }
    for key, value in expected.items():
        if fr.get(key) != value:
            fail(f"freeze identity mismatch: {key}")

    if float(fr.get("structural_burden_bps",-1)) != STRUCTURAL_BURDEN_BPS:
        fail("structural burden mismatch")
    if float(fr.get("qualifying_diff_bps",-1)) != QUALIFYING_DIFF_BPS:
        fail("qualifying differential mismatch")
    if int(fr.get("match_tolerance_ms",-1)) != MATCH_TOLERANCE_MS:
        fail("match tolerance mismatch")

    reg = load_json(REGISTRY).get("b13a_funding_structural_calibration") or {}
    if reg.get("funding_values_access_authorized") is not True:
        fail("funding value access not authorized")
    if reg.get("funding_timestamps_access_authorized") is not True:
        fail("funding timestamp access not authorized")
    for key in (
        "price_access_authorized","basis_access_authorized","trade_body_access_authorized",
        "l2_access_authorized","strategy_price_pnl_authorized","promotional_evidence_authorized"
    ):
        if reg.get(key) is not False:
            fail(f"contamination firewall mismatch: {key}")

    u = load_json(UNIVERSE)
    frozen = tuple(x.get("symbol") for x in u.get("universe_ranked",[]))
    if frozen != SYMBOLS:
        fail(f"frozen universe mismatch: {frozen}")

def request_json(url: str, label: str) -> dict:
    last = None
    for attempt in range(1, RETRIES+1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent":"BotMarketplace-SC001-B13A/0.1",
                "Accept":"application/json",
            })
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                raw = resp.read(MAX_JSON+1)
            if len(raw) > MAX_JSON:
                fail(f"{label} response exceeds cap")
            return json.loads(raw.decode("utf-8"))
        except Exception as exc:
            last = exc
            if attempt < RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"{label} request failed: {type(last).__name__}: {last}")

def okx_get(path: str, params: dict[str,str]) -> dict:
    url = OKX_BASE + path + "?" + urllib.parse.urlencode(params)
    obj = request_json(url, "OKX")
    if not isinstance(obj,dict) or str(obj.get("code")) != "0":
        fail(f"OKX response code mismatch: {obj!r}")
    return obj

def bybit_get(path: str, params: dict[str,str]) -> dict:
    url = BYBIT_BASE + path + "?" + urllib.parse.urlencode(params)
    obj = request_json(url, "Bybit")
    if not isinstance(obj,dict) or int(obj.get("retCode",-1)) != 0:
        fail(f"Bybit response code mismatch: {obj!r}")
    return obj

def trusted_okx_archive(url: str, filename: str) -> bool:
    p = urllib.parse.urlparse(url)
    return (
        p.scheme == "https"
        and (p.hostname or "").lower() == OKX_STATIC
        and Path(p.path).name == filename
    )

def okx_archive_metadata(symbol: str) -> list[dict]:
    family = f"{symbol}-USDT"
    obj = okx_get("/api/v5/public/market-data-history", {
        "module":"3",
        "instType":"SWAP",
        "instFamilyList":family,
        "dateAggrType":"monthly",
        "begin":str(ARCHIVE_BEGIN_MS),
        "end":str(ARCHIVE_END_MS),
    })
    data = obj.get("data")
    details = data.get("details") if isinstance(data,dict) else None
    if not isinstance(details,list):
        fail(f"OKX funding metadata details missing for {symbol}")

    files = {}
    for detail in details:
        groups = detail.get("groupDetails") if isinstance(detail,dict) else None
        if not isinstance(groups,list):
            continue
        for g in groups:
            if not isinstance(g,dict):
                continue
            filename = g.get("filename") or g.get("fileName")
            url = g.get("url")
            if not isinstance(filename,str) or not isinstance(url,str):
                continue
            if not trusted_okx_archive(url,filename):
                fail(f"untrusted OKX archive identity {symbol}: {filename} {url}")
            prev = files.get(filename)
            if prev is not None and prev["url"] != url:
                fail(f"conflicting OKX archive URL {filename}")
            files[filename] = {"filename":filename,"url":url,"sizeMB_raw":g.get("sizeMB")}

    return [files[k] for k in sorted(files)]

def download_okx(meta: dict) -> dict:
    filename = meta["filename"]
    url = meta["url"]
    dest = OKX_ARCH / filename
    OKX_ARCH.mkdir(parents=True,exist_ok=True)

    if dest.exists():
        size = dest.stat().st_size
        if size <= 0 or size > MAX_OKX_FILE:
            fail(f"bad reused OKX archive size {filename}: {size}")
        return {**meta,"path":str(dest),"bytes":size,"sha256":sha256_file(dest),"reused":True}

    tmp = Path(str(dest)+".part")
    tmp.unlink(missing_ok=True)
    req = urllib.request.Request(url,headers={
        "User-Agent":"BotMarketplace-SC001-B13A/0.1",
        "Referer":"https://www.okx.com/historical-data",
    })
    got = 0
    h = hashlib.sha256()
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp, tmp.open("wb") as f:
        final = resp.geturl()
        if not trusted_okx_archive(final,filename):
            fail(f"OKX archive redirect mismatch: {final}")
        while True:
            chunk = resp.read(CHUNK)
            if not chunk:
                break
            got += len(chunk)
            if got > MAX_OKX_FILE:
                fail(f"OKX archive file cap exceeded: {filename}")
            f.write(chunk)
            h.update(chunk)
        f.flush()
        os.fsync(f.fileno())
    if got <= 0:
        fail(f"empty OKX archive: {filename}")
    os.replace(tmp,dest)
    return {**meta,"path":str(dest),"bytes":got,"sha256":h.hexdigest(),"reused":False}

def parse_okx_funding(symbol: str, archives: list[dict]) -> list[dict]:
    inst = f"{symbol}-USDT-SWAP"
    by_ts = {}

    for meta in archives:
        path = Path(meta["path"])
        with zipfile.ZipFile(path) as z:
            bad = z.testzip()
            if bad is not None:
                fail(f"OKX ZIP CRC failure {path.name}: {bad}")
            members = [x for x in z.infolist() if not x.is_dir()]
            if not members:
                fail(f"OKX funding ZIP has no regular member: {path.name}")

            for info in members:
                if info.file_size > 100_000_000:
                    fail(f"OKX funding member cap exceeded: {info.filename}")
                with z.open(info) as raw:
                    reader = csv.reader(io.TextIOWrapper(raw,encoding="utf-8",newline=""))
                    for fields in reader:
                        if not fields:
                            continue
                        if fields[0] == "instrument_name":
                            if fields[:3] != ["instrument_name","funding_rate","funding_time"]:
                                fail(f"unexpected OKX funding header {path.name}: {fields}")
                            continue
                        if fields[0] != inst:
                            continue
                        if len(fields) != 3:
                            fail(f"unexpected OKX target funding row width {path.name}: {fields}")
                        rate = finite_decimal(fields[1])
                        ts = int(fields[2].strip())
                        if not (START_MS <= ts < END_MS_EXCL):
                            continue
                        prev = by_ts.get(ts)
                        row = {"timestamp_ms":ts,"rate":rate}
                        if prev is not None and prev["rate"] != rate:
                            fail(f"conflicting OKX funding duplicate {symbol} {ts}")
                        by_ts[ts] = row

    return [by_ts[k] for k in sorted(by_ts)]

def fetch_bybit_funding(symbol: str) -> list[dict]:
    market_symbol = f"{symbol}USDT"
    rows = {}
    end = END_MS_EXCL - 1

    for page_no in range(1,MAX_BYBIT_PAGES_PER_SYMBOL+1):
        obj = bybit_get("/v5/market/funding/history", {
            "category":"linear",
            "symbol":market_symbol,
            "endTime":str(end),
            "limit":"200",
        })
        page = (obj.get("result") or {}).get("list") or []
        if not isinstance(page,list):
            fail(f"Bybit funding list malformed {symbol}")

        if not page:
            break

        oldest = None
        for item in page:
            if item.get("symbol") != market_symbol:
                fail(f"Bybit symbol mismatch {symbol}: {item.get('symbol')}")
            ts = int(str(item.get("fundingRateTimestamp")).strip())
            rate = finite_decimal(item.get("fundingRate"))
            oldest = ts if oldest is None else min(oldest,ts)
            if START_MS <= ts < END_MS_EXCL:
                prev = rows.get(ts)
                if prev is not None and prev["rate"] != rate:
                    fail(f"conflicting Bybit funding duplicate {symbol} {ts}")
                rows[ts] = {"timestamp_ms":ts,"rate":rate}

        if oldest is None or oldest < START_MS or len(page) < 200:
            break
        end = oldest - 1
    else:
        fail(f"Bybit funding pagination cap reached for {symbol}")

    return [rows[k] for k in sorted(rows)]

def match_funding(okx: list[dict], bybit: list[dict]) -> list[dict]:
    bt = [x["timestamp_ms"] for x in bybit]
    candidates = []

    for oi,o in enumerate(okx):
        pos = bisect.bisect_left(bt,o["timestamp_ms"])
        for bj in (pos-1,pos,pos+1):
            if 0 <= bj < len(bybit):
                skew = abs(o["timestamp_ms"] - bybit[bj]["timestamp_ms"])
                if skew <= MATCH_TOLERANCE_MS:
                    candidates.append((skew,o["timestamp_ms"],bybit[bj]["timestamp_ms"],oi,bj))

    candidates.sort()
    used_o=set(); used_b=set(); out=[]
    for skew,ots,bts,oi,bj in candidates:
        if oi in used_o or bj in used_b:
            continue
        used_o.add(oi); used_b.add(bj)
        o=okx[oi]; b=bybit[bj]
        diff_bps=float(abs(o["rate"]-b["rate"])*Decimal(10000))
        out.append({
            "okx_timestamp_ms":o["timestamp_ms"],
            "bybit_timestamp_ms":b["timestamp_ms"],
            "skew_ms":skew,
            "okx_rate":format(o["rate"],"f"),
            "bybit_rate":format(b["rate"],"f"),
            "gross_funding_diff_bps":diff_bps,
        })

    out.sort(key=lambda x:(x["okx_timestamp_ms"],x["bybit_timestamp_ms"]))
    return out

def nr(vals: list[float], q: float):
    if not vals:
        return None
    s=sorted(vals)
    idx=max(0,min(len(s)-1,math.ceil(q*len(s))-1))
    return s[idx]

def main() -> int:
    try:
        require_freeze()
        OUT_DIR.mkdir(parents=True,exist_ok=True)

        per_symbol={}
        all_matches=[]
        total_okx_bytes=0

        for i,symbol in enumerate(SYMBOLS,1):
            print(f"B13-A [{i}/12] {symbol} source/funding",flush=True)

            metas=okx_archive_metadata(symbol)
            downloaded=[]
            for meta in metas:
                d=download_okx(meta)
                total_okx_bytes += int(d["bytes"])
                if total_okx_bytes > MAX_OKX_TOTAL:
                    fail(f"OKX total archive cap exceeded: {total_okx_bytes}")
                downloaded.append(d)

            okx_rows=parse_okx_funding(symbol,downloaded)
            bybit_rows=fetch_bybit_funding(symbol)
            matches=match_funding(okx_rows,bybit_rows)

            eligible=bool(okx_rows and bybit_rows)
            for m in matches:
                m["symbol"]=symbol
            all_matches.extend(matches)

            per_symbol[symbol]={
                "source_eligible":eligible,
                "okx_archive_files":[x["filename"] for x in downloaded],
                "okx_archive_bytes":sum(int(x["bytes"]) for x in downloaded),
                "okx_funding_rows":len(okx_rows),
                "bybit_funding_rows":len(bybit_rows),
                "matched_settlements":len(matches),
                "qualifying_ge50bps":sum(1 for x in matches if x["gross_funding_diff_bps"]>=QUALIFYING_DIFF_BPS),
            }

            print(
                f"  eligible={eligible} okx={len(okx_rows)} bybit={len(bybit_rows)} "
                f"matched={len(matches)} ge50={per_symbol[symbol]['qualifying_ge50bps']}",
                flush=True,
            )

        source_eligible=[s for s,v in per_symbol.items() if v["source_eligible"]]
        months=sorted({
            datetime.fromtimestamp(x["okx_timestamp_ms"]/1000,tz=timezone.utc).strftime("%Y-%m")
            for x in all_matches
        })

        data_gates={
            "source_eligible_gte8":len(source_eligible)>=MIN_SOURCE_ELIGIBLE,
            "matched_months_gte4":len(months)>=MIN_MATCH_MONTHS,
            "matched_settlements_gte500":len(all_matches)>=MIN_MATCHED_TOTAL,
        }

        rates=[x["gross_funding_diff_bps"] for x in all_matches]
        qualifying=[x for x in all_matches if x["gross_funding_diff_bps"]>=QUALIFYING_DIFF_BPS]

        if not all(data_gates.values()):
            status=DEFER
            structural_gates=None
        else:
            q_dates=sorted({
                datetime.fromtimestamp(x["okx_timestamp_ms"]/1000,tz=timezone.utc).strftime("%Y-%m-%d")
                for x in qualifying
            })
            q_months=sorted({
                datetime.fromtimestamp(x["okx_timestamp_ms"]/1000,tz=timezone.utc).strftime("%Y-%m")
                for x in qualifying
            })
            q_symbols=sorted({x["symbol"] for x in qualifying})
            symbol_counts={s:sum(1 for x in qualifying if x["symbol"]==s) for s in SYMBOLS}
            top=max(symbol_counts.values()) if symbol_counts else 0
            top_share=(top/len(qualifying)) if qualifying else None

            structural_gates={
                "qualifying_events_gte12":len(qualifying)>=MIN_QUALIFYING,
                "qualifying_dates_gte8":len(q_dates)>=MIN_QUAL_DATES,
                "qualifying_months_gte3":len(q_months)>=MIN_QUAL_MONTHS,
                "qualifying_symbols_gte4":len(q_symbols)>=MIN_QUAL_SYMBOLS,
                "single_symbol_share_le50pct":top_share is not None and top_share<=MAX_SINGLE_SYMBOL_QUAL_SHARE,
            }
            status=SURVIVE if all(structural_gates.values()) else REJECT

        q_dates=sorted({
            datetime.fromtimestamp(x["okx_timestamp_ms"]/1000,tz=timezone.utc).strftime("%Y-%m-%d")
            for x in qualifying
        })
        q_months=sorted({
            datetime.fromtimestamp(x["okx_timestamp_ms"]/1000,tz=timezone.utc).strftime("%Y-%m")
            for x in qualifying
        })
        q_symbols=sorted({x["symbol"] for x in qualifying})
        q_symbol_counts={s:sum(1 for x in qualifying if x["symbol"]==s) for s in SYMBOLS}
        q_month_counts={m:sum(
            1 for x in qualifying
            if datetime.fromtimestamp(x["okx_timestamp_ms"]/1000,tz=timezone.utc).strftime("%Y-%m")==m
        ) for m in q_months}

        report={
            "stage":STAGE,
            "version":"0.1",
            "status":status,
            "candidate_label":"B13-A_NOT_YET_C13",
            "window":{"start_ms":START_MS,"end_exclusive_ms":END_MS_EXCL},
            "venues":["OKX","BYBIT"],
            "symbols":list(SYMBOLS),
            "sign_semantics":"positive funding => longs pay shorts on both venues",
            "match_tolerance_ms":MATCH_TOLERANCE_MS,
            "structural_burden_bps":STRUCTURAL_BURDEN_BPS,
            "qualifying_diff_bps":QUALIFYING_DIFF_BPS,
            "source_eligible_symbols":source_eligible,
            "source_eligible_count":len(source_eligible),
            "matched_settlements":len(all_matches),
            "matched_months":months,
            "data_quality_gates":data_gates,
            "qualifying_opportunities":len(qualifying),
            "qualifying_dates":q_dates,
            "qualifying_months":q_months,
            "qualifying_symbols":q_symbols,
            "qualifying_symbol_counts":q_symbol_counts,
            "qualifying_month_counts":q_month_counts,
            "structural_gates":structural_gates,
            "diagnostics":{
                "median_diff_bps":statistics.median(rates) if rates else None,
                "p90_diff_bps":nr(rates,0.90),
                "p99_diff_bps":nr(rates,0.99),
                "max_diff_bps":max(rates) if rates else None,
                "median_match_skew_ms":statistics.median([x["skew_ms"] for x in all_matches]) if all_matches else None,
                "p99_match_skew_ms":nr([float(x["skew_ms"]) for x in all_matches],0.99),
            },
            "per_symbol":per_symbol,
            "okx_archive_total_bytes":total_okx_bytes,
            "price_accessed":False,
            "basis_calculated":False,
            "trade_body_accessed":False,
            "l2_accessed":False,
            "strategy_price_pnl_calculated":False,
            "candidate_id_assigned":False,
            "promotional_evidence":False,
        }
        atomic_json(OUT,report)

        print(status)
        print("source_eligible =",len(source_eligible),"/ 12")
        print("matched_settlements =",len(all_matches))
        print("matched_months =",months)
        print("qualifying_ge50bps =",len(qualifying))
        print("qualifying_dates/months/symbols =",len(q_dates),"/",len(q_months),"/",len(q_symbols))
        print("diagnostics =",report["diagnostics"])
        print("structural_gates =",structural_gates)
        print("price/basis/PnL/promotional = False")
        print("candidate_id_assigned = False")
        print("report =",OUT)
        return 0

    except Exception as exc:
        print("B13A_STRUCTURAL_PREFLIGHT_IMPLEMENTATION_FAIL")
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

if __name__=="__main__":
    raise SystemExit(main())
