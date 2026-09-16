from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from sc001_common_accounting_core import Fill
from sc001_normalized_market_schema import BookState

D=Decimal

@dataclass(frozen=True)
class TakerRequest:
    request_id:str
    inst_id:str
    side:str
    qty_lots:int
    decision_ts_ms:int
    decision_to_send_ms:int
    outbound_latency_ms:int
    fee_bps:D
    seq_base:int=0
    def validate(self):
        if not self.request_id or not self.inst_id: raise ValueError('empty request field')
        if self.side not in {'BUY','SELL'}: raise ValueError('bad side')
        if self.qty_lots<=0: raise ValueError('nonpositive qty')
        if min(self.decision_ts_ms,self.decision_to_send_ms,self.outbound_latency_ms,self.seq_base)<0: raise ValueError('negative timing field')
        if self.fee_bps<0: raise ValueError('negative fee')
    @property
    def send_ts_ms(self): return self.decision_ts_ms+self.decision_to_send_ms
    @property
    def activation_ts_ms(self): return self.send_ts_ms+self.outbound_latency_ms

@dataclass(frozen=True)
class TakerExecutionResult:
    request_id:str
    activation_ts_ms:int
    requested_qty_lots:int
    filled_qty_lots:int
    remaining_qty_lots:int
    complete:bool
    fills:tuple[Fill,...]

def execute_taker(req:TakerRequest, book:BookState)->TakerExecutionResult:
    req.validate(); book.validate()
    if req.inst_id!=book.inst_id: raise ValueError('wrong instrument')
    if not book.active_at(req.activation_ts_ms): raise ValueError('book_not_valid_at_activation')
    levels=book.asks if req.side=='BUY' else book.bids
    remaining=req.qty_lots; fills=[]; filled=0
    for i,lv in enumerate(levels):
        if remaining<=0: break
        q=min(remaining,lv.qty_lots)
        fills.append(Fill(
            fill_id=f'{req.request_id}:{i}',
            seq=req.seq_base+i,
            ts_ms=req.activation_ts_ms,
            side=req.side,
            liquidity='taker',
            price_ticks=lv.price_ticks,
            qty_lots=q,
            fee_bps=req.fee_bps,
        ))
        remaining-=q; filled+=q
    return TakerExecutionResult(
        request_id=req.request_id,
        activation_ts_ms=req.activation_ts_ms,
        requested_qty_lots=req.qty_lots,
        filled_qty_lots=filled,
        remaining_qty_lots=remaining,
        complete=(remaining==0),
        fills=tuple(fills),
    )
