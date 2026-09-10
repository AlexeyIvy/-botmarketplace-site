from __future__ import annotations
import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SYMBOL='BTCUSDT'
EXCHANGE_INFO='https://api.binance.com/api/v3/exchangeInfo'
KLINES='https://data-api.binance.vision/api/v3/klines'
CAPITALS=[50,100,150,200,250,300,400,500,750,1000,1500,2000,3000,5000,10000,25000,50000,100000]
TARGETS=[0,0.025,0.05,0.075,0.10,0.125,0.15,0.175,0.20]


def get_json(url, params):
    req=Request(url+'?'+urlencode(params), headers={'User-Agent':'botmarketplace-r009-g001/0.1'})
    with urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))


def d(x): return Decimal(str(x))

def floor_step(x, step):
    x=d(x); step=d(step)
    if step<=0: return x
    return (x/step).to_integral_value(rounding=ROUND_DOWN)*step


def parse_filters(symbol_info):
    fs={f['filterType']:f for f in symbol_info.get('filters',[])}
    lot=fs.get('LOT_SIZE',{})
    mlot=fs.get('MARKET_LOT_SIZE',{})
    steps=[d(v) for v in [lot.get('stepSize','0'), mlot.get('stepSize','0')] if d(v)>0]
    mins=[d(v) for v in [lot.get('minQty','0'), mlot.get('minQty','0')] if d(v)>0]
    step=max(steps) if steps else d('0')
    min_qty=max(mins) if mins else d('0')
    min_notional=d('0')
    n=fs.get('NOTIONAL')
    mn=fs.get('MIN_NOTIONAL')
    if n and str(n.get('applyMinToMarket',True)).lower()!='false':
        min_notional=max(min_notional,d(n.get('minNotional','0')))
    if mn and str(mn.get('applyToMarket',True)).lower()!='false':
        min_notional=max(min_notional,d(mn.get('minNotional','0')))
    return {'step_size':step,'min_qty':min_qty,'min_notional':min_notional}


def latest_closed_daily():
    now_ms=int(datetime.now(timezone.utc).timestamp()*1000)
    rows=get_json(KLINES,{'symbol':SYMBOL,'interval':'1d','limit':3})
    closed=[r for r in rows if int(r[6])<now_ms]
    if not closed: raise RuntimeError('No fully closed daily bar')
    r=closed[-1]
    return {'open_time_ms':int(r[0]),'close_time_ms':int(r[6]),'close':d(r[4])}


