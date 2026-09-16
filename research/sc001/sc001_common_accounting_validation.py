from __future__ import annotations
from decimal import Decimal as D
from pathlib import Path
import json, os, sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from sc001_common_accounting_core import LinearSpec,Fill,price_to_ticks,ticks_to_price,qty_to_lots,lots_to_qty,apply_fills,equity_usdt,causal_visible,ledger_hash

PASS='SC001_COMMON_ACCOUNTING_CORE_VALIDATION_PASS'
REVIEW='SC001_COMMON_ACCOUNTING_CORE_VALIDATION_REVIEW'
DATA_ROOT=Path(os.environ.get('SC001_DATA_ROOT',str(Path.home()/'sc001_data'))).expanduser().resolve()
OUT=DATA_ROOT/'SC001_COMMON_ACCOUNTING_VALIDATION'/'sc001_common_accounting_validation_report.json'

def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); q=Path(str(p)+'.tmp')
    with q.open('w',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(q,p)

def assert_raises(fn):
    try: fn()
    except Exception: return
    raise AssertionError('expected exception')

def main():
    spec=LinearSpec('TEST-USDT-SWAP',D('0.1'),D('0.1'),D('0.1'),D('0.01'))
    tests=[]
    def T(name,fn):
        try: fn(); tests.append((name,True,None)); print('PASS',name)
        except Exception as e: tests.append((name,False,f'{type(e).__name__}: {e}')); print('FAIL',name,e)

    T('P01_tick_roundtrip',lambda: (_ for _ in ()).throw(AssertionError()) if ticks_to_price(price_to_ticks(D('50000.0'),spec),spec)!=D('50000.0') else None)
    T('P02_off_tick_reject',lambda: assert_raises(lambda: price_to_ticks(D('50000.05'),spec)))
    T('P03_lot_roundtrip',lambda: (_ for _ in ()).throw(AssertionError()) if lots_to_qty(qty_to_lots(D('1.2'),spec),spec)!=D('1.2') else None)
    T('P04_off_lot_reject',lambda: assert_raises(lambda: qty_to_lots(D('1.25'),spec)))
    T('P05_min_size',lambda: assert_raises(lambda: qty_to_lots(D('0.05'),spec)))

    def long_rt():
        fs=[Fill('a',0,1000,'BUY','maker',500000,10,D('2')),Fill('b',1,2000,'SELL','taker',501000,10,D('5'))]
        s=apply_fills(spec,fs)
        gross=D('1.0'); fees=D('0.3505'); net=D('0.6495')
        assert s['position_lots']==0 and s['gross_cash_usdt']==gross and s['fees_usdt']==fees and s['cash_usdt']==net
    T('P06_long_roundtrip_handcalc',long_rt)

    def short_rt():
        fs=[Fill('a',0,1000,'SELL','maker',501000,10,D('2')),Fill('b',1,2000,'BUY','taker',500000,10,D('5'))]
        s=apply_fills(spec,fs)
        assert s['position_lots']==0 and s['gross_cash_usdt']==D('1.0') and s['fees_usdt']==D('0.3502') and s['cash_usdt']==D('0.6498')
    T('P07_short_roundtrip_handcalc',short_rt)

    def partial():
        fs=[Fill('a',0,1,'BUY','maker',500000,4,D('2')),Fill('b',1,2,'BUY','maker',500000,6,D('2')),Fill('c',2,3,'SELL','taker',501000,10,D('5'))]
        s=apply_fills(spec,fs); assert s['position_lots']==0 and s['cash_usdt']==D('0.6495')
    T('P08_partial_fill_aggregation',partial)
    T('P09_same_side_accumulation',lambda: (_ for _ in ()).throw(AssertionError()) if apply_fills(spec,[Fill('a',0,1,'BUY','maker',500000,4,D('2')),Fill('b',1,2,'BUY','maker',500000,6,D('2'))])['position_lots']!=10 else None)
    T('P10_inventory_conservation',lambda: (_ for _ in ()).throw(AssertionError()) if apply_fills(spec,[Fill('a',0,1,'BUY','maker',500000,10,D('2')),Fill('b',1,2,'SELL','maker',500000,10,D('2'))])['position_lots']!=0 else None)
    T('P11_cash_conservation_flat_same_price',lambda: (_ for _ in ()).throw(AssertionError()) if apply_fills(spec,[Fill('a',0,1,'BUY','maker',500000,10,D('2')),Fill('b',1,2,'SELL','maker',500000,10,D('2'))])['cash_usdt']!=D('-0.2') else None)

    def mtm_long():
        s=apply_fills(spec,[Fill('a',0,1,'BUY','maker',500000,10,D('0'))]); assert equity_usdt(spec,s,501000)==D('1.0')
    T('P12_mtm_long',mtm_long)
    def mtm_short():
        s=apply_fills(spec,[Fill('a',0,1,'SELL','maker',501000,10,D('0'))]); assert equity_usdt(spec,s,500000)==D('1.0')
    T('P13_mtm_short',mtm_short)
    T('P14_duplicate_fill_reject',lambda: assert_raises(lambda: apply_fills(spec,[Fill('a',0,1,'BUY','maker',500000,1,D('2')),Fill('a',1,2,'SELL','maker',500000,1,D('2'))])))
    T('P15_nonpositive_qty_reject',lambda: assert_raises(lambda: apply_fills(spec,[Fill('a',0,1,'BUY','maker',500000,0,D('2'))])))
    T('P16_bad_side_liquidity_reject',lambda: (assert_raises(lambda: apply_fills(spec,[Fill('a',0,1,'HOLD','maker',500000,1,D('2'))])),assert_raises(lambda: apply_fills(spec,[Fill('b',0,1,'BUY','unknown',500000,1,D('2'))]))))
    T('P17_future_visibility_guard',lambda: (_ for _ in ()).throw(AssertionError()) if not(causal_visible(1000,1000) and not causal_visible(1001,1000)) else None)
    def det_hash():
        a=Fill('a',0,1,'BUY','maker',500000,1,D('2')); b=Fill('b',1,1,'SELL','taker',500100,1,D('5'))
        assert ledger_hash([a,b])==ledger_hash([b,a])
    T('P18_deterministic_ledger_hash',det_hash)
    def seq_order():
        a=Fill('a',1,1,'BUY','maker',500000,1,D('0')); b=Fill('b',0,1,'SELL','maker',500000,1,D('0'))
        s=apply_fills(spec,[a,b]); assert [x.fill_id for x in s['ordered_fills']]==['b','a']
    T('P19_same_timestamp_sequence_order',seq_order)
    T('P20_inverse_contract_fail_closed',lambda: assert_raises(lambda: LinearSpec('INV',D('1'),D('1'),D('1'),D('100'),'BTC','inverse')))

    ok=all(x[1] for x in tests)
    status=PASS if ok else REVIEW
    rep={'status':status,'tests_total':len(tests),'tests_passed':sum(1 for x in tests if x[1]),'tests':[{'name':n,'pass':p,'error':e} for n,p,e in tests],'real_market_data_body_accessed':False,'strategy_signal_calculated':False,'promotional_pnl_calculated':False,'july_august_reserved_bodies_accessed':False,'historical_exact_execution_specs_verified':False}
    atomic_json(OUT,rep)
    print(status); print('tests_passed =',rep['tests_passed'],'/',rep['tests_total']); print('real market data body accessed = False'); print('strategy signal calculated = False'); print('promotional PnL calculated = False'); print('July/August reserved bodies accessed = False'); print('report =',OUT)
    return 0 if ok else 2

if __name__=='__main__': raise SystemExit(main())
