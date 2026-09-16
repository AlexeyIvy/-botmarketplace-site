from __future__ import annotations
import json, os
from decimal import Decimal
from pathlib import Path
from sc001_common_accounting_core import LinearSpec, apply_fills, ledger_hash
from sc001_normalized_market_schema import MarketEvent, BookLevel, BookState, make_book, require_strategy_visible
from sc001_taker_execution_kernel import TakerRequest, execute_taker

D=Decimal
PASS='SC001_TAKER_KERNEL_SYNTHETIC_VALIDATION_PASS'
REVIEW='SC001_TAKER_KERNEL_SYNTHETIC_VALIDATION_REVIEW'
DATA_ROOT=Path(os.environ.get('SC001_DATA_ROOT',str(Path.home()/'sc001_data'))).expanduser().resolve()
OUT=DATA_ROOT/'SC001_TAKER_KERNEL_SYNTHETIC_VALIDATION'/'sc001_taker_kernel_synthetic_validation_report.json'
SPEC=LinearSpec('TEST-USDT-SWAP',D('0.1'),D('1'),D('1'),D('1'))
FEE=D('5')

def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); q=Path(str(p)+'.tmp')
    with q.open('w',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True,default=str); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.replace(q,p)

def raises(fn):
    try: fn()
    except Exception: return True
    return False

def req(rid,side,qty,decision=1000,d2s=0,out=100,inst='TEST-USDT-SWAP'):
    return TakerRequest(rid,inst,side,qty,decision,d2s,out,FEE)

def base_book(a=900,b=2000):
    return make_book('TEST-USDT-SWAP',a,b,[(1000,10),(990,20)],[(1010,10),(1020,20)])

