from __future__ import annotations

import json
import math
import os
import statistics
from pathlib import Path

DATA_ROOT = Path(os.environ.get('SC001_DATA_ROOT', str(Path.home() / 'sc001_data'))).expanduser().resolve()
PARENT = DATA_ROOT / 'SC001_E007R1_GROSS_FEASIBILITY' / 'sc001_e007r1_gross_feasibility_report.json'
OUT_DIR = DATA_ROOT / 'SC001_E007R1_READONLY_POSTMORTEM'
OUT = OUT_DIR / 'sc001_e007r1_readonly_postmortem_report.json'

PASS = 'E007R1_READONLY_POSTMORTEM_PASS'
PARENT_FAIL = 'E007R1_GROSS_FEASIBILITY_FAIL'
ASSETS = ('BTC', 'ETH', 'DOGE', 'ORDI', 'UNI', 'XRP', 'OP', 'BCH')
DATES = tuple(f'2024-07-{d:02d}' for d in range(1, 15))


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def load(path: Path) -> dict:
    if not path.exists():
        fail(f'missing parent report: {path}')
    obj = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(obj, dict):
        fail('parent report must be a JSON object')
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


def f(x, default=0.0) -> float:
    if x is None:
        return float(default)
    v = float(x)
    if not math.isfinite(v):
        fail(f'nonfinite numeric value: {x!r}')
    return v


