from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import signal
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

STAGE="SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.2"
SELFTEST_PASS="B13C_COLLECTOR_V02_SELF_TEST_PASS"
SELFTEST_REVIEW="B13C_COLLECTOR_V02_SELF_TEST_REVIEW"
RUNNING="B13C_COLLECTION_RUNNING"
SOURCE_REVIEW="B13C_COLLECTION_SOURCE_REVIEW"
IMPLEMENTATION_FAIL="B13C_COLLECTION_IMPLEMENTATION_FAIL"
STOPPED="B13C_COLLECTION_STOPPED"

SYMBOLS=(
    "BTCUSDT","ETHUSDT","SOLUSDT","DOGEUSDT","ORDIUSDT","FILUSDT",
    "UNIUSDT","XRPUSDT","LTCUSDT","OPUSDT","BCHUSDT","SUIUSDT",
)
TOPICS=tuple(f"allLiquidation.{s}" for s in SYMBOLS)

REST_BASE="https://api.bybit.com"
WS_URL="wss://stream.bybit.com/v5/public/linear"
TIMEOUT=30
RETRIES=3
MAX_JSON=4_000_000
PING_SECONDS=20
STALE_CONNECTION_SECONDS=60
HEARTBEAT_SECONDS=30
LEGACY_STAGE="SC001-B13C-BYBIT-PROSPECTIVE-LIQUIDATION-COLLECTOR-V0.1"

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-b13c-bybit-prospective-liquidation-collector-protocol-v0.2.md"
REGISTRY=ROOT/"docs/research/sc001-contamination-registry-v0.26.json"
FREEZE=ROOT/"docs/research/sc001-b13c-bybit-prospective-liquidation-collector-implementation-freeze-v0.2.json"

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR=DATA_ROOT/"SC001_B13C_PROSPECTIVE_LIQUIDATIONS"
RAW_DIR=OUT_DIR/"raw"
EVENT_DIR=OUT_DIR/"events"
CONN_DIR=OUT_DIR/"connection"
CONN_LOG=CONN_DIR/"connection_events.jsonl"
STATE=OUT_DIR/"collector_state.json"

STOP_REQUESTED=False

def now_ms()->int:
    return time.time_ns()//1_000_000

def iso_ms(ms:int)->str:
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()

def fail(msg:str)->None:
    raise RuntimeError(msg)

def load_json(path:Path)->dict:
    obj=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        fail(f"JSON object expected: {path}")
    return obj

def atomic_json(path:Path,obj:object)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(str(path)+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp,path)

