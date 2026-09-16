"""SC001-E008 promotional Discovery metadata/HEAD preflight.

Metadata only. No promotional L2/trade body download. No fills, spread capture,
fees, inventory P&L or profitability.
"""
from __future__ import annotations
import json, os, shutil, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

STAGE="SC001-E008-DISCOVERY-METADATA-PREFLIGHT"
VERSION="1.0"
INST="BTC-USDT-SWAP"
FAMILY="BTC-USDT"
INST_TYPE="SWAP"
DISCOVERY_DATES=("2024-01-06","2024-01-13","2024-01-19","2024-01-24","2024-02-06","2024-02-11","2024-02-21","2024-02-23")
CONTAMINATED={"2024-01-05","2024-01-14","2024-01-31","2024-02-12","2024-02-13"}
DOMAINS=("https://www.okx.com","https://us.okx.com")
PATH="/priapi/v5/broker/public/trade-data/download-link"
REFERER="https://www.okx.com/historical-data"
UA="BotMarketplace-SC001-E008-META/1.0"
TIMEOUT=90
RETRIES=3
ALLOWED_HOST="static.okx.com"
RESP_CAP=4_000_000
DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUTDIR=DATA_ROOT/"SC001_E008_DISCOVERY_METADATA_PREFLIGHT"
REPORT=OUTDIR/"sc001_e008_discovery_metadata_preflight_report.json"
MIN_FREE=10_000_000_000

