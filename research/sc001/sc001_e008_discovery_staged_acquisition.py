"""SC001-E008 staged promotional Discovery data acquisition v1.0.

Data engineering only. Uses ONLY exact URLs/Content-Length identities recorded in
the successful metadata preflight. No fills/spread capture/fees/inventory/P&L.
"""
from __future__ import annotations

import argparse, csv, hashlib, io, json, os, shutil, subprocess, tarfile, zipfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

STAGE = "SC001-E008-DISCOVERY-STAGED-ACQUISITION"
VERSION = "1.0"
PASS_META = "E008_DISCOVERY_METADATA_PREFLIGHT_PASS"
DATA_ROOT = Path(os.environ.get("SC001_DATA_ROOT", str(Path.home()/"sc001_data"))).expanduser().resolve()
META_REPORT = DATA_ROOT/"SC001_E008_DISCOVERY_METADATA_PREFLIGHT"/"sc001_e008_discovery_metadata_preflight_report.json"
ROOT = DATA_ROOT/"SC001_E008_DISCOVERY_DATA"
TRADES_DIR = ROOT/"trades"
L2_DIR = ROOT/"l2"
REPORTS = ROOT/"reports"
MIN_FREE = 10_000_000_000
ALLOWED_HOST = "static.okx.com"
UA = "BotMarketplace-SC001-E008-ACQ/1.0"
REFERER = "https://www.okx.com/historical-data"
TRADE_HEADER = ["instrument_name","trade_id","side","price","size","created_time"]
DISCOVERY_DATES = ("2024-01-06","2024-01-13","2024-01-19","2024-01-24","2024-02-06","2024-02-11","2024-02-21","2024-02-23")
BATCHES = {
    "l2-a": ("2024-01-06","2024-01-13"),
    "l2-b": ("2024-01-19","2024-01-24"),
    "l2-c": ("2024-02-06","2024-02-11"),
    "l2-d": ("2024-02-21","2024-02-23"),
}
TOKENS = {
    "trades":"E008_DISCOVERY_TRADES_ACQUISITION_PASS",
    "l2-a":"E008_DISCOVERY_L2_A_ACQUISITION_PASS",
    "l2-b":"E008_DISCOVERY_L2_B_ACQUISITION_PASS",
    "l2-c":"E008_DISCOVERY_L2_C_ACQUISITION_PASS",
    "l2-d":"E008_DISCOVERY_L2_D_ACQUISITION_PASS",
    "verify":"E008_DISCOVERY_ACQUISITION_VERIFY_PASS",
}

def fail(s): raise RuntimeError(s)
def sha256_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(8*1024*1024),b""): h.update(c)
    return h.hexdigest()
def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); q=Path(str(p)+".tmp")
    with q.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(q,p)
def trusted(url,fn):
    try:
        u=urlparse(url)
        return u.scheme=="https" and (u.hostname or "").lower()==ALLOWED_HOST and Path(u.path).name==fn
    except Exception:return False
def head_check(url,fn,expected):
    if not trusted(url,fn): fail(f"untrusted frozen URL: {fn}")
    req=Request(url,method="HEAD",headers={"User-Agent":UA,"Referer":REFERER})
    with urlopen(req,timeout=90) as r:
        final=r.geturl(); status=int(getattr(r,"status",200)); cl=r.headers.get("Content-Length")
    got=int(cl) if cl and cl.isdigit() else None
    if status!=200 or got!=expected or not trusted(final,fn): fail(f"HEAD identity changed: {fn} status={status} bytes={got} expected={expected}")
    return final

def load_meta():
    if not META_REPORT.exists(): fail(f"missing metadata PASS report: {META_REPORT}")
    x=json.loads(META_REPORT.read_text(encoding="utf-8"))
    if x.get("status")!=PASS_META or x.get("disk_pass") is not True: fail("metadata report not exact PASS")
    if tuple(x.get("discovery_dates") or ())!=DISCOVERY_DATES: fail("Discovery date set mismatch")
    if x.get("promotional_market_data_body_downloaded") is not False: fail("metadata firewall mismatch")
    rows={r.get("date"):r for r in x.get("rows",[]) if isinstance(r,dict)}
    if set(rows)!=set(DISCOVERY_DATES): fail("metadata row set mismatch")
    return x,rows

