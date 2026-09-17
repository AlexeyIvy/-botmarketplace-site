from __future__ import annotations

import json, math, os, statistics
from pathlib import Path

DATA_ROOT=Path(os.environ.get('SC001_DATA_ROOT',str(Path.home()/'sc001_data'))).expanduser().resolve()
PARENT=DATA_ROOT/'SC001_E009_GROSS_FEASIBILITY'/'sc001_e009_gross_feasibility_report.json'
OUT_DIR=DATA_ROOT/'SC001_E009_READONLY_POSTMORTEM'
OUT=OUT_DIR/'sc001_e009_readonly_postmortem_report.json'
PASS='E009_READONLY_POSTMORTEM_PASS'
PARENT_FAIL='E009_GROSS_FEASIBILITY_FAIL'
ASSETS=('BTC','ETH','DOGE','ORDI','UNI','XRP','OP','BCH')


def fail(s): raise RuntimeError(s)
def load(p):
    if not p.exists(): fail(f'missing {p}')
    x=json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(x,dict): fail('parent must be object')
    return x

def atomic(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); q=Path(str(p)+'.tmp')
    with q.open('w',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(q,p)
def finite(x):
    if x is None:return None
    v=float(x)
    if not math.isfinite(v): fail(f'nonfinite {x!r}')
    return v


def main():
    p=load(PARENT)
    if p.get('status')!=PARENT_FAIL: fail(f'parent status {p.get("status")}')
    if tuple(p.get('assets') or [])!=ASSETS: fail('asset identity mismatch')
    for k in ('asset_holdout_accessed','october_confirmation_accessed','august_repurposed','discrete_contract_pnl_calculated'):
        if p.get(k) is not False: fail(f'firewall mismatch {k}')
    per=p.get('per_instrument') or {}
    if set(per)!=set(ASSETS): fail('per-instrument identity mismatch')
    agg=p.get('aggregate') or {}
    failed=list(p.get('failed_gates') or [])
    rows=[]; total_completed=0; total_abs=0.0
    for s in ASSETS:
        b=per[s]; pm=b.get('primary') or {}; st=b.get('stress') or {}
        comp=int(pm.get('completed',0)); sg=finite(pm.get('sum_gross_bps')) or 0.0
        total_completed+=comp; total_abs+=abs(sg)
        rows.append({
            'symbol':s,'candidate_count':int(b.get('candidate_count',0)),'decisions':int(pm.get('decisions',0)),
            'completed':comp,'active_days':int(pm.get('active_days',0)),'mean_bps':finite(pm.get('mean_bps')),
            'median_bps':finite(pm.get('median_bps')),'trimmed_mean_bps':finite(pm.get('trimmed_mean_bps')),
            'positive_event_share':finite(pm.get('positive_event_share')),'positive_active_day_share':finite(pm.get('positive_active_day_share')),
            'long_count':int(pm.get('long_count',0)),'short_count':int(pm.get('short_count',0)),
            'long_mean_bps':finite(pm.get('long_mean_bps')),'short_mean_bps':finite(pm.get('short_mean_bps')),
            'sum_gross_bps':sg,'lat1000_mean_bps':finite((st.get('1000') or {}).get('mean_bps')),
            'lat2000_mean_bps':finite((st.get('2000') or {}).get('mean_bps')),
            'valid_normalized_observations':b.get('valid_normalized_observations'),
            'trigger_abs_z_median':b.get('trigger_abs_z_median'),
        })
    if total_completed!=int(agg.get('pooled_completed',-1)): fail('completed reconciliation mismatch')
    for r in rows:
        r['event_weight']=r['completed']/total_completed if total_completed else 0.0
        r['abs_gross_contribution_share']=abs(r['sum_gross_bps'])/total_abs if total_abs else 0.0
    ranked=sorted(rows,key=lambda r:(-(r['mean_bps'] if r['mean_bps'] is not None else 0.0),r['symbol']))
    means=[0.0 if r['mean_bps'] is None else r['mean_bps'] for r in rows]
    cls={
        'adequate_sample': total_completed>=40,
        'cross_market_average_headroom_insufficient': any(x in failed for x in ('equal_weight_mean_gte20','median_instrument_mean_gte15')),
        'cross_market_breadth_insufficient': 'positive_instruments_gte5' in failed,
        'pooled_robust_headroom_insufficient': any(x in failed for x in ('pooled_trimmed_mean_gte15','pooled_median_gte10')),
        'latency_robustness_insufficient': any(x in failed for x in ('lat1000_equal_weight_gte15','lat2000_equal_weight_gte10')),
        'concentration_failure': 'top_instrument_abs_contribution_lte035' in failed,
    }
    rep={'stage':'SC001-E009-READONLY-POSTMORTEM','status':PASS,'parent_status':PARENT_FAIL,'parent_failed_gates':failed,
         'per_instrument':rows,'ranked_by_primary_mean':[r['symbol'] for r in ranked],
         'summary':{'pooled_completed':total_completed,'pooled_mean_bps':finite(agg.get('pooled_mean_bps')),
                    'pooled_trimmed_mean_bps':finite(agg.get('pooled_trimmed_mean_bps')),'pooled_median_bps':finite(agg.get('pooled_median_bps')),
                    'equal_weight_mean_bps':finite(agg.get('equal_weight_instrument_mean_bps')),
                    'median_instrument_mean_bps':finite(agg.get('median_instrument_mean_bps')),
                    'positive_instruments':int(agg.get('positive_instrument_count',0)),
                    'cross_instrument_mean_std_bps':statistics.pstdev(means),
                    'best_instrument':ranked[0]['symbol'],'best_instrument_mean_bps':ranked[0]['mean_bps'],
                    'worst_instrument':ranked[-1]['symbol'],'worst_instrument_mean_bps':ranked[-1]['mean_bps'],
                    'max_event_weight':max(r['event_weight'] for r in rows),
                    'max_abs_gross_contribution_share':max(r['abs_gross_contribution_share'] for r in rows)},
         'classifications':cls,'strategy_rerun_performed':False,'e009_terminal_decision_changed':False,
         'asset_holdout_accessed':False,'october_confirmation_accessed':False,'august_repurposed':False,
         'l2_accessed':False,'discrete_or_net_pnl_calculated':False}
    atomic(OUT,rep)
    print(PASS)
    print('ranked_by_mean =',rep['ranked_by_primary_mean'])
    print('best_instrument =',rep['summary']['best_instrument'],rep['summary']['best_instrument_mean_bps'])
    print('worst_instrument =',rep['summary']['worst_instrument'],rep['summary']['worst_instrument_mean_bps'])
    print('cross_instrument_mean_std_bps =',rep['summary']['cross_instrument_mean_std_bps'])
    print('max_event_weight =',rep['summary']['max_event_weight'])
    print('max_abs_gross_contribution_share =',rep['summary']['max_abs_gross_contribution_share'])
    print('classifications =',cls)
    print('strategy rerun performed = False')
    print('E009 terminal decision changed = False')
    print('asset holdout accessed = False')
    print('October Confirmation accessed = False')
    print('August repurposed = False')
    print('discrete/net PnL calculated = False')
    print('report =',OUT)
    return 0

if __name__=='__main__': raise SystemExit(main())
