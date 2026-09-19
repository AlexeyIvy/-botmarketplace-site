from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

STAGE="SC001-B14A-P0-PROSPECTIVE-TRADE-COLLECTOR-V0.1"
SELFTEST_PASS="B14A_P0_COLLECTOR_SELF_TEST_PASS"
SELFTEST_REVIEW="B14A_P0_COLLECTOR_SELF_TEST_REVIEW"
WAITING="B14A_P0_COLLECTION_WAITING"
RUNNING="B14A_P0_COLLECTION_RUNNING"
COMPLETE="B14A_P0_COLLECTION_COMPLETE"
REVIEW="B14A_P0_COLLECTION_REVIEW"

WS_URL="wss://ws.okx.com:8443/ws/v5/public"
OKX_DOMAINS=("https://www.okx.com","https://us.okx.com")

EVENT_EXPIRY_MS=int(datetime(2026,9,25,8,0,tzinfo=timezone.utc).timestamp()*1000)
T0_MS=int(datetime(2026,9,25,7,30,tzinfo=timezone.utc).timestamp()*1000)
CAPTURE_START_MS=int(datetime(2026,9,25,7,29,tzinfo=timezone.utc).timestamp()*1000)
CAPTURE_END_MS=int(datetime(2026,9,25,8,2,tzinfo=timezone.utc).timestamp()*1000)
CONNECT_AT_MS=int(datetime(2026,9,25,7,28,30,tzinfo=timezone.utc).timestamp()*1000)

INSTRUMENTS=(
    ("BTC-USD-260925","FUTURES"),
    ("BTC-USD-SWAP","SWAP"),
    ("ETH-USD-260925","FUTURES"),
    ("ETH-USD-SWAP","SWAP"),
)
EXPECTED_EXPIRY={
    "BTC-USD-260925":EVENT_EXPIRY_MS,
    "ETH-USD-260925":EVENT_EXPIRY_MS,
}

TIMEOUT=30
PING_SECONDS=20
ACK_TIMEOUT_SECONDS=15
STALE_SECONDS=60

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/"docs/research/sc001-b14a-p0-prospective-2026-09-25-headroom-protocol-v0.1.md"
REGISTRY=ROOT/"docs/research/sc001-contamination-registry-v0.29.json"
FREEZE=ROOT/"docs/research/sc001-b14a-p0-collector-implementation-freeze-v0.1.json"

DATA_ROOT=Path(os.environ.get("SC001_DATA_ROOT",str(Path.home()/"sc001_data"))).expanduser().resolve()
OUT_DIR=DATA_ROOT/"SC001_B14A_P0_20260925"
RAW=OUT_DIR/"raw_trades.jsonl"
CONN=OUT_DIR/"connection_events.jsonl"
STATE=OUT_DIR/"collector_state.json"

STOP=False

def now_ms():
    return time.time_ns()//1_000_000

def iso(ms):
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()

def fail(msg):
    raise RuntimeError(msg)

def load_json(p):
    obj=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(obj,dict):
        fail(f"JSON object expected: {p}")
    return obj

def atomic_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(str(p)+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,sort_keys=True)
        f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(tmp,p)