def specs(meta,rows):
    l2={}; trades={}
    for d in DISCOVERY_DATES:
        r=rows[d]
        z=r.get("l2") or {}; fn=z.get("filename"); url=z.get("url"); b=z.get("bytes")
        if z.get("status")!="PASS" or not isinstance(fn,str) or not isinstance(url,str) or not isinstance(b,int) or b<=0: fail(f"bad L2 metadata {d}")
        l2[d]={"date":d,"filename":fn,"url":url,"bytes":b}
        for t in r.get("trades") or []:
            fn=t.get("filename"); url=t.get("url"); b=t.get("bytes")
            if t.get("status")!="PASS" or not isinstance(fn,str) or not isinstance(url,str) or not isinstance(b,int) or b<=0: fail(f"bad trade metadata {d}")
            prev=trades.get(fn)
            cur={"filename":fn,"url":url,"bytes":b}
            if prev and prev!=cur: fail(f"duplicate trade identity disagreement {fn}")
            trades[fn]=cur
    if sum(z["bytes"] for z in l2.values())!=int(meta.get("expected_l2_total_bytes")): fail("L2 total mismatch")
    if sum(z["bytes"] for z in trades.values())!=int(meta.get("expected_unique_trade_total_bytes")): fail("trade total mismatch")
    for mode,ds in BATCHES.items():
        total=sum(l2[d]["bytes"] for d in ds)
        if total>=1_200_000_000: fail(f"{mode} exceeds frozen 1.2 GB cap: {total}")
    return l2,trades

def ensure_space(bytes_needed):
    free=shutil.disk_usage(DATA_ROOT).free
    if free-bytes_needed<MIN_FREE: fail(f"10 GB reserve would be violated: free={free}, need={bytes_needed}")
def verify_trade(p):
    with zipfile.ZipFile(p,"r") as z:
        bad=z.testzip()
        if bad is not None: fail(f"ZIP CRC failure {p.name}: {bad}")
        ms=[m for m in z.infolist() if not m.is_dir()]
        if len(ms)!=1: fail(f"trade member count {p.name}: {len(ms)}")
        with z.open(ms[0],"r") as raw:
            rd=csv.reader(io.TextIOWrapper(raw,encoding="utf-8",newline="")); hdr=[s.strip().lower() for s in (next(rd,None) or [])]
            if hdr!=TRADE_HEADER: fail(f"trade header mismatch {p.name}: {hdr}")
def verify_l2(p):
    regular=0; uncompressed=0
    with tarfile.open(p,mode="r|gz") as tf:
        for m in tf:
            if not m.isfile(): continue
            regular+=1
            if regular>1: fail(f"multiple regular L2 members {p.name}")
            f=tf.extractfile(m)
            if f is None: fail(f"cannot read L2 member {p.name}")
            while True:
                c=f.read(8*1024*1024)
                if not c: break
                uncompressed+=len(c)
    if regular!=1 or uncompressed<=0: fail(f"invalid L2 tar.gz {p.name}")
    return uncompressed

def verify_local(p,expected,kind):
    if not p.exists() or p.stat().st_size!=expected: return None
    extra=None
    if kind=="trade": verify_trade(p)
    else: extra=verify_l2(p)
    return {"path":str(p),"bytes":expected,"sha256":sha256_file(p),"uncompressed_bytes":extra}
def download_one(spec,dest,kind):
    dest.parent.mkdir(parents=True,exist_ok=True); expected=int(spec["bytes"])
    reuse=verify_local(dest,expected,kind)
    if reuse is not None:
        print("REUSED VERIFIED",dest.name); reuse["download_status"]="REUSED"; return reuse
    if dest.exists(): fail(f"existing final file wrong/corrupt: {dest}")
    part=Path(str(dest)+".part"); start=part.stat().st_size if part.exists() else 0
    if start<0 or start>expected: fail(f"bad partial size {dest.name}: {start}")
    ensure_space(expected-start)
    final=head_check(spec["url"],spec["filename"],expected)
    cmd=["curl","-L","--fail","--retry","5","--retry-delay","3","-C","-","-A",UA,"-e",REFERER,"-o",str(part),final]
    print(f"DOWNLOAD {dest.name} from={start:,} expected={expected:,}")
    cp=subprocess.run(cmd)
    if cp.returncode!=0: fail(f"curl failed rc={cp.returncode} {dest.name}")
    if not part.exists() or part.stat().st_size!=expected: fail(f"download size mismatch {dest.name}: {part.stat().st_size if part.exists() else None} != {expected}")
    os.replace(part,dest)
    out=verify_local(dest,expected,kind)
    if out is None: fail(f"post-download verification failed {dest.name}")
    out["download_status"]="DOWNLOADED" if start==0 else "RESUMED"; out["resumed_from_bytes"]=start
    print("VERIFIED",dest.name,out["sha256"])
    return out