def main():
    tests=[]
    def T(name,fn):
        ok=False; err=None
        try: ok=bool(fn())
        except Exception as e: err=f'{type(e).__name__}: {e}'
        tests.append({'name':name,'pass':ok,'error':err})
        print(('PASS' if ok else 'FAIL'),name,('' if err is None else err))

    T('P01_event_causal_timestamp_order',lambda: (MarketEvent('X',100,105,1,'trade').validate() is None))
    T('P02_observed_before_source_reject',lambda: raises(lambda: MarketEvent('X',105,100,1,'trade').validate()))
    T('P03_strategy_future_visibility_reject',lambda: raises(lambda: require_strategy_visible(MarketEvent('X',100,120,1,'trade'),119)))
    T('P04_valid_book_interval_membership',lambda: base_book().active_at(1100))
    T('P05_activation_at_valid_from_accept',lambda: execute_taker(req('r5','BUY',1,decision=800,out=100),base_book()).complete)
    T('P06_activation_at_valid_to_reject',lambda: raises(lambda: execute_taker(req('r6','BUY',1,decision=1900,out=100),base_book())))
    T('P07_crossed_book_reject',lambda: raises(lambda: BookState('TEST-USDT-SWAP',0,10,0,(BookLevel(1010,1),),(BookLevel(1010,1),)).validate()))
    T('P08_duplicate_level_reject',lambda: raises(lambda: BookState('TEST-USDT-SWAP',0,10,0,(BookLevel(1000,1),),(BookLevel(1010,1),BookLevel(1010,2))).validate()))
    T('P09_bad_ask_order_reject',lambda: raises(lambda: BookState('TEST-USDT-SWAP',0,10,0,(BookLevel(1000,1),),(BookLevel(1020,1),BookLevel(1010,1))).validate()))
    T('P10_bad_bid_order_reject',lambda: raises(lambda: BookState('TEST-USDT-SWAP',0,10,0,(BookLevel(990,1),BookLevel(1000,1)),(BookLevel(1010,1),)).validate()))
    T('P11_buy_single_level_fill',lambda: (lambda r: r.complete and len(r.fills)==1 and r.fills[0].price_ticks==1010 and r.fills[0].qty_lots==3)(execute_taker(req('r11','BUY',3),base_book())))
    T('P12_sell_single_level_fill',lambda: (lambda r: r.complete and len(r.fills)==1 and r.fills[0].price_ticks==1000 and r.fills[0].qty_lots==3)(execute_taker(req('r12','SELL',3),base_book())))
    mb=make_book('TEST-USDT-SWAP',900,2000,[(1000,2),(990,2)],[(1010,2),(1020,2)])
    T('P13_buy_multilevel_sweep',lambda: (lambda r: r.complete and [(f.price_ticks,f.qty_lots) for f in r.fills]==[(1010,2),(1020,1)])(execute_taker(req('r13','BUY',3),mb)))
    T('P14_sell_multilevel_sweep',lambda: (lambda r: r.complete and [(f.price_ticks,f.qty_lots) for f in r.fills]==[(1000,2),(990,1)])(execute_taker(req('r14','SELL',3),mb)))
    T('P15_partial_depth_explicit_remainder',lambda: (lambda r: (not r.complete) and r.filled_qty_lots==4 and r.remaining_qty_lots==1)(execute_taker(req('r15','BUY',5),mb)))
    T('P16_nonpositive_request_reject',lambda: raises(lambda: execute_taker(req('r16','BUY',0),base_book())))
    T('P17_wrong_instrument_reject',lambda: raises(lambda: execute_taker(req('r17','BUY',1,inst='OTHER-USDT-SWAP'),base_book())))
    T('P18_latency_sets_activation_timestamp',lambda: execute_taker(req('r18','BUY',1,decision=1000,d2s=50,out=200),make_book('TEST-USDT-SWAP',1200,1400,[(1000,2)],[(1010,2)])).activation_ts_ms==1250)
    T('P19_future_book_cannot_backuse',lambda: raises(lambda: execute_taker(req('r19','BUY',1,decision=1000,out=100),make_book('TEST-USDT-SWAP',1101,1300,[(1000,2)],[(1010,2)]))))
    T('P20_deterministic_fill_ids_order',lambda: [f.fill_id for f in execute_taker(req('r20','BUY',3),mb).fills]==['r20:0','r20:1'])

    buybook=make_book('TEST-USDT-SWAP',1000,1500,[(1000,10)],[(1010,10)])
    sellbook=make_book('TEST-USDT-SWAP',2000,2500,[(1020,10)],[(1030,10)])
    b=execute_taker(req('long_entry','BUY',2,decision=1000,out=100),buybook)
    s=execute_taker(req('long_exit','SELL',2,decision=2000,out=100),sellbook)
    longfills=list(b.fills+s.fills); longstate=apply_fills(SPEC,longfills)
    T('P21_accounting_buy_sell_roundtrip',lambda: longstate['position_lots']==0 and longstate['gross_cash_usdt']==D('2') and longstate['fees_usdt']==D('0.203') and longstate['cash_usdt']==D('1.797'))

    short_entry=execute_taker(req('short_entry','SELL',2,decision=1000,out=100),make_book('TEST-USDT-SWAP',1000,1500,[(1020,10)],[(1030,10)]))
    short_exit=execute_taker(req('short_exit','BUY',2,decision=2000,out=100),make_book('TEST-USDT-SWAP',2000,2500,[(1000,10)],[(1010,10)]))
    shortfills=list(short_entry.fills+short_exit.fills); shortstate=apply_fills(SPEC,shortfills)
    T('P22_accounting_sell_buy_roundtrip',lambda: shortstate['position_lots']==0 and shortstate['gross_cash_usdt']==D('2') and shortstate['fees_usdt']==D('0.203') and shortstate['cash_usdt']==D('1.797'))
    T('P23_fee_drag_matches_fill_ledger',lambda: longstate['gross_cash_usdt']-longstate['cash_usdt']==longstate['fees_usdt'])
    T('P24_repeat_run_same_ledger_hash',lambda: ledger_hash(list(execute_taker(req('repeat','BUY',3),mb).fills))==ledger_hash(list(execute_taker(req('repeat','BUY',3),mb).fills)))

    n=sum(1 for x in tests if x['pass']); status=PASS if n==24 else REVIEW
    rep={'stage':'SC001-TAKER-KERNEL-SYNTHETIC-VALIDATION','version':'0.1','status':status,'tests_passed':n,'tests_total':24,'tests':tests,'real_market_data_body_accessed':False,'strategy_signal_calculated':False,'promotional_pnl_calculated':False,'july_august_reserved_bodies_accessed':False,'historical_exact_execution_specs_verified':False}
    atomic_json(OUT,rep)
    print(status); print('tests_passed =',n,'/ 24')
    print('real market data body accessed = False')
    print('strategy signal calculated = False')
    print('promotional PnL calculated = False')
    print('July/August reserved bodies accessed = False')
    print('historical exact execution specs verified = False')
    print('report =',OUT)
    return 0 if n==24 else 2

if __name__=='__main__': raise SystemExit(main())
