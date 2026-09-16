from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib, json

D=Decimal

@dataclass(frozen=True)
class LinearSpec:
    inst_id:str
    tick_sz:D
    lot_sz:D
    min_sz:D
    ct_val:D
    settle_ccy:str='USDT'
    ct_type:str='linear'
    def __post_init__(self):
        if self.ct_type!='linear' or self.settle_ccy!='USDT': raise ValueError('unsupported contract')
        if min(self.tick_sz,self.lot_sz,self.min_sz,self.ct_val)<=0: raise ValueError('nonpositive spec')

@dataclass(frozen=True)
class Fill:
    fill_id:str
    seq:int
    ts_ms:int
    side:str
    liquidity:str
    price_ticks:int
    qty_lots:int
    fee_bps:D


def _integral_units(x:D, step:D)->int:
    q=x/step
    qi=q.to_integral_value(rounding=ROUND_HALF_EVEN)
    if q!=qi: raise ValueError('off-grid')
    return int(qi)

def price_to_ticks(price:D,spec:LinearSpec)->int:return _integral_units(price,spec.tick_sz)
def ticks_to_price(t:int,spec:LinearSpec)->D:return D(t)*spec.tick_sz
def qty_to_lots(q:D,spec:LinearSpec)->int:
    if q<spec.min_sz: raise ValueError('below minSz')
    return _integral_units(q,spec.lot_sz)
def lots_to_qty(l:int,spec:LinearSpec)->D:return D(l)*spec.lot_sz

def validate_fill(f:Fill):
    if not f.fill_id or f.seq<0 or f.ts_ms<0 or f.price_ticks<=0 or f.qty_lots<=0: raise ValueError('bad fill')
    if f.side not in {'BUY','SELL'}: raise ValueError('bad side')
    if f.liquidity not in {'maker','taker'}: raise ValueError('bad liquidity')
    if f.fee_bps<0: raise ValueError('negative fee unsupported')

def apply_fills(spec:LinearSpec,fills:list[Fill]):
    seen=set(); pos_lots=0; cash=D('0'); gross_cash=D('0'); fees=D('0')
    ordered=sorted(fills,key=lambda x:(x.ts_ms,x.seq))
    for f in ordered:
        validate_fill(f)
        if f.fill_id in seen: raise ValueError('duplicate fill_id')
        seen.add(f.fill_id)
        price=ticks_to_price(f.price_ticks,spec)
        contracts=lots_to_qty(f.qty_lots,spec)
        notional=price*contracts*spec.ct_val
        fee=notional*f.fee_bps/D('10000')
        signed= f.qty_lots if f.side=='BUY' else -f.qty_lots
        pos_lots += signed
        gross_cash += -notional if f.side=='BUY' else notional
        cash += (-notional-fee) if f.side=='BUY' else (notional-fee)
        fees += fee
    return {'position_lots':pos_lots,'gross_cash_usdt':gross_cash,'fees_usdt':fees,'cash_usdt':cash,'ordered_fills':ordered}

def equity_usdt(spec:LinearSpec,state:dict,mark_ticks:int)->D:
    pos_contracts=lots_to_qty(abs(state['position_lots']),spec)
    signed=D(1) if state['position_lots']>=0 else D(-1)
    mark=ticks_to_price(mark_ticks,spec)
    return state['cash_usdt'] + signed*pos_contracts*spec.ct_val*mark

def causal_visible(observed_ts_ms:int,decision_ts_ms:int)->bool:
    return observed_ts_ms<=decision_ts_ms

def ledger_hash(fills:list[Fill])->str:
    rows=[{'fill_id':f.fill_id,'seq':f.seq,'ts_ms':f.ts_ms,'side':f.side,'liquidity':f.liquidity,'price_ticks':f.price_ticks,'qty_lots':f.qty_lots,'fee_bps':str(f.fee_bps)} for f in sorted(fills,key=lambda x:(x.ts_ms,x.seq))]
    b=(json.dumps(rows,sort_keys=True,separators=(',',':'))+'\n').encode()
    return hashlib.sha256(b).hexdigest()
