from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_ROOT = Path(os.environ.get('SC001_DATA_ROOT', str(Path.home() / 'sc001_data'))).expanduser().resolve()
META = DATA_ROOT / 'SC001_E007R1_TRADE_METADATA_PREFLIGHT' / 'sc001_e007r1_trade_metadata_preflight_report.json'
ACQ = DATA_ROOT / 'SC001_E007R1_TRADE_ACQUISITION'
ARCH = ACQ / 'archives'
VERIFY = ACQ / 'sc001_e007r1_trade_acquisition_verify_report.json'
OUT_DIR = DATA_ROOT / 'SC001_E007R1_TRADE_SEMANTIC_INTEGRITY'
PREFLIGHT_REPORT = OUT_DIR / 'sc001_e007r1_trade_semantic_preflight_report.json'
REPORT = OUT_DIR / 'sc001_e007r1_trade_semantic_integrity_report.json'

ASSETS = ('BTC', 'ETH', 'DOGE', 'ORDI', 'UNI', 'XRP', 'OP', 'BCH')
ARCHIVE_DATES = tuple(['2024-06-30'] + [f'2024-07-{d:02d}' for d in range(1, 16)])
TARGET_DATES = tuple(['2024-06-30'] + [f'2024-07-{d:02d}' for d in range(1, 15)])
HEADER = ['instrument_name', 'trade_id', 'side', 'price', 'size', 'created_time']
PREFLIGHT_PASS = 'E007R1_TRADE_SEMANTIC_PREFLIGHT_PASS'
SEMANTIC_PASS = 'E007R1_TRADE_SEMANTIC_INTEGRITY_PASS'


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load(path: Path) -> dict:
    if not path.exists():
        fail(f'missing required file: {path}')
    obj = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(obj, dict):
        fail(f'JSON object expected: {path}')
    return obj


