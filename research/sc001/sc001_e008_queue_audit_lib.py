"""Qualified-source helpers for SC001-E008 queue-model feasibility.
No fills, spread capture, inventory, P&L or profitability.
"""
from __future__ import annotations
import bisect,csv,hashlib,io,itertools,json,math,os,tarfile,zipfile
from array import array
from datetime import datetime,timezone
from pathlib import Path

INST="BTC-USDT-SWAP"
DAYS=("2024-01-14","2024-01-31","2024-02-12","2024-02-13")
TRADE_HEADER=["instrument_name","trade_id","side","price","size","created_time"]
DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
INVENTORY=DATA_ROOT/"SC001_E008_DATA_INVENTORY"/"sc001_e008_data_inventory_report.json"
Q006R=DATA_ROOT/"SC001_DATA_Q006R_OKX_UTC_STITCH"/"sc001_data_q006r_okx_utc_stitch_report.json"

def fail(s): raise RuntimeError(s)
def load_json(p):
    if not p.exists(): fail(f"missing JSON: {p}")
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): fail(f"JSON object expected: {p}")
    return x

def sha256_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(8*1024*1024),b""): h.update(c)
    return h.hexdigest()

def parse_ts_ms(s):
    v=int(str(s).strip()); a=abs(v)
    if a>=10**17:return v//1_000_000
    if a>=10**14:return v//1_000
    if a>=10**11:return v
    if a>=10**9:return v*1000
    fail(f"timestamp scale unresolved: {s!r}")

def day_bounds(day):
    d=datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc); lo=int(d.timestamp()*1000)
    return lo,lo+86_400_000

def qualified_state():
    inv=load_json(INVENTORY)
    if inv.get("status")!="E008_DATA_INVENTORY_PASS" or inv.get("queue_model_inputs_complete") is not True: fail("inventory not PASS")
    for k in ("fill_simulation_calculated","spread_capture_calculated","maker_pnl_calculated","profitability_calculated","tfi_used","q2_accessed","validation_or_final_accessed"):
        if inv.get(k) is not False: fail(f"inventory firewall mismatch: {k}")
    q6=load_json(Q006R)
    if q6.get("stage")!="SC001-DATA-Q006R-OKX-UTC-STITCH" or q6.get("overall_status")!="PASS": fail("Q006R not PASS")
    qrows={x.get("date"):x for x in q6.get("days",[]) if isinstance(x,dict)}
    if not set(DAYS).issubset(qrows): fail("Q006R day set missing")
    return inv,qrows

def _q9_sha(inv,day,batch):
    br=(inv.get("batch_reports") or {}).get(batch) or {}; p=Path(str(br.get("path",""))); rep=load_json(p)
    if rep.get("overall_status")!="PASS": fail(f"Q009{batch} not PASS")
    for r in rep.get("days",[]):
        if isinstance(r,dict) and r.get("date")==day and r.get("status")=="FULL_DAY_PASS":
            d=(r.get("archive") or {}).get("sha256")
            if isinstance(d,str) and len(d)==64:return d
    fail(f"L2 parent SHA missing {day}")

def resolve_l2(inv,day):
    r=next(x for x in inv["days"] if x.get("date")==day); expected=int(r["expected_l2_bytes"]); dig=_q9_sha(inv,day,str(r["batch"]))
    for x in r.get("l2_candidates",[]):
        p=Path(str(x.get("path","")))
        if p.exists() and p.stat().st_size==expected and sha256_file(p)==dig:return p,expected,dig
    fail(f"qualified L2 body missing/hash mismatch {day}")

def _trade_id(row,which):
    if which=="exact":
        x=row.get("exact_archive") or {}; fn,b,d=x.get("filename"),x.get("bytes"),x.get("sha256")
    else:
        x=row.get("neighbor_archive") or {}; dl=x.get("download") or {}; hd=x.get("head") or {}
        fn=x.get("filename"); b=dl.get("bytes") or hd.get("content_length"); d=dl.get("sha256")
    if not isinstance(fn,str) or not isinstance(b,int) or b<=0 or not isinstance(d,str) or len(d)!=64: fail(f"Q006R {which} identity incomplete")
    return fn,b,d