def main() -> int:
    parent = load(PARENT)
    if parent.get('status') != PARENT_FAIL:
        fail(f'parent is not terminal FAIL: {parent.get("status")}')
    if tuple(parent.get('assets') or []) != ASSETS:
        fail('parent asset identity mismatch')
    if parent.get('asset_holdout_accessed') is not False:
        fail('asset holdout firewall mismatch')
    if parent.get('august_confirmation_accessed') is not False:
        fail('August Confirmation firewall mismatch')
    if parent.get('discrete_contract_pnl_calculated') is not False:
        fail('discrete contract PnL firewall mismatch')
    if parent.get('fees_or_net_pnl_calculated') is not False:
        fail('net PnL firewall mismatch')

    per = parent.get('per_instrument') or {}
    if set(per) != set(ASSETS):
        fail('per-instrument identity mismatch')

    agg = parent.get('aggregate') or {}
    gates = parent.get('gates') or {}
    failed = list(parent.get('failed_gates') or [])

    rows = []
    total_completed = 0
    total_abs_contrib = 0.0
    for sym in ASSETS:
        block = per[sym]
        primary = block.get('primary') or {}
        stress = block.get('stress') or {}
        completed = int(primary.get('completed', 0))
        total_completed += completed
        sum_gross = f(primary.get('sum_gross_bps'))
        total_abs_contrib += abs(sum_gross)
        row = {
            'symbol': sym,
            'candidate_count': int(block.get('candidate_count', 0)),
            'decisions': int(primary.get('decisions', 0)),
            'completed': completed,
            'active_days': int(primary.get('active_days', 0)),
            'completion_rate': f(primary.get('completion_rate')),
            'mean_bps': None if primary.get('mean_bps') is None else f(primary.get('mean_bps')),
            'median_bps': None if primary.get('median_bps') is None else f(primary.get('median_bps')),
            'trimmed_mean_bps': None if primary.get('trimmed_mean_bps') is None else f(primary.get('trimmed_mean_bps')),
            'positive_event_share': f(primary.get('positive_event_share')),
            'positive_active_day_share': f(primary.get('positive_active_day_share')),
            'long_count': int(primary.get('long_count', 0)),
            'short_count': int(primary.get('short_count', 0)),
            'long_mean_bps': None if primary.get('long_mean_bps') is None else f(primary.get('long_mean_bps')),
            'short_mean_bps': None if primary.get('short_mean_bps') is None else f(primary.get('short_mean_bps')),
            'sum_gross_bps': sum_gross,
            'lat1000_mean_bps': None if (stress.get('1000') or {}).get('mean_bps') is None else f((stress.get('1000') or {}).get('mean_bps')),
            'lat2000_mean_bps': None if (stress.get('2000') or {}).get('mean_bps') is None else f((stress.get('2000') or {}).get('mean_bps')),
            'day_means': primary.get('day_means') or {},
        }
        rows.append(row)

    if total_completed != int(agg.get('pooled_completed', -1)):
        fail('pooled completed reconciliation mismatch')

    for row in rows:
        row['event_weight'] = row['completed'] / total_completed if total_completed else 0.0
        row['abs_gross_contribution_share'] = abs(row['sum_gross_bps']) / total_abs_contrib if total_abs_contrib else 0.0
        row['signed_gross_contribution_share'] = row['sum_gross_bps'] / total_abs_contrib if total_abs_contrib else 0.0

    ranked = sorted(rows, key=lambda r: (-(r['mean_bps'] if r['mean_bps'] is not None else 0.0), r['symbol']))
    for i, row in enumerate(ranked, 1):
        row['mean_rank'] = i

    means = [0.0 if r['mean_bps'] is None else r['mean_bps'] for r in rows]
    stress1 = [0.0 if r['lat1000_mean_bps'] is None else r['lat1000_mean_bps'] for r in rows]
    stress2 = [0.0 if r['lat2000_mean_bps'] is None else r['lat2000_mean_bps'] for r in rows]

    day_rows = []
    for d in DATES:
        vals = []
        active = 0
        positive = 0
        for r in rows:
            dm = r['day_means']
            if d in dm:
                v = f(dm[d])
                active += 1
                if v > 0:
                    positive += 1
                vals.append(v)
            else:
                vals.append(0.0)
        day_rows.append({
            'date': d,
            'active_instruments': active,
            'positive_instruments': positive,
            'equal_weight_all8_day_mean_bps': statistics.fmean(vals),
            'median_all8_day_mean_bps': statistics.median(vals),
        })

    pooled_mean = None if agg.get('pooled_mean_bps') is None else f(agg.get('pooled_mean_bps'))
    eq_mean = f(agg.get('equal_weight_instrument_mean_bps'))
    med_inst = f(agg.get('median_instrument_mean_bps'))
    pooled_trim = f(agg.get('pooled_trimmed_mean_bps'))
    pooled_median = f(agg.get('pooled_median_bps'))
    lat1_eq = f((agg.get('stress_equal_weight_mean_bps') or {}).get('1000'))
    lat2_eq = f((agg.get('stress_equal_weight_mean_bps') or {}).get('2000'))

    q = statistics.quantiles(means, n=4, method='inclusive') if len(means) >= 4 else [None, None, None]
    classifications = {
        'event_level_effect_present_somewhere': pooled_trim >= 15.0 and pooled_median >= 10.0,
        'cross_market_average_headroom_insufficient': ('equal_weight_mean_gte20' in failed or 'median_instrument_mean_gte15' in failed),
        'cross_market_breadth_insufficient': 'positive_instruments_gte5' in failed,
        'latency_robustness_insufficient': ('lat1000_equal_weight_gte15' in failed or 'lat2000_equal_weight_gte10' in failed),
        'sample_or_activity_failure': any(x in failed for x in ('active_assets_gte_6', 'assets_completed_gte5_count_gte4', 'pooled_completed_gte40')),
        'concentration_failure': 'top_instrument_abs_contribution_lte035' in failed,
    }

    rep = {
        'stage': 'SC001-E007R1-READONLY-POSTMORTEM',
        'status': PASS,
        'parent_status': PARENT_FAIL,
        'parent_failed_gates': failed,
        'per_instrument': rows,
        'ranked_by_primary_mean': [r['symbol'] for r in ranked],
        'calendar_day_diagnostics': day_rows,
        'summary': {
            'pooled_completed': total_completed,
            'pooled_mean_bps': pooled_mean,
            'pooled_trimmed_mean_bps': pooled_trim,
            'pooled_median_bps': pooled_median,
            'equal_weight_mean_bps': eq_mean,
            'median_instrument_mean_bps': med_inst,
            'positive_instruments': int(agg.get('positive_instrument_count', 0)),
            'lat1000_equal_weight_mean_bps': lat1_eq,
            'lat2000_equal_weight_mean_bps': lat2_eq,
            'cross_instrument_mean_std_bps': statistics.pstdev(means),
            'cross_instrument_mean_q1_bps': q[0],
            'cross_instrument_mean_q3_bps': q[2],
            'best_instrument': ranked[0]['symbol'],
            'best_instrument_mean_bps': ranked[0]['mean_bps'],
            'worst_instrument': ranked[-1]['symbol'],
            'worst_instrument_mean_bps': ranked[-1]['mean_bps'],
            'max_event_weight': max(r['event_weight'] for r in rows),
            'max_abs_gross_contribution_share': max(r['abs_gross_contribution_share'] for r in rows),
            'mean_latency_decay_500_to_1000_bps': statistics.fmean(means) - statistics.fmean(stress1),
            'mean_latency_decay_500_to_2000_bps': statistics.fmean(means) - statistics.fmean(stress2),
        },
        'classifications': classifications,
        'strategy_rerun_performed': False,
        'e007r1_terminal_decision_changed': False,
        'asset_holdout_accessed': False,
        'august_confirmation_accessed': False,
        'july_16_30_accessed': False,
        'l2_accessed': False,
        'discrete_or_net_pnl_calculated': False,
        'historical_exact_execution_specs_verified': False,
    }
    atomic(OUT, rep)

    print(PASS)
    print('pooled_mean_bps =', pooled_mean)
    print('equal_weight_mean_bps =', eq_mean)
    print('median_instrument_mean_bps =', med_inst)
    print('ranked_by_mean =', rep['ranked_by_primary_mean'])
    print('best_instrument =', rep['summary']['best_instrument'], rep['summary']['best_instrument_mean_bps'])
    print('worst_instrument =', rep['summary']['worst_instrument'], rep['summary']['worst_instrument_mean_bps'])
    print('cross_instrument_mean_std_bps =', rep['summary']['cross_instrument_mean_std_bps'])
    print('max_event_weight =', rep['summary']['max_event_weight'])
    print('max_abs_gross_contribution_share =', rep['summary']['max_abs_gross_contribution_share'])
    print('classifications =', classifications)
    print('strategy rerun performed = False')
    print('E007R1 terminal decision changed = False')
    print('asset holdout accessed = False')
    print('August Confirmation accessed = False')
    print('discrete/net PnL calculated = False')
    print('report =', OUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