def append_jsonl(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f:
        f.write(json.dumps(obj,ensure_ascii=False,separators=(",",":"))+"\n")
        f.flush(); os.fsync(f.fileno())

def git_blob(p):
    return subprocess.check_output(
        ["git","-C",str(ROOT),"hash-object",str(p.relative_to(ROOT))],
        text=True,
    ).strip()

def require_freeze():
    fr=load_json(FREEZE)
    if fr.get("status")!="FROZEN_BEFORE_B14A_P0_COLLECTION":
        fail("freeze status mismatch")
    checks={
        "runner_git_blob_sha":git_blob(Path(__file__).resolve()),
        "protocol_git_blob_sha":git_blob(PROTOCOL),
        "contamination_registry_git_blob_sha":git_blob(REGISTRY),
    }
    for k,v in checks.items():
        if fr.get(k)!=v:
            fail(f"freeze identity mismatch: {k}")
    if int(fr.get("t0_ms",-1))!=T0_MS:
        fail("T0 mismatch")
    if int(fr.get("capture_start_ms",-1))!=CAPTURE_START_MS or int(fr.get("capture_end_ms",-1))!=CAPTURE_END_MS:
        fail("capture window mismatch")
    if tuple(fr.get("instruments") or ())!=tuple(x[0] for x in INSTRUMENTS):
        fail("instrument freeze mismatch")
    if float(fr.get("headroom_hurdle_bps",-1))!=50.0:
        fail("headroom hurdle mismatch")
    reg=load_json(REGISTRY).get("b14a_p0") or {}
    if reg.get("classification")!="PROSPECTIVE_HEADROOM_PILOT_2026_09_25":
        fail("registry role mismatch")
    if reg.get("raw_trade_capture_authorized") is not True:
        fail("raw trade capture not authorized")
    for k in (
        "convergence_authorized","settlePx_analysis_authorized",
        "execution_model_authorized","pnl_authorized",
        "candidate_id_assignment_authorized","promotional_evidence_authorized"
    ):
        if reg.get(k) is not False:
            fail(f"registry firewall mismatch: {k}")

def import_ws():
    try:
        import websocket
    except Exception as exc:
        raise RuntimeError("python3-websocket/websocket-client dependency missing") from exc
    return websocket

def finite_positive(x):
    try:
        d=Decimal(str(x).strip())
    except (InvalidOperation,ValueError) as exc:
        raise ValueError(f"invalid decimal {x!r}") from exc
    if not d.is_finite() or d<=0:
        raise ValueError(f"non-positive decimal {x!r}")
    return str(x).strip()

def parse_trade(item):
    if not isinstance(item,dict):
        raise ValueError("trade row is not object")
    inst=str(item.get("instId") or "")
    if inst not in {x[0] for x in INSTRUMENTS}:
        raise ValueError(f"unexpected instId {inst!r}")
    ts=int(str(item.get("ts")).strip())
    if ts<=0:
        raise ValueError("invalid ts")
    trade_id=str(item.get("tradeId") or "").strip()
    if not trade_id:
        raise ValueError("missing tradeId")
    side=str(item.get("side") or "")
    if side not in {"buy","sell"}:
        raise ValueError(f"invalid side {side!r}")
    px=finite_positive(item.get("px"))
    sz=finite_positive(item.get("sz"))
    return {
        "instId":inst,
        "tradeId":trade_id,
        "side":side,
        "px":px,
        "sz":sz,
        "ts":ts,
        "source":item.get("source"),
        "count":item.get("count"),
    }

def request_json(url):
    req=urllib.request.Request(url,headers={
        "User-Agent":"BotMarketplace-SC001-B14A-P0/0.1",
        "Accept":"application/json",
    })
    with urllib.request.urlopen(req,timeout=TIMEOUT) as resp:
        raw=resp.read(4_000_001)
    if len(raw)>4_000_000:
        fail("REST response cap")
    return json.loads(raw.decode("utf-8"))

def qualify_instruments():
    out={}
    for inst,typ in INSTRUMENTS:
        last=None
        for domain in OKX_DOMAINS:
            try:
                url=domain+"/api/v5/public/instruments?"+urllib.parse.urlencode({
                    "instType":typ,"instId":inst
                })
                obj=request_json(url)
                if str(obj.get("code"))!="0":
                    fail(f"OKX instrument code {obj.get('code')}")
                rows=obj.get("data") or []
                exact=[r for r in rows if isinstance(r,dict) and r.get("instId")==inst]
                if len(exact)!=1:
                    fail(f"instrument row count {inst}: {len(exact)}")
                r=exact[0]
                if r.get("state")!="live":
                    fail(f"instrument not live {inst}: {r.get('state')}")
                if inst in EXPECTED_EXPIRY:
                    if int(str(r.get("expTime") or "0"))!=EXPECTED_EXPIRY[inst]:
                        fail(f"expiry changed {inst}: {r.get('expTime')}")
                out[inst]={
                    "instType":r.get("instType"),
                    "state":r.get("state"),
                    "expTime":r.get("expTime"),
                    "ctType":r.get("ctType"),
                    "settleCcy":r.get("settleCcy"),
                    "ctVal":r.get("ctVal"),
                    "ctValCcy":r.get("ctValCcy"),
                }
                last=None
                break
            except Exception as exc:
                last=exc
        if last is not None:
            raise RuntimeError(f"instrument qualification failed {inst}: {last}")
    return out

def self_test():
    try:
        require_freeze()
        websocket=import_ws()
        good={
            "instId":"BTC-USD-260925","tradeId":"1","side":"buy",
            "px":"100000","sz":"1","ts":"1790321400000","source":"0"
        }
        row=parse_trade(good)
        if row["instId"]!="BTC-USD-260925":
            fail("valid fixture mismatch")
        bad=dict(good); bad["side"]="x"
        try:
            parse_trade(bad)
        except ValueError:
            pass
        else:
            fail("bad-side fixture accepted")
        bad2=dict(good); bad2["px"]="nan"
        try:
            parse_trade(bad2)
        except ValueError:
            pass
        else:
            fail("bad-price fixture accepted")
        OUT_DIR.mkdir(parents=True,exist_ok=True)
        test=OUT_DIR/".p0_selftest.tmp"
        test.write_text("ok\n",encoding="utf-8")
        if test.read_text(encoding="utf-8")!="ok\n":
            fail("write fixture mismatch")
        test.unlink()
        print(SELFTEST_PASS)
        print("instruments =",[x[0] for x in INSTRUMENTS])
        print("expiry_utc =",iso(EVENT_EXPIRY_MS))
        print("decision_anchor_utc =",iso(T0_MS))
        print("capture_window_utc =",iso(CAPTURE_START_MS),"..",iso(CAPTURE_END_MS))
        print("websocket_client_version =",getattr(websocket,"__version__","unknown"))
        print("basis/convergence/PnL = CLOSED")
        return 0
    except Exception as exc:
        print(SELFTEST_REVIEW)
        print("error =",f"{type(exc).__name__}: {exc}")
        return 2

def stop_handler(signum,frame):
    global STOP
    STOP=True

def wait_until(target_ms):
    while not STOP:
        rem=target_ms-now_ms()
        if rem<=0:
            return
        time.sleep(min(60,max(1,rem/1000)))

def log_conn(event,epoch,**extra):
    t=now_ms()
    append_jsonl(CONN,{
        "stage":STAGE,"event":event,"ts_ms":t,"ts_utc":iso(t),
        "epoch":epoch,**extra
    })

def collect():
    websocket=import_ws()
    require_freeze()

    current=now_ms()
    if current>CAPTURE_END_MS:
        print(REVIEW)
        print("error = capture window already ended")
        return 2

    metadata=qualify_instruments()
    OUT_DIR.mkdir(parents=True,exist_ok=True)

    state={
        "stage":STAGE,
        "status":WAITING if current<CONNECT_AT_MS else RUNNING,
        "started_script_ms":current,
        "started_script_utc":iso(current),
        "expiry_ms":EVENT_EXPIRY_MS,
        "t0_ms":T0_MS,
        "capture_start_ms":CAPTURE_START_MS,
        "capture_end_ms":CAPTURE_END_MS,
        "instrument_metadata":metadata,
        "subscription_ack":False,
        "raw_trade_messages":0,
        "normalized_trade_rows":0,
        "invalid_trade_rows":0,
        "reconnect_count":0,
        "connection_gaps":[],
        "basis_calculated":False,
        "convergence_calculated":False,
        "pnl_calculated":False,
    }
    atomic_json(STATE,state)

    if current<CONNECT_AT_MS:
        print(WAITING,flush=True)
        print("connect_at_utc =",iso(CONNECT_AT_MS),flush=True)
        print("decision_anchor_utc =",iso(T0_MS),flush=True)
        wait_until(CONNECT_AT_MS)

    epoch_no=0
    backoff=1.0
    last_disconnect=None

    while not STOP and now_ms()<=CAPTURE_END_MS+5000:
        epoch_no+=1
        epoch=f"epoch-{epoch_no:04d}"
        ws=None
        connect_ms=now_ms()
        if last_disconnect is not None:
            state["reconnect_count"]+=1
            state["connection_gaps"].append({
                "start_ms":last_disconnect,
                "end_ms":connect_ms,
                "duration_ms":max(0,connect_ms-last_disconnect),
            })
        try:
            log_conn("CONNECT_ATTEMPT",epoch,url=WS_URL)
            ws=websocket.create_connection(
                WS_URL,timeout=TIMEOUT,
                header=["User-Agent: BotMarketplace-SC001-B14A-P0/0.1"],
            )
            ws.settimeout(1.0)
            log_conn("CONNECTED",epoch)
            args=[{"channel":"trades","instId":x[0]} for x in INSTRUMENTS]
            ws.send(json.dumps({
                "id":"b14ap0-sub","op":"subscribe","args":args
            },separators=(",",":")))

            subscribed=set()
            ack_deadline=time.monotonic()+ACK_TIMEOUT_SECONDS
            last_rx=time.monotonic()
            last_ping=time.monotonic()

            while not STOP and now_ms()<=CAPTURE_END_MS+5000:
                mono=time.monotonic()
                if mono-last_ping>=PING_SECONDS:
                    ws.send("ping")
                    last_ping=mono
                if mono-last_rx>=STALE_SECONDS:
                    raise RuntimeError("websocket stale")

                try:
                    raw=ws.recv()
                except websocket.WebSocketTimeoutException:
                    if len(subscribed)<len(INSTRUMENTS) and time.monotonic()>ack_deadline:
                        raise RuntimeError(f"subscription ACK incomplete {len(subscribed)}/4")
                    continue

                if raw is None or raw=="":
                    raise RuntimeError("websocket closed")
                last_rx=time.monotonic()

                if raw=="pong":
                    continue

                try:
                    obj=json.loads(raw)
                except Exception:
                    log_conn("INVALID_JSON",epoch)
                    continue

                if obj.get("event")=="subscribe":
                    arg=obj.get("arg") or {}
                    if arg.get("channel")=="trades" and arg.get("instId") in {x[0] for x in INSTRUMENTS}:
                        subscribed.add(arg.get("instId"))
                        if len(subscribed)==len(INSTRUMENTS):
                            state["subscription_ack"]=True
                            state["status"]=RUNNING
                            atomic_json(STATE,state)
                            print(RUNNING,flush=True)
                            print("subscription_ack = True instruments = 4",flush=True)
                    continue
                if obj.get("event")=="error":
                    raise RuntimeError(f"OKX subscription error: {obj}")

                arg=obj.get("arg") or {}
                if arg.get("channel")!="trades":
                    continue
                data=obj.get("data") or []
                if not isinstance(data,list):
                    continue

                accepted=[]
                for item in data:
                    try:
                        row=parse_trade(item)
                    except Exception:
                        state["invalid_trade_rows"]+=1
                        continue
                    if CAPTURE_START_MS<=row["ts"]<=CAPTURE_END_MS:
                        accepted.append(row)

                if accepted:
                    recv=now_ms()
                    append_jsonl(RAW,{
                        "stage":STAGE,
                        "recv_ms":recv,
                        "recv_utc":iso(recv),
                        "epoch":epoch,
                        "arg":arg,
                        "trades":accepted,
                    })
                    state["raw_trade_messages"]+=1
                    state["normalized_trade_rows"]+=len(accepted)
                    atomic_json(STATE,state)

            break

        except Exception as exc:
            last_disconnect=now_ms()
            log_conn("DISCONNECTED",epoch,error=f"{type(exc).__name__}: {exc}")
            if now_ms()>CAPTURE_END_MS+5000 or STOP:
                break
            time.sleep(backoff)
            backoff=min(30.0,backoff*2)
        finally:
            if ws is not None:
                try: ws.close()
                except Exception: pass

    finished=now_ms()
    state["finished_ms"]=finished
    state["finished_utc"]=iso(finished)
    state["status"]=COMPLETE if finished>=CAPTURE_END_MS else REVIEW
    atomic_json(STATE,state)
    print(state["status"])
    print("subscription_ack =",state["subscription_ack"])
    print("raw_trade_messages =",state["raw_trade_messages"])
    print("normalized_trade_rows =",state["normalized_trade_rows"])
    print("invalid_trade_rows =",state["invalid_trade_rows"])
    print("reconnect_count =",state["reconnect_count"])
    print("basis/convergence/PnL = False")
    print("state =",STATE)
    return 0 if state["status"]==COMPLETE else 2

def main():
    signal.signal(signal.SIGINT,stop_handler)
    signal.signal(signal.SIGTERM,stop_handler)
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("self-test","collect"),required=True)
    args=ap.parse_args()
    return self_test() if args.mode=="self-test" else collect()

if __name__=="__main__":
    raise SystemExit(main())
