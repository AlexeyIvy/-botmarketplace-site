"""SC001 seeded historical universe metadata probe.

Metadata/HEAD only. No trade/L2 body download. No signal/PnL.
"""
from __future__ import annotations

import json, os, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

STAGE="SC001-HISTORICAL-UNIVERSE-SEEDED-PROBE"
VERSION="0.1"
PASS="SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE_PASS"
REVIEW="SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE_REVIEW"
DOMAINS=("https://www.okx.com","https://us.okx.com")
PATH="/priapi/v5/broker/public/trade-data/download-link"
REFERER="https://www.okx.com/historical-data"
UA="BotMarketplace-SC001-SeededUniverse/0.1"
ALLOWED_HOST="static.okx.com"
ANCHORS=("2023-12-30","2024-02-29")
MIN_PASS=16
DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
REPO_ROOT=Path(__file__).resolve().parents[2]
SEED=REPO_ROOT/"docs/research/sc001-historical-universe-seed-2023-12-30-v0.1.json"
OUT_DIR=DATA_ROOT/"SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE"
OUT=OUT_DIR/"sc001_historical_universe_seeded_probe_report.json"

def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); q=Path(str(p)+".tmp")
    with q.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(q,p)

def bounds(d):
    x=datetime.strptime(d,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    lo=int(x.timestamp()*1000); hi=int((x+timedelta(days=1)-timedelta(milliseconds=1)).timestamp()*1000)
    return lo,hi

def trusted(url,fn):
    try:
        u=urlparse(url)
        return u.scheme=="https" and (u.hostname or "").lower()==ALLOWED_HOST and Path(u.path).name==fn
    except Exception:return False

def walk(node):
    if isinstance(node,dict):
        fn=node.get("filename") or node.get("fileName")
        url=node.get("url") or node.get("fileUrl") or node.get("downloadUrl")
        if isinstance(fn,str) and isinstance(url,str): yield fn,url
        for v in node.values(): yield from walk(v)
    elif isinstance(node,list):
        for v in node: yield from walk(v)

def request(domain,payload):
    url=domain+PATH+"?t="+str(int(time.time()*1000))
    body=json.dumps(payload,separators=(",",":")).encode()
    req=Request(url,data=body,method="POST",headers={"User-Agent":UA,"Accept":"application/json,*/*","Content-Type":"application/json","Referer":REFERER})
    try:
        with urlopen(req,timeout=60) as r: raw=r.read(8_000_001)
        if len(raw)>8_000_000:return None,"response_cap"
        obj=json.loads(raw.decode("utf-8"))
        if isinstance(obj,dict) and obj.get("code")=="0":return obj,None
        return None,"code:"+str(obj.get("code") if isinstance(obj,dict) else "not_dict")
    except HTTPError as e:return None,f"http:{e.code}"
    except (URLError,TimeoutError,OSError,ValueError) as e:return None,f"{type(e).__name__}:{e}"

def head(url,fn):
    try:
        req=Request(url,method="HEAD",headers={"User-Agent":UA,"Referer":REFERER})
        with urlopen(req,timeout=60) as r:
            final=r.geturl(); status=int(getattr(r,"status",200)); cl=r.headers.get("Content-Length")
        if status==200 and cl and cl.isdigit() and int(cl)>0 and trusted(final,fn):return int(cl),None
        return None,f"head_identity status={status} cl={cl}"
    except Exception as e:return None,f"{type(e).__name__}:{e}"

def probe_one(symbol,date):
    family=f"{symbol}-USDT"; fn=f"{symbol}-USDT-SWAP-trades-{date}.zip"
    lo,hi=bounds(date)
    qdates=(date,(datetime.strptime(date,"%Y-%m-%d")-timedelta(days=1)).strftime("%Y-%m-%d"))
    attempts=[]
    for qd in qdates:
        qlo,qhi=bounds(qd)
        payload={"module":"1","instType":"SWAP","instQueryParam":{"instFamilyList":[family]},"dateQuery":{"dateAggrType":"daily","begin":str(qlo),"end":str(qhi)}}
        for domain in DOMAINS:
            obj,err=request(domain,payload); attempts.append({"query_date":qd,"domain":domain,"ok":obj is not None,"error":err})
            if obj is None:
                if err=="http:429": time.sleep(1.0)
                continue
            matches=[]
            for got,url in walk(obj.get("data")):
                if got==fn and trusted(url,fn): matches.append(url)
            matches=list(dict.fromkeys(matches))
            if len(matches)==1:
                size,herr=head(matches[0],fn)
                if size is not None:return {"pass":True,"filename":fn,"bytes":size,"attempts":attempts}
                attempts.append({"head_error":herr})
            elif len(matches)>1:
                return {"pass":False,"filename":fn,"error":"multiple_exact_urls","attempts":attempts}
        time.sleep(0.03)
    return {"pass":False,"filename":fn,"error":"exact_archive_not_resolved","attempts":attempts}

def main():
    seed=json.loads(SEED.read_text(encoding="utf-8")); symbols=list(seed.get("symbols") or [])
    rows=[]; both=[]
    for i,s in enumerate(symbols,1):
        print(f"[{i}/{len(symbols)}] {s}")
        a=probe_one(s,ANCHORS[0]); b=probe_one(s,ANCHORS[1])
        if a["pass"] and b["pass"]: cls="BOTH_ANCHORS_PASS"; both.append(s)
        elif a["pass"]: cls="EARLY_ONLY"
        elif b["pass"]: cls="LATE_ONLY"
        else: cls="NO_EXACT_ARCHIVE"
        rows.append({"symbol":s,"classification":cls,ANCHORS[0]:a,ANCHORS[1]:b})
        print(s,cls)
    controls=all(next((r for r in rows if r["symbol"]==s),{}).get("classification")=="BOTH_ANCHORS_PASS" for s in ("BTC","ETH"))
    passed=controls and len(both)>=MIN_PASS
    status=PASS if passed else REVIEW
    rep={"stage":STAGE,"version":VERSION,"status":status,"seed_path":str(SEED),"anchor_dates":list(ANCHORS),"both_anchor_count":len(both),"both_anchor_symbols":both,"controls_pass":controls,"rows":rows,"market_data_body_downloaded":False,"strategy_signal_calculated":False,"strategy_pnl_calculated":False,"promotional_universe_frozen":False}
    atomic_json(OUT,rep)
    print(status)
    print("controls BTC+ETH pass =",controls)
    print("both-anchor instruments =",len(both))
    print("both-anchor symbols =",both)
    print("market data body downloaded = False")
    print("strategy signal/PnL calculated = False")
    print("promotional universe frozen = False")
    print("report =",OUT)
    return 0 if passed else 2

if __name__=="__main__": raise SystemExit(main())