def append_jsonl(path:Path,obj:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    line=json.dumps(obj,ensure_ascii=False,separators=(",",":"))+"\n"
    with path.open("a",encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())

def git_blob(path:Path)->str:
    return subprocess.check_output(
        ["git","-C",str(ROOT),"hash-object",str(path.relative_to(ROOT))],
        text=True,
    ).strip()

def require_freeze()->dict:
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_B13C_PROSPECTIVE_COLLECTION_V02":
        fail("freeze status mismatch")
    expected={
        "runner_git_blob_sha":git_blob(Path(__file__).resolve()),
        "protocol_git_blob_sha":git_blob(PROTOCOL),
        "contamination_registry_git_blob_sha":git_blob(REGISTRY),
    }
    for k,v in expected.items():
        if fr.get(k)!=v:
            fail(f"freeze identity mismatch: {k}")
    if tuple(fr.get("symbols") or ())!=SYMBOLS:
        fail("frozen symbol universe mismatch")
    if fr.get("websocket_url")!=WS_URL:
        fail("websocket URL mismatch")
    for k in (
        "post_event_return_authorized","pre_event_return_authorized",
        "continuation_reversal_authorized","threshold_selection_authorized",
        "symbol_ranking_authorized","execution_model_authorized",
        "pnl_authorized","candidate_id_assignment_authorized",
        "promotional_evidence_authorized",
    ):
        if fr.get(k) is not False:
            fail(f"freeze firewall mismatch: {k}")

    reg=load_json(REGISTRY).get("b13c_prospective_collection") or {}
    if reg.get("classification")!="PROTECTED_PROSPECTIVE_RAW_LIQUIDATION_STREAM":
        fail("registry role mismatch")
    if tuple(reg.get("symbols") or ())!=SYMBOLS:
        fail("registry symbol mismatch")
    if reg.get("raw_liquidation_event_access_authorized") is not True:
        fail("raw liquidation collection not authorized")
    for k in (
        "post_event_return_authorized","pre_event_return_authorized",
        "continuation_reversal_authorized","threshold_selection_authorized",
        "symbol_ranking_authorized","execution_model_authorized",
        "pnl_authorized","candidate_id_assignment_authorized",
        "promotional_evidence_authorized",
    ):
        if reg.get(k) is not False:
            fail(f"registry firewall mismatch: {k}")
    return fr

def finite_positive_decimal(text)->str:
    try:
        x=Decimal(str(text).strip())
    except (InvalidOperation,ValueError) as exc:
        raise ValueError(f"invalid decimal {text!r}") from exc
    if not x.is_finite() or x<=0:
        raise ValueError(f"non-positive/non-finite decimal {text!r}")
    return format(x,"f")

def normalize_event(item:dict,recv_ms:int,server_ts_ms:int,epoch_id:str)->dict:
    if not isinstance(item,dict):
        raise ValueError("event is not object")
    t=int(str(item.get("T")).strip())
    symbol=str(item.get("s") or "").strip()
    side=str(item.get("S") or "").strip()
    if t<=0:
        raise ValueError("invalid event timestamp")
    if symbol not in SYMBOLS:
        raise ValueError(f"unexpected symbol {symbol!r}")
    if side not in {"Buy","Sell"}:
        raise ValueError(f"unexpected liquidation side {side!r}")
    size=finite_positive_decimal(item.get("v"))
    bankruptcy=finite_positive_decimal(item.get("p"))
    liquidated="LONG_LIQUIDATED" if side=="Buy" else "SHORT_LIQUIDATED"
    canonical="|".join((str(t),symbol,side,size,bankruptcy))
    fp=hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "collector_stage":STAGE,
        "recv_ts_ms":recv_ms,
        "server_ts_ms":server_ts_ms,
        "liquidation_ts_ms":t,
        "symbol":symbol,
        "raw_side":side,
        "liquidated_position_side":liquidated,
        "executed_size_raw":size,
        "bankruptcy_price_raw":bankruptcy,
        "event_fingerprint_sha256":fp,
        "connection_epoch":epoch_id,
    }

def self_test_parser()->None:
    valid={"T":1739502302929,"s":"BTCUSDT","S":"Sell","v":"20000","p":"0.04499"}
    row=normalize_event(valid,1739502303204,1739502303204,"fixture")
    if row["liquidated_position_side"]!="SHORT_LIQUIDATED":
        fail("valid parser fixture side semantics mismatch")

    bad_side=dict(valid); bad_side["S"]="Unknown"
    try:
        normalize_event(bad_side,1,1,"fixture")
    except ValueError:
        pass
    else:
        fail("invalid-side fixture was accepted")

    bad_num=dict(valid); bad_num["v"]="nan"
    try:
        normalize_event(bad_num,1,1,"fixture")
    except ValueError:
        pass
    else:
        fail("invalid numeric fixture was accepted")

def import_websocket():
    try:
        import websocket
    except Exception as exc:
        raise RuntimeError(
            "missing dependency websocket-client; install with: python3 -m pip install --user websocket-client"
        ) from exc
    return websocket

def output_write_selftest()->None:
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    p=OUT_DIR/".collector_selftest.tmp"
    p.write_text("ok\n",encoding="utf-8")
    if p.read_text(encoding="utf-8")!="ok\n":
        fail("output write/read self-test mismatch")
    p.unlink()