def main(outdir:Path):
    outdir.mkdir(parents=True, exist_ok=True)
    ex=get_json(EXCHANGE_INFO,{'symbol':SYMBOL})
    syms=[s for s in ex.get('symbols',[]) if s.get('symbol')==SYMBOL]
    if len(syms)!=1: raise RuntimeError('BTCUSDT symbol info missing/ambiguous')
    s=syms[0]; pf=parse_filters(s); px=latest_closed_daily(); price=px['close']
    snap={
      'created_at_utc':datetime.now(timezone.utc).isoformat(), 'symbol':SYMBOL,
      'status':s.get('status'), 'baseAsset':s.get('baseAsset'), 'quoteAsset':s.get('quoteAsset'),
      'latest_closed_daily_price':float(price), 'latest_close_time_ms':px['close_time_ms'],
      'effective_market_step_size':str(pf['step_size']), 'effective_market_min_qty':str(pf['min_qty']),
      'effective_market_min_notional':str(pf['min_notional']), 'raw_filters':s.get('filters',[]),
      'sources':{'exchangeInfo':EXCHANGE_INFO,'klines':KLINES}
    }
    (outdir/'r009_g001_instrument_snapshot.json').write_text(json.dumps(snap,indent=2),encoding='utf-8')

    import csv
    target_rows=[]; transition_rows=[]; qmap={}
    for C in CAPITALS:
        qmap[C]={}
        for w in TARGETS:
            ideal=d(C)*d(w)/price if w>0 else d('0')
            q=floor_step(ideal,pf['step_size']) if w>0 else d('0')
            notional=q*price
            feasible=(w==0) or (q>=pf['min_qty'] and notional>=pf['min_notional'])
            qmap[C][w]=q if feasible else d('0')
            effective_notional=(q if feasible else d('0'))*price
            target_rows.append({
              'capital_usd':C,'target_weight':w,'ideal_notional_usd':float(d(C)*d(w)),
              'rounded_qty_btc':float(q),'rounded_notional_usd':float(notional),
              'target_mechanically_feasible':feasible,
              'effective_weight_if_opened':float(effective_notional/d(C)),
              'absolute_weight_error_pp':abs(float(effective_notional/d(C))-w)*100,
            })
    for C in CAPITALS:
        for wi in TARGETS:
            for wj in TARGETS:
                if wi==wj: continue
                qi=qmap[C][wi]; qj=qmap[C][wj]
                dq=abs(qj-qi); n=dq*price
                feasible=(dq>=pf['min_qty'] and n>=pf['min_notional']) if dq>0 else False
                transition_rows.append({'capital_usd':C,'from_target':wi,'to_target':wj,'delta_target_pp':abs(wj-wi)*100,'delta_qty_btc':float(dq),'delta_notional_usd':float(n),'market_order_feasible':feasible})

    def write_csv(path, rows):
        with open(path,'w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    write_csv(outdir/'r009_g001_target_feasibility.csv',target_rows)
    write_csv(outdir/'r009_g001_transition_feasibility.csv',transition_rows)

    smallest=0.025
    analytic=max(float(pf['min_notional'])/smallest if pf['min_notional']>0 else 0.0,
                 float(pf['min_qty']*price)/smallest if pf['min_qty']>0 else 0.0)
    direct=[]
    for C in CAPITALS:
        row=next(r for r in transition_rows if r['capital_usd']==C and r['from_target']==0 and r['to_target']==0.025)
        if row['market_order_feasible']: direct.append(C)
    all_targets=[]
    for C in CAPITALS:
        rows=[r for r in target_rows if r['capital_usd']==C and r['target_weight']>0]
        if rows and all(r['target_mechanically_feasible'] for r in rows): all_targets.append(C)
    state={
      'status':'MECHANICAL_ENVELOPE_ESTABLISHED','evidence_status':'IMPLEMENTATION_GRANULARITY_ONLY_NOT_STRATEGY_PASS',
      'symbol':SYMBOL,'capital_grid_usd':CAPITALS,'r009_target_weights':TARGETS,
      'current_price':float(price),'effective_step_size':float(pf['step_size']),'effective_min_qty':float(pf['min_qty']),'effective_min_notional':float(pf['min_notional']),
      'analytic_floor_for_2_5pp_order_usd':analytic,
      'first_grid_capital_with_0_to_2_5pp_order_feasible':direct[0] if direct else None,
      'first_grid_capital_with_all_nonzero_target_states_feasible':all_targets[0] if all_targets else None,
      'important_limitation':'G001 is a current-rule mechanical snapshot. It does not simulate daily drift/rebalancing, skipped micro-rebalances, historical filter changes, slippage, or market-impact capacity. Those belong to G002/G003.',
      'outputs':['r009_g001_run_state.json','r009_g001_instrument_snapshot.json','r009_g001_target_feasibility.csv','r009_g001_transition_feasibility.csv','r009_g001_summary.md']
    }
    (outdir/'r009_g001_run_state.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
    md=f"""# R009-G001 Capital Granularity Snapshot v0.1\n\n- Status: **MECHANICAL_ENVELOPE_ESTABLISHED**\n- BTCUSDT latest fully closed daily price: **${float(price):,.2f}**\n- Effective market min quantity: **{pf['min_qty']} BTC**\n- Effective market step size: **{pf['step_size']} BTC**\n- Effective market min notional: **${float(pf['min_notional']):,.2f}**\n- Analytic lower bound for a standalone 2.5pp order: **${analytic:,.2f}**\n- First tested capital where 0 -> 2.5% is mechanically feasible: **{direct[0] if direct else 'none in grid'} USD**\n- First tested capital where every nonzero R009 target state is mechanically holdable: **{all_targets[0] if all_targets else 'none in grid'} USD**\n\nThis is not a strategy-performance result. G001 uses current Binance Spot filters and a current fully closed BTCUSDT price to establish the small-account mechanical floor. It does not certify exact daily rebalancing fidelity; pathwise discrete replay is G002 after forward plumbing is verified.\n"""
    (outdir/'r009_g001_summary.md').write_text(md,encoding='utf-8')
    print(md)

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--outdir',type=Path,required=True); a=ap.parse_args(); main(a.outdir)
