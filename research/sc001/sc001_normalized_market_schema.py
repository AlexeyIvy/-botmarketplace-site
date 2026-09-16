from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class MarketEvent:
    inst_id: str
    source_event_ts_ms: int
    observed_ts_ms: int
    seq: int
    event_type: str
    def validate(self):
        if not self.inst_id or not self.event_type: raise ValueError('empty event field')
        if min(self.source_event_ts_ms,self.observed_ts_ms,self.seq)<0: raise ValueError('negative event field')
        if self.observed_ts_ms < self.source_event_ts_ms: raise ValueError('observed_before_source')

def strategy_visible(event:MarketEvent, decision_ts_ms:int)->bool:
    event.validate()
    if decision_ts_ms<0: raise ValueError('negative decision_ts')
    return event.observed_ts_ms<=decision_ts_ms

def require_strategy_visible(event:MarketEvent, decision_ts_ms:int):
    if not strategy_visible(event,decision_ts_ms): raise ValueError('future_visibility')

@dataclass(frozen=True)
class BookLevel:
    price_ticks:int
    qty_lots:int
    def validate(self):
        if self.price_ticks<=0 or self.qty_lots<=0: raise ValueError('nonpositive book level')

@dataclass(frozen=True)
class BookState:
    inst_id:str
    valid_from_ts_ms:int
    valid_to_ts_ms:int
    seq:int
    bids:tuple[BookLevel,...]
    asks:tuple[BookLevel,...]
    def validate(self):
        if not self.inst_id: raise ValueError('empty inst_id')
        if self.valid_from_ts_ms<0 or self.valid_to_ts_ms<=self.valid_from_ts_ms or self.seq<0: raise ValueError('bad book interval')
        if not self.bids or not self.asks: raise ValueError('empty book side')
        for x in self.bids+self.asks: x.validate()
        bp=[x.price_ticks for x in self.bids]; ap=[x.price_ticks for x in self.asks]
        if len(set(bp))!=len(bp) or len(set(ap))!=len(ap): raise ValueError('duplicate price level')
        if any(bp[i]<=bp[i+1] for i in range(len(bp)-1)): raise ValueError('bids_not_strict_desc')
        if any(ap[i]>=ap[i+1] for i in range(len(ap)-1)): raise ValueError('asks_not_strict_asc')
        if bp[0]>=ap[0]: raise ValueError('crossed_or_locked_book')
    def active_at(self,ts_ms:int)->bool:
        self.validate(); return self.valid_from_ts_ms<=ts_ms<self.valid_to_ts_ms

def make_book(inst_id,valid_from_ts_ms,valid_to_ts_ms,bids,asks,seq=0):
    b=BookState(inst_id,valid_from_ts_ms,valid_to_ts_ms,seq,tuple(BookLevel(*x) for x in bids),tuple(BookLevel(*x) for x in asks))
    b.validate(); return b