def self_test()->int:
    try:
        require_freeze()
        self_test_parser()
        websocket=import_websocket()
        output_write_selftest()
        print(SELFTEST_PASS)
        print("symbols =",len(SYMBOLS))
        print("topics =",len(TOPICS))
        print("websocket_client_version =",getattr(websocket,"__version__","unknown"))
        print("output_dir =",OUT_DIR)
        print("resilience = heartbeat+process_restart_gap_ledger")
        print("strategy outcomes calculated = False")
        return 0
    except Exception as exc:
        print(SELFTEST_REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def request_json(url:str)->dict:
    last=None
    for attempt in range(1,RETRIES+1):
        try:
            req=urllib.request.Request(url,headers={
                "User-Agent":"BotMarketplace-SC001-B13C-Collector/0.2",
                "Accept":"application/json",
            })
            with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
                raw=resp.read(MAX_JSON+1)
            if len(raw)>MAX_JSON:
                fail("REST response cap exceeded")
            return json.loads(raw.decode("utf-8"))
        except Exception as exc:
            last=exc
            if attempt<RETRIES:
                time.sleep(float(attempt))
    raise RuntimeError(f"REST request failed: {last}")

def qualify_symbols()->list[dict]:
    rows=[]
    for symbol in SYMBOLS:
        url=REST_BASE+"/v5/market/instruments-info?"+urllib.parse.urlencode({
            "category":"linear","symbol":symbol
        })
        obj=request_json(url)
        if int(obj.get("retCode",-1))!=0:
            fail(f"Bybit instrument response code {symbol}: {obj.get('retCode')} {obj.get('retMsg')}")
        data=(obj.get("result") or {}).get("list") or []
        exact=[r for r in data if isinstance(r,dict) and r.get("symbol")==symbol]
        if len(exact)!=1:
            fail(f"Bybit exact instrument row mismatch {symbol}: {len(exact)}")
        r=exact[0]
        ok=(
            r.get("contractType")=="LinearPerpetual"
            and r.get("quoteCoin")=="USDT"
            and r.get("status")=="Trading"
        )
        if not ok:
            fail(
                f"Bybit frozen symbol not active LinearPerpetual USDT: "
                f"{symbol} contractType={r.get('contractType')} quoteCoin={r.get('quoteCoin')} status={r.get('status')}"
            )
        rows.append({
            "symbol":symbol,
            "baseCoin":r.get("baseCoin"),
            "quoteCoin":r.get("quoteCoin"),
            "contractType":r.get("contractType"),
            "status":r.get("status"),
            "launchTime":r.get("launchTime"),
        })
    return rows

def initial_state()->tuple[dict,bool]:
    if STATE.exists():
        s=load_json(STATE)
        if s.get("stage") not in {STAGE,LEGACY_STAGE}:
            fail("existing collector state stage mismatch")
        if tuple(s.get("symbols") or ())!=SYMBOLS:
            fail("existing collector state symbol mismatch")
        migrated=s.get("stage")==LEGACY_STAGE
        s["stage"]=STAGE
        s["version"]="0.2"
        s.setdefault("last_heartbeat_ms",s.get("last_message_ms"))
        s.setdefault("process_restart_count",0)
        s.setdefault("cumulative_process_gap_ms",0)
        s.setdefault("process_restart_gaps",[])
        return s,True
    t=now_ms()
    s={
        "stage":STAGE,
        "version":"0.2",
        "status":"INITIALIZED",
        "symbols":list(SYMBOLS),
        "collector_start_ms":t,
        "collector_start_utc":iso_ms(t),
        "connection_epoch_counter":0,
        "connection_status":"DISCONNECTED",
        "last_connect_ms":None,
        "last_disconnect_ms":None,
        "last_message_ms":None,
        "last_heartbeat_ms":t,
        "total_raw_messages":0,
        "total_normalized_events":0,
        "invalid_event_count":0,
        "reconnect_count":0,
        "cumulative_gap_ms":0,
        "process_restart_count":0,
        "cumulative_process_gap_ms":0,
        "process_restart_gaps":[],
        "source_qualified_symbols":0,
        "strategy_outcomes_calculated":False,
    }
    atomic_json(STATE,s)
    return s,False

def record_process_start_gap(s:dict,had_state:bool)->None:
    t=now_ms()
    if had_state:
        prev=s.get("last_heartbeat_ms") or s.get("last_message_ms") or s.get("stopped_ms")
        if prev is not None:
            prev=int(prev)
            gap=max(0,t-prev)
            rec={"start_ms":prev,"end_ms":t,"duration_ms":gap}
            s["process_restart_count"]=int(s.get("process_restart_count",0))+1
            s["cumulative_process_gap_ms"]=int(s.get("cumulative_process_gap_ms",0))+gap
            gaps=s.setdefault("process_restart_gaps",[])
            gaps.append(rec)
            if len(gaps)>1000:
                del gaps[:-1000]
            log_connection("PROCESS_RESTART_GAP","process",**rec)
    s["last_heartbeat_ms"]=t
    atomic_json(STATE,s)

def heartbeat(s:dict)->None:
    s["last_heartbeat_ms"]=now_ms()
    atomic_json(STATE,s)

def save_state(s:dict)->None:
    atomic_json(STATE,s)

def daily_path(root:Path,recv_ms:int)->Path:
    d=datetime.fromtimestamp(recv_ms/1000,tz=timezone.utc).strftime("%Y-%m-%d")
    return root/f"{d}.jsonl"

def log_connection(event:str,epoch_id:str,**extra)->None:
    rec={
        "stage":STAGE,
        "event":event,
        "ts_ms":now_ms(),
        "ts_utc":iso_ms(now_ms()),
        "connection_epoch":epoch_id,
        **extra,
    }
    append_jsonl(CONN_LOG,rec)

def handle_liquidation_message(obj:dict,state:dict,epoch_id:str)->None:
    topic=str(obj.get("topic") or "")
    if topic not in TOPICS:
        return
    recv=now_ms()
    try:
        server_ts=int(str(obj.get("ts")).strip())
    except Exception:
        server_ts=0
    if server_ts<=0:
        state["invalid_event_count"]+=1
        save_state(state)
        return

    raw_record={
        "collector_stage":STAGE,
        "recv_ts_ms":recv,
        "connection_epoch":epoch_id,
        "topic":topic,
        "type":obj.get("type"),
        "server_ts_ms":server_ts,
        "data":obj.get("data"),
    }
    append_jsonl(daily_path(RAW_DIR,recv),raw_record)
    state["total_raw_messages"]+=1

    data=obj.get("data")
    items=data if isinstance(data,list) else [data]
    for item in items:
        try:
            row=normalize_event(item,recv,server_ts,epoch_id)
        except Exception:
            state["invalid_event_count"]+=1
            continue
        append_jsonl(daily_path(EVENT_DIR,recv),row)
        state["total_normalized_events"]+=1

    state["last_message_ms"]=recv
    save_state(state)

def stop_handler(signum,frame):
    global STOP_REQUESTED
    STOP_REQUESTED=True

def run_collector()->int:
    global STOP_REQUESTED
    try:
        require_freeze()
        self_test_parser()
        websocket=import_websocket()
        output_write_selftest()

        metadata=qualify_symbols()
        state,had_state=initial_state()
        record_process_start_gap(state,had_state)
        state["source_qualified_symbols"]=len(metadata)
        state["status"]=RUNNING
        save_state(state)

        print(RUNNING,flush=True)
        print("source_qualified =",len(metadata),"/",len(SYMBOLS),flush=True)
        print("collector_start_utc =",state["collector_start_utc"],flush=True)
        print("raw strategy outcomes = CLOSED",flush=True)

        backoff=1.0

        while not STOP_REQUESTED:
            ws=None
            state["connection_epoch_counter"]=int(state.get("connection_epoch_counter",0))+1
            epoch=f"epoch-{state['connection_epoch_counter']:06d}"
            connect_start=now_ms()

            previous_disconnect=state.get("last_disconnect_ms")
            if previous_disconnect is not None:
                gap=max(0,connect_start-int(previous_disconnect))
                state["cumulative_gap_ms"]=int(state.get("cumulative_gap_ms",0))+gap
                state["reconnect_count"]=int(state.get("reconnect_count",0))+1

            try:
                log_connection("CONNECT_ATTEMPT",epoch,ws_url=WS_URL)
                ws=websocket.create_connection(
                    WS_URL,
                    timeout=TIMEOUT,
                    header=["User-Agent: BotMarketplace-SC001-B13C-Collector/0.2"],
                )
                ws.settimeout(1.0)
                state["connection_status"]="CONNECTED"
                state["last_connect_ms"]=now_ms()
                state["last_heartbeat_ms"]=state["last_connect_ms"]
                save_state(state)
                log_connection("CONNECTED",epoch)

                req_id=f"sub-{state['connection_epoch_counter']}"
                ws.send(json.dumps({"req_id":req_id,"op":"subscribe","args":list(TOPICS)},separators=(",",":")))

                subscribed=False
                ack_deadline=time.monotonic()+15.0
                last_ping=time.monotonic()
                last_control_rx=time.monotonic()

                while not STOP_REQUESTED:
                    now_mono=time.monotonic()
                    if now_mono-last_ping>=PING_SECONDS:
                        ws.send(json.dumps({"req_id":f"ping-{state['connection_epoch_counter']}","op":"ping"},separators=(",",":")))
                        last_ping=now_mono
                        heartbeat(state)

                    if now_mono-last_control_rx>=STALE_CONNECTION_SECONDS:
                        raise RuntimeError("connection stale: no message/pong within timeout")

                    try:
                        raw=ws.recv()
                    except websocket.WebSocketTimeoutException:
                        if not subscribed and time.monotonic()>ack_deadline:
                            raise RuntimeError("subscription ACK timeout")
                        continue

                    if raw is None or raw=="":
                        raise RuntimeError("websocket closed")

                    last_control_rx=time.monotonic()
                    state["last_heartbeat_ms"]=now_ms()
                    save_state(state)
                    try:
                        obj=json.loads(raw)
                    except Exception:
                        log_connection("INVALID_JSON",epoch)
                        continue

                    if obj.get("op")=="subscribe":
                        if obj.get("success") is not True:
                            raise RuntimeError(f"subscription failed: {obj}")
                        if not subscribed:
                            subscribed=True
                            log_connection("SUBSCRIBED",epoch,topic_count=len(TOPICS))
                            print("subscription_ack = True topics =",len(TOPICS),flush=True)
                        continue

                    if obj.get("op") in {"ping","pong"} or obj.get("ret_msg")=="pong":
                        continue

                    handle_liquidation_message(obj,state,epoch)

                backoff=1.0

            except KeyboardInterrupt:
                STOP_REQUESTED=True
            except Exception as exc:
                t=now_ms()
                state["connection_status"]="DISCONNECTED"
                state["last_disconnect_ms"]=t
                state["status"]=RUNNING
                save_state(state)
                log_connection("DISCONNECTED",epoch,error=f"{type(exc).__name__}: {exc}")
                print("collector reconnect:",f"{type(exc).__name__}: {exc}",flush=True)
                if STOP_REQUESTED:
                    break
                time.sleep(backoff)
                backoff=min(backoff*2.0,30.0)
            finally:
                if ws is not None:
                    try:
                        ws.close()
                    except Exception:
                        pass

        t=now_ms()
        state["status"]=STOPPED
        state["connection_status"]="STOPPED"
        state["stopped_ms"]=t
        state["stopped_utc"]=iso_ms(t)
        state["last_heartbeat_ms"]=t
        save_state(state)
        log_connection("STOPPED","none")
        print(STOPPED)
        print("total_raw_messages =",state["total_raw_messages"])
        print("total_normalized_events =",state["total_normalized_events"])
        print("invalid_event_count =",state["invalid_event_count"])
        print("reconnect_count =",state["reconnect_count"])
        print("cumulative_gap_ms =",state["cumulative_gap_ms"])
        print("strategy outcomes calculated = False")
        return 0

    except Exception as exc:
        print(IMPLEMENTATION_FAIL)
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","collect"),required=True)
    args=ap.parse_args()

    signal.signal(signal.SIGTERM,stop_handler)
    signal.signal(signal.SIGINT,stop_handler)

    if args.mode=="self-test":
        return self_test()
    return run_collector()

if __name__=="__main__":
    raise SystemExit(main())