def base_report(mode):
    return {"stage":STAGE,"version":VERSION,"mode":mode,"status":"RUNNING","files":[],"fill_simulation_calculated":False,"spread_capture_calculated":False,"markout_calculated":False,"fees_calculated":False,"inventory_pnl_calculated":False,"profitability_calculated":False,"tfi_used":False,"q2_accessed":False,"validation_or_final_accessed":False,"confirmation_body_accessed":False}
def save(mode,rep): atomic_json(REPORTS/f"sc001_e008_discovery_acquisition_{mode}.json",rep)
def run_stage(mode,l2,trades):
    rep=base_report(mode)
    if mode=="trades":
        selected=[("trade",s,TRADES_DIR/s["filename"]) for s in sorted(trades.values(),key=lambda x:x["filename"])]
    else:
        selected=[]
        for d in BATCHES[mode]:
            s=l2[d]; selected.append(("l2",s,L2_DIR/d/s["filename"]))
    ensure_space(sum(max(0,int(s["bytes"])-(Path(str(p)+".part").stat().st_size if Path(str(p)+".part").exists() else 0)) for _,s,p in selected))
    try:
        for kind,s,p in selected:
            r=download_one(s,p,kind); r.update({"kind":kind,"source_filename":s["filename"],"frozen_url":s["url"]}); rep["files"].append(r); save(mode,rep)
        rep["status"]=TOKENS[mode]; save(mode,rep); print(TOKENS[mode]); print("file_count =",len(rep["files"])); print("fills/spread_capture/fees/inventory_PnL/profitability calculated = False"); print("Q2/Validation/Final/Confirmation = CLOSED"); print("report =",REPORTS/f"sc001_e008_discovery_acquisition_{mode}.json")
    except Exception as e:
        rep["status"]="ERROR"; rep["error"]=repr(e); save(mode,rep); raise

def verify_all(l2,trades):
    rep=base_report("verify"); missing=[]
    for s in sorted(trades.values(),key=lambda x:x["filename"]):
        p=TRADES_DIR/s["filename"]; r=verify_local(p,s["bytes"],"trade")
        print("PASS" if r else "FAIL",p); missing.append(str(p)) if r is None else rep["files"].append({**r,"kind":"trade"})
    for d in DISCOVERY_DATES:
        s=l2[d]; p=L2_DIR/d/s["filename"]; r=verify_local(p,s["bytes"],"l2")
        print("PASS" if r else "FAIL",p); missing.append(str(p)) if r is None else rep["files"].append({**r,"kind":"l2","date":d})
    if missing: rep["status"]="REVIEW"; rep["missing_or_bad"]=missing; save("verify",rep); fail(f"verify failed for {len(missing)} files")
    rep["status"]=TOKENS["verify"]; save("verify",rep); print(TOKENS["verify"]); print("verified_files =",len(rep["files"])); print("promotional profitability calculated = False"); print("Q2/Validation/Final/Confirmation = CLOSED")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("mode",choices=("preflight","trades","l2-a","l2-b","l2-c","l2-d","verify")); a=ap.parse_args()
    meta,rows=load_meta(); l2,trades=specs(meta,rows)
    if a.mode=="preflight":
        print("E008_DISCOVERY_ACQUISITION_PREFLIGHT_PASS")
        print("trade_files =",len(trades),"bytes =",sum(x["bytes"] for x in trades.values()))
        for m,ds in BATCHES.items(): print(m,"dates =",list(ds),"bytes =",sum(l2[d]["bytes"] for d in ds))
        print("promotional bodies downloaded by this mode = False"); return
    ROOT.mkdir(parents=True,exist_ok=True)
    if a.mode=="verify": verify_all(l2,trades)
    else: run_stage(a.mode,l2,trades)
if __name__=="__main__": main()
