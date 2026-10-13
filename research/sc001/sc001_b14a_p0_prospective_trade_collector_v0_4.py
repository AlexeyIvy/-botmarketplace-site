"""B14-A v0.4: offline-review version of the complete collector control flow.

Only explicit in-memory test adapters are supplied by this repair. This module
has no network/filesystem implementation and no collection CLI. A future live
adapter, exact prospective identity freeze and user admission are separate gates.
The frozen September 25 v0.3 collector is not imported, changed or reactivated.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
import json
import math
import re

STAGE = "SC001-B14A-P0-PROSPECTIVE-TRADE-COLLECTOR-V0.4-OFFLINE"
STATE_SCHEMA = "sc001.b14a.collector_state.v0.4"
WAITING = "B14A_P0_COLLECTION_WAITING"
RUNNING = "B14A_P0_COLLECTION_RUNNING"
COMPLETE = "B14A_P0_COLLECTION_COMPLETE"
REVIEW = "B14A_P0_COLLECTION_REVIEW"
WS_URL = "wss://ws.okx.com/ws/v5/public"  # Documentation-only; never opened here.
INSTRUMENTS = (
    ("BTC-USD-260925", "FUTURES"), ("BTC-USD-SWAP", "SWAP"),
    ("ETH-USD-260925", "FUTURES"), ("ETH-USD-SWAP", "SWAP"),
)
INSTRUMENT_IDS = tuple(inst for inst, _ in INSTRUMENTS)
EVENT_EXPIRY_MS = 1790323200000
T0_MS = 1790321400000
CAPTURE_START_MS = 1790321340000
CAPTURE_END_MS = 1790323320000
CONNECT_AT_MS = 1790321310000
HEADROOM_HURDLE_BPS = 50.0  # Historical constant only; never calculated here.
ACK_TIMEOUT_SECONDS = 15.0
STALE_SECONDS = 60.0
PING_SECONDS = 20.0
HEARTBEAT_SECONDS = 30.0
EVENT_IDENTITY = {
    "instruments": list(INSTRUMENT_IDS), "expiry_ms": EVENT_EXPIRY_MS,
    "t0_ms": T0_MS, "capture_start_ms": CAPTURE_START_MS,
    "capture_end_ms": CAPTURE_END_MS, "connect_at_ms": CONNECT_AT_MS,
}
IDENTITY_FIELDS = ("instId", "instType", "instFamily", "ctType", "settleCcy",
                   "ctVal", "ctValCcy", "ctMult")


class CollectorError(RuntimeError):
    """A fail-closed source/session validation failure, not a code exception."""


class AckDeadline(CollectorError):
    pass


class ClockError(CollectorError):
    """A broken clock cannot be repaired by reconnecting."""


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise CollectorError("invalid " + name)
    return value


def timestamp_ms(value, name="timestamp"):
    """Require exact integer milliseconds, not seconds, bools or floats."""
    if type(value) is int:
        value = str(value)
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{13}", value):
        raise CollectorError("invalid millisecond " + name)
    return int(value)


def finite_positive(value):
    if not isinstance(value, str) or not value or value != value.strip():
        raise CollectorError("invalid decimal representation")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise CollectorError("invalid decimal") from exc
    if not number.is_finite() or number <= 0:
        raise CollectorError("non-positive or non-finite decimal")
    return number


def validate_expectations(expected):
    """Explicit fixture expectations are not live instrument qualification."""
    if not isinstance(expected, dict) or set(expected) != set(INSTRUMENT_IDS):
        raise CollectorError("exact four-instrument expectations required")
    for inst, typ in INSTRUMENTS:
        row = expected[inst]
        if not isinstance(row, dict) or any(k not in row for k in IDENTITY_FIELDS):
            raise CollectorError("incomplete expected identity")
        family = inst.split("-")[0] + "-USD"
        required = {"instId": inst, "instType": typ, "instFamily": family,
                    "ctType": "inverse", "settleCcy": family.split("-")[0],
                    "ctValCcy": "USD"}
        if any(row[k] != value for k, value in required.items()):
            raise CollectorError("expected identity changes frozen product mapping")
        finite_positive(row["ctVal"])
        finite_positive(row["ctMult"])


def qualify_instrument(response, expected, as_of_ms):
    """Exact response identity, units and time validation; no source fallback."""
    as_of_ms = timestamp_ms(as_of_ms, "qualification clock")
    if not isinstance(response, dict) or response.get("code") != "0":
        raise CollectorError("instrument response code/schema")
    rows = response.get("data")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise CollectorError("instrument response must contain one exact row")
    row = rows[0]
    for key in IDENTITY_FIELDS:
        if key not in row or key not in expected:
            raise CollectorError("missing instrument field: " + key)
        if key in ("ctVal", "ctMult"):
            if finite_positive(row[key]) != finite_positive(expected[key]):
                raise CollectorError("instrument unit mismatch: " + key)
        elif not isinstance(row[key], str) or row[key] != expected[key]:
            raise CollectorError("instrument identity mismatch: " + key)
    if row.get("state") != "live":
        raise CollectorError("instrument is not live")
    listed = timestamp_ms(row.get("listTime"), "listTime")
    if listed > as_of_ms:
        raise CollectorError("instrument not listed at qualification time")
    if expected["instType"] == "FUTURES":
        expiry = timestamp_ms(row.get("expTime"), "expTime")
        if expiry != EVENT_EXPIRY_MS or not listed < expiry or as_of_ms >= expiry:
            raise CollectorError("instrument expiry/order mismatch")
    elif row.get("expTime") != "":
        raise CollectorError("SWAP expiry must be absent as empty string")
    return {key: row[key] for key in (*IDENTITY_FIELDS, "state", "listTime", "expTime")}


def parse_trade(item, envelope_inst):
    if not isinstance(item, dict) or item.get("instId") != envelope_inst:
        raise CollectorError("trade row/envelope instrument mismatch")
    if envelope_inst not in INSTRUMENT_IDS:
        raise CollectorError("unexpected trade instrument")
    stamp = timestamp_ms(item.get("ts"), "trade ts")
    trade_id = item.get("tradeId")
    if not isinstance(trade_id, str) or not trade_id.strip():
        raise CollectorError("missing tradeId")
    if not isinstance(item.get("side"), str) or item["side"] not in {"buy", "sell"}:
        raise CollectorError("invalid trade side")
    finite_positive(item.get("px"))
    finite_positive(item.get("sz"))
    return {"instId": envelope_inst, "tradeId": trade_id, "side": item["side"],
            "px": item["px"], "sz": item["sz"], "ts": stamp,
            "source": item.get("source"), "count": item.get("count")}


def new_state(now):
    return {
        "schema": STATE_SCHEMA, "stage": STAGE, "event_identity": deepcopy(EVENT_IDENTITY),
        "status": WAITING, "connection_generation": 0, "subscription_ack": False,
        "acknowledged_instruments": [], "ever_subscription_ack": False,
        "connection_gaps": [], "open_connection_gap": None,
        "process_restart_gaps": [], "process_restart_count": 0,
        "reconnect_count": 0, "raw_trade_messages": 0, "normalized_trade_rows": 0,
        "invalid_trade_rows": 0, "last_heartbeat_ms": now,
        "basis_calculated": False, "convergence_calculated": False, "pnl_calculated": False,
    }


def validate_state(state):
    if not isinstance(state, dict) or state.get("schema") != STATE_SCHEMA or state.get("stage") != STAGE:
        raise CollectorError("state identity mismatch; no legacy migration")
    if state.get("event_identity") != EVENT_IDENTITY:
        raise CollectorError("persisted event identity mismatch")
    if not isinstance(state.get("status"), str) or state["status"] not in {WAITING, RUNNING, COMPLETE, REVIEW}:
        raise CollectorError("persisted status mismatch")
    for key in ("connection_generation", "process_restart_count", "reconnect_count",
                "raw_trade_messages", "normalized_trade_rows", "invalid_trade_rows"):
        _integer(state.get(key), key)
    for key in ("subscription_ack", "ever_subscription_ack"):
        if type(state.get(key)) is not bool:
            raise CollectorError("invalid state flag: " + key)
    acks = state.get("acknowledged_instruments")
    if not isinstance(acks, list) or any(x not in INSTRUMENT_IDS for x in acks) or len(set(acks)) != len(acks):
        raise CollectorError("invalid persisted ACK set")
    timestamp_ms(state.get("last_heartbeat_ms"), "last heartbeat")
    for key in ("basis_calculated", "convergence_calculated", "pnl_calculated"):
        if state.get(key) is not False:
            raise CollectorError("state research firewall mismatch")
    for key in ("connection_gaps", "process_restart_gaps"):
        rows = state.get(key)
        if not isinstance(rows, list):
            raise CollectorError("invalid gap ledger")
        for row in rows:
            _validate_gap(row, closed=True)
    gap = state.get("open_connection_gap")
    if gap is not None:
        _validate_gap(gap, closed=False)


def _validate_gap(gap, closed):
    if not isinstance(gap, dict):
        raise CollectorError("invalid gap object")
    start = timestamp_ms(gap.get("start_ms"), "gap start")
    if closed:
        end = timestamp_ms(gap.get("end_ms"), "gap end")
        if end < start or gap.get("duration_ms") != end - start:
            raise CollectorError("invalid closed gap")
    elif gap.get("end_ms") is not None:
        raise CollectorError("open gap cannot have an end")


class Collector:
    """Complete collector flow with explicit clock, transport and sink adapters.

    Adapter contract (no defaults): offline_synthetic=True; now_ms(), monotonic(),
    sleep(seconds), should_stop(), load_state(), save_state(dict), log(dict),
    write_trades(dict), instrument_response(instId, instType), connect(url).
    Socket contract: settimeout(seconds), send(text), recv(), close(). Adapter
    maps a receive timeout to built-in TimeoutError. All sink writes are copies.
    A live adapter is deliberately absent and outside this repair admission.
    """

    def __init__(self, adapter, expected_instruments):
        if getattr(adapter, "offline_synthetic", False) is not True:
            raise CollectorError("OFFLINE_REPAIR_ONLY: no live adapter admitted")
        self.io = adapter
        self.expected = deepcopy(expected_instruments)
        self.state = None
        self.subscribed = set()
        self.connected = False
        self.request_id = None
        self.conn_id = None
        self.ack_deadline = None
        self.last_rx = None
        self.last_ping = None
        self.last_mono = None
        self.last_wall = None

    def wall(self):
        try:
            value = timestamp_ms(self.io.now_ms(), "wall clock")
        except CollectorError as exc:
            raise ClockError("invalid wall clock") from exc
        if self.last_wall is not None and value < self.last_wall:
            raise ClockError("wall clock moved backwards")
        self.last_wall = value
        return value

    def mono(self):
        value = self.io.monotonic()
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ClockError("invalid monotonic clock")
        if self.last_mono is not None and value < self.last_mono:
            raise ClockError("monotonic clock moved backwards")
        self.last_mono = value
        return value

    def save(self):
        self.io.save_state(deepcopy(self.state))

    def log(self, event, **extra):
        self.io.log({"stage": STAGE, "event": event, "ts_ms": self.wall(),
                     "generation": self.state["connection_generation"], **extra})

    def heartbeat(self):
        self.state["last_heartbeat_ms"] = self.wall()
        self.save()

    def open_gap(self, start):
        timestamp_ms(start, "gap start")
        gap = self.state["open_connection_gap"]
        if gap is None:
            self.state["open_connection_gap"] = {"start_ms": start, "end_ms": None}
        else:
            gap["start_ms"] = min(start, gap["start_ms"])

    def reset_session(self):
        self.subscribed = set()
        self.connected = False
        self.conn_id = None
        self.state["subscription_ack"] = False
        self.state["acknowledged_instruments"] = []

    def begin_attempt(self):
        self.reset_session()
        number = self.state["connection_generation"] + 1
        request_id = "b14ap0g" + str(number)
        if not re.fullmatch(r"[A-Za-z0-9]{1,32}", request_id):
            raise CollectorError("subscription generation exhausted")
        self.state["connection_generation"] = number
        if number > 1:
            self.state["reconnect_count"] += 1
        self.request_id = request_id
        self.open_gap(self.wall())
        self.state["status"] = WAITING
        self.save()  # Persist generation before transport or send can occur.
        self.log("CONNECT_ATTEMPT", request_id=request_id)

    def check_deadlines(self):
        now = self.mono()
        if not self.state["subscription_ack"] and now >= self.ack_deadline:
            raise AckDeadline("subscription ACK incomplete at fixed deadline")
        if now - self.last_rx >= STALE_SECONDS:
            raise CollectorError("websocket stale")
        return now

    def receive_ack(self, obj):
        arg = obj.get("arg")
        if (not self.connected or not isinstance(arg, dict)
                or obj.get("id") != self.request_id
                or obj.get("code", "0") != "0"
                or arg.get("channel") != "trades"
                or arg.get("instId") not in INSTRUMENT_IDS):
            self.log("ACK_REJECTED")
            return
        conn_id = obj.get("connId")
        if not isinstance(conn_id, str) or not conn_id or (self.conn_id is not None and conn_id != self.conn_id):
            self.log("ACK_REJECTED")
            return
        self.conn_id = conn_id
        inst = arg["instId"]
        if inst in self.subscribed:
            self.log("ACK_DUPLICATE", instrument=inst)
            return
        self.subscribed.add(inst)
        self.state["acknowledged_instruments"] = sorted(self.subscribed)
        if self.subscribed == set(INSTRUMENT_IDS):
            self.state["subscription_ack"] = True
            self.state["ever_subscription_ack"] = True
            self.state["status"] = RUNNING
            gap = self.state["open_connection_gap"]
            if gap is None:
                raise CollectorError("ready transition has no open availability gap")
            end = self.wall()
            self.state["connection_gaps"].append({
                "start_ms": gap["start_ms"], "end_ms": end,
                "duration_ms": end - gap["start_ms"],
            })
            self.state["open_connection_gap"] = None
            self.log("SUBSCRIPTION_READY", request_id=self.request_id)
        self.save()

    def receive_message(self, raw, received_ms):
        # Receipt time is fixed before persistence or parsing can delay handling.
        received_ms = timestamp_ms(received_ms, "receive timestamp")
        # Both callers and this handler check time: no fast traffic path bypass.
        self.check_deadlines()
        if raw is None or raw == "":
            raise CollectorError("websocket closed")
        self.last_rx = self.mono()
        self.heartbeat()
        if raw == "pong":
            return
        try:
            obj = json.loads(raw)
        except (ValueError, TypeError):
            self.log("INVALID_JSON")
            return
        if not isinstance(obj, dict):
            self.log("INVALID_MESSAGE_OBJECT")
            return
        if obj.get("event") == "subscribe":
            self.receive_ack(obj)
            return
        if obj.get("event") == "error":
            raise CollectorError("source subscription error")
        arg = obj.get("arg")
        if not isinstance(arg, dict) or arg.get("channel") != "trades":
            return
        if not self.state["subscription_ack"]:
            self.log("PRE_ACK_TRADE_DROPPED")
            return
        if arg.get("instId") not in INSTRUMENT_IDS or not isinstance(obj.get("data"), list):
            self.log("INVALID_TRADE_ENVELOPE")
            return
        recv_ms = received_ms
        accepted = []
        for item in obj["data"]:
            try:
                row = parse_trade(item, arg["instId"])
            except CollectorError:
                self.state["invalid_trade_rows"] += 1
                continue
            if CAPTURE_START_MS <= recv_ms <= CAPTURE_END_MS and CAPTURE_START_MS <= row["ts"] <= CAPTURE_END_MS:
                accepted.append(row)
        if accepted:
            self.io.write_trades({"stage": STAGE, "recv_ms": recv_ms,
                                  "generation": self.state["connection_generation"],
                                  "request_id": self.request_id, "arg": deepcopy(arg),
                                  "trades": accepted})
            self.state["raw_trade_messages"] += 1
            self.state["normalized_trade_rows"] += len(accepted)
        self.save()

    def run_connection(self, ws):
        if self.wall() > CAPTURE_END_MS:
            raise CollectorError("event ended during connect")
        self.connected = True
        self.log("CONNECTED")
        self.heartbeat()
        now = self.mono()
        self.ack_deadline = now + ACK_TIMEOUT_SECONDS
        self.last_rx = now
        self.last_ping = now
        ws.send(json.dumps({"id": self.request_id, "op": "subscribe", "args": [
            {"channel": "trades", "instId": inst} for inst in INSTRUMENT_IDS
        ]}, separators=(",", ":")))
        while not self.io.should_stop() and self.wall() <= CAPTURE_END_MS:
            now = self.check_deadlines()
            if now - self.last_ping >= PING_SECONDS:
                ws.send("ping")
                self.last_ping = now
                self.heartbeat()
            # Bound blocking by the fixed ACK deadline, not only socket idleness.
            timeout = min(1.0, self.ack_deadline - now) if not self.state["subscription_ack"] else 1.0
            ws.settimeout(timeout)
            try:
                raw = ws.recv()
            except TimeoutError:
                self.check_deadlines()
                continue
            received_ms = self.wall()  # Immediately after recv; before sink writes.
            self.check_deadlines()  # Includes a recv that returns after deadline.
            if received_ms > CAPTURE_END_MS:
                return
            self.receive_message(raw, received_ms)

    def terminal(self, status, reason):
        self.state["status"] = status
        self.state["finished_ms"] = self.wall()
        self.state["terminal_reason"] = reason
        self.save()
        return deepcopy(self.state)

    def abort_without_retry(self):
        # Use the last validated wall time even if the clock itself failed.
        self.open_gap(self.last_wall)
        self.reset_session()
        self.state["status"] = REVIEW
        self.state["finished_ms"] = self.last_wall
        self.state["terminal_reason"] = "fatal implementation/clock failure; no retry"
        self.save()

    def run(self):
        current = self.wall()
        prior = self.io.load_state()
        if prior is not None:
            validate_state(prior)
            self.state = deepcopy(prior)
            if self.state["status"] == COMPLETE:
                return deepcopy(self.state)  # No writes, qualification or reconnect.
            if current >= CAPTURE_END_MS:
                self.reset_session()
                return self.terminal(REVIEW, "event already ended; no retry")
            if self.state["status"] == REVIEW:
                self.reset_session()
                return deepcopy(self.state)  # No new transport or qualification.
            previous = self.state["last_heartbeat_ms"]
            if previous > current:
                raise CollectorError("persisted heartbeat is in the future")
            self.state["process_restart_count"] += 1
            self.state["process_restart_gaps"].append({
                "start_ms": previous, "end_ms": current, "duration_ms": current - previous,
            })
            self.open_gap(previous)
            self.reset_session()  # Persisted ACK is never session evidence.
            self.state["status"] = WAITING
            self.log("PROCESS_RESTART_GAP", start_ms=previous, end_ms=current)
            self.heartbeat()
        else:
            self.state = new_state(current)
            if current >= CAPTURE_END_MS:
                return self.terminal(REVIEW, "event already ended; no retry")
            self.save()
        try:
            validate_expectations(self.expected)
            metadata = {}
            for inst, typ in INSTRUMENTS:
                metadata[inst] = qualify_instrument(
                    self.io.instrument_response(inst, typ), self.expected[inst], self.wall())
            self.state["instrument_metadata"] = metadata
            self.save()
        except (CollectorError, OSError):
            self.reset_session()
            return self.terminal(REVIEW, "instrument qualification failed closed")
        while not self.io.should_stop() and self.wall() < CONNECT_AT_MS:
            self.heartbeat()
            self.io.sleep(min(HEARTBEAT_SECONDS, (CONNECT_AT_MS - self.wall()) / 1000))
        backoff = 1.0
        while not self.io.should_stop() and self.wall() <= CAPTURE_END_MS:
            self.begin_attempt()
            ws = None
            try:
                ws = self.io.connect(WS_URL)
                self.run_connection(ws)
                if self.wall() > CAPTURE_END_MS and self.state["subscription_ack"]:
                    self.reset_session()
                    return self.terminal(COMPLETE, "capture interval ended after full session ACK")
                break
            except ClockError:
                self.abort_without_retry()
                raise
            except (CollectorError, OSError) as exc:
                self.open_gap(self.wall())
                self.reset_session()
                self.state["status"] = WAITING
                self.state["last_disconnect_ms"] = self.wall()
                self.heartbeat()
                self.log("DISCONNECTED", failure_class=type(exc).__name__)
                if self.wall() >= CAPTURE_END_MS or self.io.should_stop():
                    break
                self.io.sleep(min(backoff, (CAPTURE_END_MS - self.wall()) / 1000))
                backoff = min(30.0, backoff * 2)
            except Exception:
                self.abort_without_retry()
                raise
            finally:
                if ws is not None:
                    try:
                        ws.close()
                    except OSError:
                        self.log("CLOSE_ERROR")
        self.open_gap(self.wall())
        self.reset_session()
        return self.terminal(REVIEW, "stopped or ended without acknowledged final session")


def main():
    print("B14A_OFFLINE_REPAIR_ONLY: no live collector or event is authorized")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