def resolve_trades(qrow):
    ef,eb,ed=_trade_id(qrow,"exact"); nf,nb,nd=_trade_id(qrow,"neighbor")
    ep=DATA_ROOT/"SC001_DATA_Q006_OKX_TRADES"/"archives"/ef
    np=DATA_ROOT/"SC001_DATA_Q006R_OKX_UTC_STITCH"/"neighbor_archives"/nf
    for p,b,d in ((ep,eb,ed),(np,nb,nd)):
        if not p.exists() or p.stat().st_size!=b or sha256_file(p)!=d: fail(f"trade identity mismatch {p}")
    return ep,np

def load_trade_day(day,ep,np):
    lo,hi=day_bounds(day); ts=array("q"); px=array("d"); sz=array("d"); side=bytearray(); mins=bytearray(1440)
    prev_t=prev_id=None; gaps=0
    for p in (ep,np):
        with zipfile.ZipFile(p,"r") as z:
            bad=z.testzip()
            if bad is not None: fail(f"trade ZIP CRC {p.name}: {bad}")
            m=[x for x in z.infolist() if not x.is_dir()]
            if len(m)!=1: fail(f"trade member count {p.name}")
            with z.open(m[0],"r") as raw:
                rd=csv.reader(io.TextIOWrapper(raw,encoding="utf-8",newline="")); hdr=[x.strip().lower() for x in (next(rd,None) or [])]
                if hdr!=TRADE_HEADER: fail(f"trade header mismatch {p.name}")
                for rn,row in enumerate(rd,start=2):
                    if not row:continue
                    if len(row)!=6:fail(f"trade row width {p.name}:{rn}")
                    inst,tidt,sd,pt,st,tt=row; sd=sd.strip().lower(); tid=int(tidt); t=parse_ts_ms(tt); pr=float(pt); s=float(st)
                    if inst.strip()!=INST or sd not in {"buy","sell"} or not math.isfinite(pr) or pr<=0 or not math.isfinite(s) or s<=0:fail(f"invalid trade {p.name}:{rn}")
                    if lo<=t<hi:
                        if prev_t is not None and t<prev_t:fail(f"trade timestamp reversal {day}")
                        if prev_id is not None:
                            if tid<=prev_id:fail(f"trade-id duplicate/backward {day}")
                            if tid!=prev_id+1:gaps+=1
                        prev_t,prev_id=t,tid; ts.append(t);px.append(pr);sz.append(s);side.append(1 if sd=="buy" else 0);mins[(t-lo)//60000]=1
    if not ts or sum(mins)!=1440:fail(f"trade coverage {day}: {sum(mins)}/1440")
    return {"ts":ts,"px":px,"sz":sz,"side":side,"rows":len(ts),"minutes":sum(mins),"id_gaps":gaps}

def parse_level(x):
    if not isinstance(x,list) or len(x)!=3:fail("L2 level shape")
    p=float(x[0]);s=float(x[1]);of=float(x[2]);o=int(round(of))
    if not math.isfinite(p) or not math.isfinite(s) or not math.isfinite(of) or p<=0 or s<0 or o<0 or abs(of-o)>1e-9:fail("invalid L2 level")
    return p,s,o

def apply(book,prices,levels):
    for p,s,o in levels:
        if s==0:
            if p in book:
                del book[p];i=bisect.bisect_left(prices,p)
                if i<len(prices) and prices[i]==p:prices.pop(i)
        else:
            if p not in book:bisect.insort(prices,p)
            book[p]=(s,o)

def iter_l2(path):
    with tarfile.open(path,mode="r|gz") as tf:
        regular=0;last=None
        for m in tf:
            if not m.isfile():continue
            regular+=1
            if regular>1:fail(f"multiple L2 members {path.name}")
            f=tf.extractfile(m)
            if f is None:fail(f"cannot extract {path.name}")
            for raw in f:
                if not raw.strip():continue
                r=json.loads(raw)
                if not isinstance(r,dict) or r.get("instId")!=INST:fail("L2 record/instrument mismatch")
                a=r.get("action");t=int(r.get("ts"));aa=r.get("asks");bb=r.get("bids")
                if a not in {"snapshot","update"} or not isinstance(aa,list) or not isinstance(bb,list):fail("L2 schema mismatch")
                if last is not None and t<last:fail("L2 timestamp reversal")
                last=t;yield t,a,[parse_level(x) for x in aa],[parse_level(x) for x in bb]
        if regular!=1:fail(f"L2 regular member count {path.name}: {regular}")