def fail(s): raise RuntimeError(s)
def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); tmp=Path(str(p)+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,p)
def bounds(day):
    d=datetime.strptime(day,"%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(d.timestamp()*1000),int((d+timedelta(days=1)).timestamp()*1000)-1
def next_day(day): return (datetime.strptime(day,"%Y-%m-%d")+timedelta(days=1)).strftime("%Y-%m-%d")
def payload(module,day):
    lo,hi=bounds(day)
    return {"module":module,"instType":INST_TYPE,"instQueryParam":{"instFamilyList":[FAMILY]},"dateQuery":{"dateAggrType":"daily","begin":str(lo),"end":str(hi)}}
def trusted(url,fn):
    try:
        u=urlparse(url)
        return u.scheme=="https" and (u.hostname or "").lower()==ALLOWED_HOST and Path(u.path).name==fn
    except Exception:return False
def request_json(domain,module,day):
    body=json.dumps(payload(module,day),separators=(",",":")).encode()
    url=domain+PATH+"?t="+str(int(time.time()*1000))
    headers={"User-Agent":UA,"Accept":"application/json,*/*","Content-Type":"application/json","Referer":REFERER}
    last=None
    for a in range(1,RETRIES+1):
        try:
            req=Request(url,data=body,method="POST",headers=headers)
            with urlopen(req,timeout=TIMEOUT) as r: raw=r.read(RESP_CAP+1)
            if len(raw)>RESP_CAP: fail("metadata response cap exceeded")
            x=json.loads(raw.decode("utf-8"))
            return x
        except HTTPError as e:
            last=repr(e)
            if e.code==429 and a<RETRIES: time.sleep(1.5*a); continue
            break
        except (URLError,TimeoutError,OSError,ValueError,RuntimeError) as e:
            last=repr(e)
            if a<RETRIES: time.sleep(1.5*a); continue
    return {"code":"ERROR","msg":last or "request failed"}
def links(x):
    out=[]
    if not isinstance(x,dict) or x.get("code") not in ("0",0): return out
    data=x.get("data"); details=data.get("details") if isinstance(data,dict) else None
    if not isinstance(details,list): return out
    for d in details:
        gs=d.get("groupDetails") if isinstance(d,dict) else None
        if not isinstance(gs,list): continue
        for g in gs:
            if not isinstance(g,dict): continue
            fn=g.get("filename") or g.get("fileName"); url=g.get("url")
            if isinstance(fn,str) and isinstance(url,str) and trusted(url,fn): out.append({"filename":fn,"url":url})
    return out
def discover_exact(module,file_day,expected):
    # Query exact date then prior day because historical OKX grouping may surface D under D-1 metadata.
    d=datetime.strptime(file_day,"%Y-%m-%d")
    qdays=(file_day,(d-timedelta(days=1)).strftime("%Y-%m-%d"))
    found=[]
    for qd in qdays:
        for domain in DOMAINS:
            for z in links(request_json(domain,module,qd)):
                if z["filename"]==expected and z["url"] not in found: found.append(z["url"])
            if found: break
        if found: break
    if len(found)!=1: return {"status":"REVIEW","matches":len(found),"filename":expected}
    url=found[0]
    try:
        req=Request(url,method="HEAD",headers={"User-Agent":UA,"Referer":REFERER})
        with urlopen(req,timeout=TIMEOUT) as r:
            final=r.geturl(); status=int(getattr(r,"status",200)); cl=r.headers.get("Content-Length")
        size=int(cl) if cl and cl.isdigit() else None
        ok=status==200 and trusted(final,expected) and isinstance(size,int) and size>0
        return {"status":"PASS" if ok else "REVIEW","filename":expected,"url":url,"final_url":final,"bytes":size,"http_status":status}
    except Exception as e:
        return {"status":"REVIEW","filename":expected,"url":url,"error":repr(e)}

def main():
    if set(DISCOVERY_DATES)&CONTAMINATED: fail("date firewall overlap")
    if len(DISCOVERY_DATES)!=8 or len(set(DISCOVERY_DATES))!=8: fail("discovery date set mismatch")
    rows=[]; all_trade_labels=set()
    for d in DISCOVERY_DATES:
        l2=discover_exact("4",d,f"{INST}-L2orderbook-400lv-{d}.tar.gz")
        labels=(d,next_day(d)); trs=[]
        for td in labels:
            all_trade_labels.add(td)
            trs.append(discover_exact("1",td,f"{INST}-trades-{td}.zip"))
        ok=l2.get("status")=="PASS" and all(x.get("status")=="PASS" for x in trs)
        rows.append({"date":d,"status":"PASS" if ok else "REVIEW","l2":l2,"trades":trs})
        print(f"E008 META {d} {'PASS' if ok else 'REVIEW'} l2_bytes={l2.get('bytes')}")
    l2_bytes=sum(int((r["l2"].get("bytes") or 0)) for r in rows)
    trade_by_name={}
    for r in rows:
        for x in r["trades"]:
            if x.get("status")=="PASS": trade_by_name[x["filename"]]=x
    trade_bytes=sum(int(x.get("bytes") or 0) for x in trade_by_name.values())
    free=shutil.disk_usage(DATA_ROOT).free
    disk_ok=free-l2_bytes-trade_bytes>=MIN_FREE
    passed=len(rows)==8 and all(r["status"]=="PASS" for r in rows) and disk_ok
    status="E008_DISCOVERY_METADATA_PREFLIGHT_PASS" if passed else "E008_DISCOVERY_METADATA_PREFLIGHT_REVIEW"
    rep={"stage":STAGE,"version":VERSION,"status":status,"discovery_dates":list(DISCOVERY_DATES),"rows":rows,"unique_trade_label_count":len(trade_by_name),"expected_l2_total_bytes":l2_bytes,"expected_unique_trade_total_bytes":trade_bytes,"disk_free_bytes":free,"minimum_free_reserve_bytes":MIN_FREE,"disk_pass":disk_ok,"promotional_market_data_body_downloaded":False,"fill_simulation_calculated":False,"spread_capture_calculated":False,"fees_calculated":False,"inventory_pnl_calculated":False,"profitability_calculated":False,"tfi_used":False,"q2_accessed":False,"validation_or_final_accessed":False}
    atomic_json(REPORT,rep)
    print(status)
    print("discovery_day_count =",len(rows))
    print("expected_l2_total_bytes =",l2_bytes)
    print("expected_unique_trade_total_bytes =",trade_bytes)
    print("disk_pass =",disk_ok)
    print("promotional market-data body downloaded = False")
    print("fills/spread_capture/fees/inventory_PnL/profitability calculated = False")
    print("Q2/Validation/Final = CLOSED")
    print("report =",REPORT)
    return 0 if passed else 2
if __name__=="__main__": raise SystemExit(main())