def atomic(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def bounds(date_text: str) -> tuple[int, int]:
    d = datetime.strptime(date_text, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    lo = int(d.timestamp() * 1000)
    hi = int((d + timedelta(days=1)).timestamp() * 1000)
    return lo, hi


def parent_map() -> dict[str, dict]:
    meta = load(META)
    if meta.get('status') != 'E007R1_TRADE_METADATA_PREFLIGHT_PASS':
        fail('metadata parent not exact PASS')
    rows = meta.get('rows') or []
    if len(rows) != 128 or int(meta.get('resolved_files', 0)) != 128:
        fail('metadata parent row count mismatch')
    byfn = {r['filename']: r for r in rows if r.get('ok')}
    if len(byfn) != 128:
        fail('metadata filename identity mismatch')
    return byfn


def local_path(row: dict) -> Path:
    sym = str(row['instrument']).split('-')[0]
    return ARCH / sym / row['filename']


def preflight() -> int:
    byfn = parent_map()
    v = load(VERIFY)
    if v.get('status') != 'E007R1_TRADE_ACQUISITION_VERIFY_PASS':
        fail('acquisition verify not exact PASS')
    if int(v.get('verified_files', 0)) != 128:
        fail('acquisition verified file count mismatch')
    if int(v.get('verified_total_bytes', -1)) != 468108915:
        fail('acquisition verified byte total mismatch')

    missing = []
    size_bad = []
    for fn, row in byfn.items():
        p = local_path(row)
        if not p.exists():
            missing.append(fn)
        elif p.stat().st_size != int(row['bytes']):
            size_bad.append(fn)
    if missing or size_bad:
        fail(f'local preflight failure missing={len(missing)} size_bad={len(size_bad)}')

    rep = {
        'stage': 'SC001-E007R1-TRADE-SEMANTIC-PREFLIGHT',
        'status': PREFLIGHT_PASS,
        'source_files': 128,
        'target_utc_days': len(ASSETS) * len(TARGET_DATES),
        'assets': list(ASSETS),
        'target_dates': list(TARGET_DATES),
        'asset_holdout_accessed': False,
        'august_confirmation_accessed': False,
        'strategy_signal_calculated': False,
        'strategy_pnl_calculated': False,
    }
    atomic(PREFLIGHT_REPORT, rep)
    print(PREFLIGHT_PASS)
    print('source_files = 128')
    print('target_utc_days = 120')
    print('asset holdout accessed = False')
    print('August Confirmation accessed = False')
    print('strategy signal/PnL calculated = False')
    return 0


def open_reader(path: Path):
    zf = zipfile.ZipFile(path, 'r')
    bad = zf.testzip()
    if bad is not None:
        zf.close()
        fail(f'ZIP CRC failure {path.name}: {bad}')
    members = [m for m in zf.infolist() if not m.is_dir()]
    if len(members) != 1:
        zf.close()
        fail(f'unexpected ZIP member count {path.name}: {len(members)}')
    raw = zf.open(members[0], 'r')
    text = io.TextIOWrapper(raw, encoding='utf-8', newline='')
    reader = csv.reader(text)
    hdr = next(reader, None)
    if hdr != HEADER:
        text.close(); zf.close()
        fail(f'unexpected header {path.name}: {hdr!r}')
    return zf, text, reader, members[0]


def parse_row(row: list[str], expected_inst: str, path_name: str) -> tuple[int, int, str, float, float]:
    if len(row) != 6:
        fail(f'malformed row width {path_name}: {len(row)}')
    if row[0] != expected_inst:
        fail(f'instrument mismatch {path_name}: {row[0]} != {expected_inst}')
    try:
        trade_id = int(row[1])
        side = row[2].lower()
        price = float(row[3])
        size = float(row[4])
        ts = int(row[5])
    except Exception as exc:
        raise RuntimeError(f'parse failure {path_name}: {row!r}') from exc
    if trade_id < 0 or ts < 0:
        fail(f'negative id/timestamp {path_name}')
    if side not in {'buy', 'sell'}:
        fail(f'bad side {path_name}: {side}')
    if not math.isfinite(price) or price <= 0:
        fail(f'bad price {path_name}: {price}')
    if not math.isfinite(size) or size <= 0:
        fail(f'bad size {path_name}: {size}')
    return trade_id, ts, side, price, size


def scan_source(path: Path, inst: str) -> dict:
    zf, text, reader, member = open_reader(path)
    count = 0
    first_ts = last_ts = None
    first_id = last_id = None
    prev_ts = prev_id = None
    try:
        for row in reader:
            if not row:
                continue
            tid, ts, side, price, size = parse_row(row, inst, path.name)
            if prev_ts is not None and ts < prev_ts:
                fail(f'source timestamp reversal {path.name}')
            if prev_id is not None and tid <= prev_id:
                fail(f'source trade-id duplicate/backward {path.name}: {tid} <= {prev_id}')
            if count == 0:
                first_ts, first_id = ts, tid
            last_ts, last_id = ts, tid
            prev_ts, prev_id = ts, tid
            count += 1
    finally:
        text.close(); zf.close()
    if count <= 0:
        fail(f'empty source archive {path.name}')
    return {
        'filename': path.name,
        'instrument': inst,
        'rows': count,
        'first_ts': first_ts,
        'last_ts': last_ts,
        'first_trade_id': first_id,
        'last_trade_id': last_id,
        'member': member.filename,
        'member_uncompressed_bytes': member.file_size,
    }


def iter_target_rows(path: Path, inst: str, lo: int, hi: int):
    zf, text, reader, _member = open_reader(path)
    try:
        for row in reader:
            if not row:
                continue
            tid, ts, side, price, size = parse_row(row, inst, path.name)
            if lo <= ts < hi:
                yield tid, ts, side
    finally:
        text.close(); zf.close()


def target_day(sym: str, day: str, byfn: dict[str, dict]) -> dict:
    inst = f'{sym}-USDT-SWAP'
    d = datetime.strptime(day, '%Y-%m-%d')
    d1 = (d + timedelta(days=1)).strftime('%Y-%m-%d')
    fn0 = f'{inst}-trades-{day}.zip'
    fn1 = f'{inst}-trades-{d1}.zip'
    if fn0 not in byfn or fn1 not in byfn:
        fail(f'missing stitch source for {inst} {day}')
    p0, p1 = local_path(byfn[fn0]), local_path(byfn[fn1])
    lo, hi = bounds(day)

    count = 0
    prev_ts = prev_id = None
    gaps = 0
    minutes: set[int] = set()
    sides: set[str] = set()
    first_ts = last_ts = None
    first_id = last_id = None

    for p in (p0, p1):
        for tid, ts, side in iter_target_rows(p, inst, lo, hi):
            if prev_ts is not None and ts < prev_ts:
                fail(f'target timestamp reversal {inst} {day}')
            if prev_id is not None:
                if tid <= prev_id:
                    fail(f'target trade-id duplicate/backward {inst} {day}: {tid} <= {prev_id}')
                if tid > prev_id + 1:
                    gaps += tid - prev_id - 1
            if count == 0:
                first_ts, first_id = ts, tid
            last_ts, last_id = ts, tid
            prev_ts, prev_id = ts, tid
            minutes.add((ts - lo) // 60000)
            sides.add(side)
            count += 1

    if count <= 0:
        fail(f'no admitted target rows {inst} {day}')
    if gaps != 0:
        fail(f'target trade-id gaps {inst} {day}: {gaps}')
    if sides != {'buy', 'sell'}:
        fail(f'target missing side breadth {inst} {day}: {sorted(sides)}')
    if len(minutes) != 1440 or min(minutes) != 0 or max(minutes) != 1439:
        fail(f'target minute coverage {inst} {day}: {len(minutes)}/1440')

    return {
        'instrument': inst,
        'date': day,
        'rows': count,
        'first_ts': first_ts,
        'last_ts': last_ts,
        'first_trade_id': first_id,
        'last_trade_id': last_id,
        'trade_id_gaps': gaps,
        'minute_buckets': len(minutes),
        'both_sides': sides == {'buy', 'sell'},
        'performance_role': 'BOUNDARY_WARMUP' if day == '2024-06-30' else 'DISCOVERY_PERFORMANCE',
    }


def run() -> int:
    # Re-run fast fail-closed parent checks before body scan.
    preflight()
    byfn = parent_map()

    source_rows = []
    for ai, sym in enumerate(ASSETS, 1):
        inst = f'{sym}-USDT-SWAP'
        for di, day in enumerate(ARCHIVE_DATES, 1):
            fn = f'{inst}-trades-{day}.zip'
            row = byfn.get(fn)
            if row is None:
                fail(f'missing metadata row {fn}')
            print(f'SOURCE [{ai}/8 {di}/16] {fn}', flush=True)
            m = scan_source(local_path(row), inst)
            source_rows.append(m)
            print(f'PASS SOURCE rows={m["rows"]}', flush=True)

    day_rows = []
    for ai, sym in enumerate(ASSETS, 1):
        for di, day in enumerate(TARGET_DATES, 1):
            print(f'UTC-STITCH [{ai}/8 {di}/15] {sym} {day}', flush=True)
            m = target_day(sym, day, byfn)
            day_rows.append(m)
            print(f'PASS UTC rows={m["rows"]} minutes={m["minute_buckets"]} gaps={m["trade_id_gaps"]}', flush=True)

    if len(source_rows) != 128:
        fail(f'source qualification count mismatch {len(source_rows)}')
    if len(day_rows) != 120:
        fail(f'target day qualification count mismatch {len(day_rows)}')

    rep = {
        'stage': 'SC001-E007R1-TRADE-SEMANTIC-INTEGRITY',
        'status': SEMANTIC_PASS,
        'source_files_qualified': 128,
        'source_files_expected': 128,
        'reconstructed_utc_days_qualified': 120,
        'reconstructed_utc_days_expected': 120,
        'assets': list(ASSETS),
        'target_dates': list(TARGET_DATES),
        'source_files': source_rows,
        'utc_days': day_rows,
        'utc_stitch_rule': 'archive D + archive D+1; retain created_time in UTC [D,D+1)',
        'asset_holdout_accessed': False,
        'august_confirmation_accessed': False,
        'l2_body_accessed': False,
        'strategy_signal_calculated': False,
        'strategy_pnl_calculated': False,
        'historical_exact_execution_specs_verified': False,
    }
    atomic(REPORT, rep)
    print(SEMANTIC_PASS)
    print('source_files_qualified = 128 / 128')
    print('reconstructed_utc_days_qualified = 120 / 120')
    print('asset holdout accessed = False')
    print('August Confirmation accessed = False')
    print('strategy signal/PnL calculated = False')
    print('report =', REPORT)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['preflight', 'run'])
    args = ap.parse_args()
    return preflight() if args.mode == 'preflight' else run()


if __name__ == '__main__':
    raise SystemExit(main())
