"""SC001 pre-period liquidity calibration v0.1.

Engineering/calibration only. Uses official OKX historical 1Dutc candles for the
66 BOTH_ANCHORS_PASS candidates. No strategy signal/PnL. No trade/L2 archives.
"""
from __future__ import annotations

import json, math, os, statistics, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

STAGE="SC001-PREPERIOD-LIQUIDITY-CALIBRATION"
VERSION="0.1"
PASS="SC001_PREPERIOD_LIQUIDITY_CALIBRATION_PASS"
REVIEW="SC001_PREPERIOD_LIQUIDITY_CALIBRATION_REVIEW"
PARENT_PASS="SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE_PASS"
DATES=("2024-02-24","2024-02-25","2024-02-26","2024-02-27","2024-02-28","2024-02-29")
MIN_MEDIAN_QUOTE_VOL=10_000_000.0
TARGET_N=12
DOMAINS=("https://www.okx.com","https://us.okx.com")
PATH="/api/v5/market/history-candles"
UA="BotMarketplace-SC001-LiquidityCalibration/0.1"
TIMEOUT=60
RETRIES=4
RATE_SLEEP=0.13

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
PARENT=DATA_ROOT/"SC001_HISTORICAL_UNIVERSE_SEEDED_PROBE"/"sc001_historical_universe_seeded_probe_report.json"
OUT_DIR=DATA_ROOT/"SC001_PREPERIOD_LIQUIDITY_CALIBRATION"
OUT=OUT_DIR/"sc001_preperiod_liquidity_calibration_report.json"


def fail(s): raise RuntimeError(s)
def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); q=Path(str(p)+".tmp")
    with q.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(q,p)
def load_json(p):
    if not p.exists(): fail(f"missing parent report: {p}")
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): fail("parent report must be object")
    return x

def ts_ms(d):
    return int(datetime.strptime(d,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)

START=ts_ms(DATES[0]); END_EXCL=ts_ms("2024-03-01")
EXPECTED_TS={ts_ms(d):d for d in DATES}


def request_candles(inst):
    # 'after' returns records older than the supplied timestamp.  March-1 UTC
    # therefore gives the six target daily bars plus older bars; we filter exact
    # UTC opening timestamps and admit target dates only.
    params={"instId":inst,"bar":"1Dutc","after":str(END_EXCL),"limit":"10"}
    qs=urlencode(params)
    errors=[]
    for domain in DOMAINS:
        url=domain+PATH+"?"+qs
        for attempt in range(1,RETRIES+1):
            try:
                req=Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
                with urlopen(req,timeout=TIMEOUT) as r:
                    raw=r.read(2_000_001)
                if len(raw)>2_000_000: raise RuntimeError("response_cap")
                obj=json.loads(raw.decode("utf-8"))
                if not isinstance(obj,dict) or obj.get("code")!="0" or not isinstance(obj.get("data"),list):
                    raise RuntimeError("non_success:"+str(obj.get("code") if isinstance(obj,dict) else "not_dict"))
                return obj["data"], url
            except HTTPError as e:
                errors.append(f"{domain}:http:{e.code}")
                if e.code==429 and attempt<RETRIES:
                    time.sleep(1.0*attempt); continue
                break
            except (URLError,TimeoutError,OSError,ValueError,RuntimeError) as e:
                errors.append(f"{domain}:{type(e).__name__}:{e}")
                if attempt<RETRIES:
                    time.sleep(0.5*attempt); continue
                break
    fail(f"history-candles failed {inst}: {errors[-6:]}")


def finite_pos(x):
    v=float(x); return math.isfinite(v) and v>0, v

def finite_nonneg(x):
    v=float(x); return math.isfinite(v) and v>=0, v


def parse_inst(symbol):
    inst=f"{symbol}-USDT-SWAP"
    raw,source=request_candles(inst)
    admitted={}; malformed=[]; duplicate=[]
    for i,row in enumerate(raw):
        try:
            if not isinstance(row,list) or len(row)<9: raise ValueError(f"row_width:{len(row) if isinstance(row,list) else 'not_list'}")
            t=int(row[0]); o=float(row[1]); h=float(row[2]); l=float(row[3]); c=float(row[4]); qv=float(row[7]); confirm=str(row[8])
            if t not in EXPECTED_TS: continue
            if not all(math.isfinite(v) and v>0 for v in (o,h,l,c)): raise ValueError("bad_ohlc")
            if not math.isfinite(qv) or qv<0: raise ValueError("bad_quote_volume")
            if confirm!="1": raise ValueError("unconfirmed")
            if t in admitted:
                duplicate.append(t); continue
            admitted[t]={"date":EXPECTED_TS[t],"ts":t,"o":o,"h":h,"l":l,"c":c,"volCcyQuote":qv,"confirm":confirm}
        except Exception as e:
            malformed.append({"index":i,"error":str(e)})
    rows=[admitted[t] for t in sorted(admitted)]
    vols=[r["volCcyQuote"] for r in rows]
    coverage=len(rows)
    median=statistics.median(vols) if vols else None
    eligible=(coverage==6 and not malformed and not duplicate and median is not None and median>=MIN_MEDIAN_QUOTE_VOL)
    return {
        "symbol":symbol,"instrument":inst,"source_url":source,
        "valid_days":coverage,"expected_days":6,"rows":rows,
        "malformed":malformed,"duplicate_target_timestamps":duplicate,
        "median_daily_quote_volume_usdt":median,
        "mean_daily_quote_volume_usdt":statistics.fmean(vols) if vols else None,
        "min_daily_quote_volume_usdt":min(vols) if vols else None,
        "max_daily_quote_volume_usdt":max(vols) if vols else None,
        "total_quote_volume_usdt":sum(vols) if vols else None,
        "classification":"LIQUIDITY_ELIGIBLE" if eligible else "LIQUIDITY_INELIGIBLE",
    }


def main():
    parent=load_json(PARENT)
    if parent.get("status")!=PARENT_PASS: fail("parent seeded probe not exact PASS")
    symbols=list(parent.get("both_anchor_symbols") or [])
    if len(symbols)<16 or parent.get("both_anchor_count")!=len(symbols): fail("parent both-anchor pool mismatch")
    if len(set(symbols))!=len(symbols): fail("duplicate parent symbols")

    out=[]
    for i,s in enumerate(symbols,1):
        print(f"[{i}/{len(symbols)}] {s}-USDT-SWAP")
        try:
            r=parse_inst(s)
        except Exception as e:
            r={"symbol":s,"instrument":f"{s}-USDT-SWAP","classification":"LIQUIDITY_INELIGIBLE","error":f"{type(e).__name__}: {e}","valid_days":0,"expected_days":6,"median_daily_quote_volume_usdt":None}
        out.append(r)
        print(s,r["classification"],"days=",r.get("valid_days"),"median_quote_usdt=",r.get("median_daily_quote_volume_usdt"))
        time.sleep(RATE_SLEEP)

    eligible=[r for r in out if r.get("classification")=="LIQUIDITY_ELIGIBLE"]
    eligible.sort(key=lambda r:(-float(r["median_daily_quote_volume_usdt"]),str(r["instrument"])))
    for rank,r in enumerate(eligible,1): r["liquidity_rank"]=rank
    proposed=[r["symbol"] for r in eligible[:TARGET_N]] if len(eligible)>=TARGET_N else []
    controls={s:next((r.get("liquidity_rank") for r in eligible if r["symbol"]==s),None) for s in ("BTC","ETH")}
    passed=len(eligible)>=TARGET_N and len(out)==len(symbols) and len(proposed)==TARGET_N
    status=PASS if passed else REVIEW
    rep={
        "stage":STAGE,"version":VERSION,"status":status,
        "parent_report":str(PARENT),"parent_both_anchor_count":len(symbols),
        "calibration_dates":list(DATES),"primary_metric":"median_daily_volCcyQuote_USDT",
        "eligibility_floor_usdt":MIN_MEDIAN_QUOTE_VOL,"eligible_count":len(eligible),
        "proposed_top12_symbols":proposed,"control_ranks":controls,
        "rows":out,
        "official_history_candles_accessed":True,
        "trade_archive_body_downloaded":False,"l2_archive_body_downloaded":False,
        "strategy_signal_calculated":False,"strategy_pnl_calculated":False,
        "promotional_universe_frozen":False,"confirmation_accessed":False,
    }
    atomic_json(OUT,rep)
    print(status)
    print("parent both-anchor instruments =",len(symbols))
    print("liquidity eligible instruments =",len(eligible))
    print("proposed top-12 symbols =",proposed)
    print("BTC/ETH liquidity ranks =",controls)
    print("trade/L2 archive body downloaded = False")
    print("strategy signal/PnL calculated = False")
    print("promotional universe frozen = False")
    print("report =",OUT)
    return 0 if passed else 2

if __name__=="__main__": raise SystemExit(main())
