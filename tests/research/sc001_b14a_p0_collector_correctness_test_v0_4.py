"""Deterministic B14-A full-flow tests. No exchange, disk state or price evidence.

Run: python tests/research/sc001_b14a_p0_collector_correctness_test_v0_4.py
All prices below are hand-authored parser fixtures, never fills or outcomes.
"""
from copy import deepcopy
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "research/sc001/sc001_b14a_p0_prospective_trade_collector_v0_4.py"
spec = importlib.util.spec_from_file_location("b14a_v04", SOURCE)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def metadata_fixtures():
    result = {}
    for inst, typ in b.INSTRUMENTS:
        asset = inst.split("-")[0]
        # Swap unit values here are synthetic expectations, not source evidence.
        result[inst] = {
            "instId": inst, "instType": typ, "instFamily": asset + "-USD",
            "ctType": "inverse", "settleCcy": asset, "ctValCcy": "USD",
            "ctVal": "100" if asset == "BTC" else "10", "ctMult": "1",
            "state": "live", "listTime": "1768551000000",
            "expTime": str(b.EVENT_EXPIRY_MS) if typ == "FUTURES" else "",
        }
    return result


def expectations():
    return {inst: {key: row[key] for key in b.IDENTITY_FIELDS}
            for inst, row in metadata_fixtures().items()}


def ack(inst, request_id=None, conn_id=None, **extra):
    def payload(runtime, ws):
        obj = {"event": "subscribe", "id": request_id or ws.request["id"],
               "arg": {"channel": "trades", "instId": inst},
               "connId": conn_id or "syntheticConnection" + str(ws.number)}
        obj.update(deepcopy(extra))
        return json.dumps(obj)
    return payload


def ack_all():
    return [(0.1, ack(inst)) for inst in b.INSTRUMENT_IDS]


def trade(inst=None, stamp=None):
    inst = inst or b.INSTRUMENT_IDS[0]
    return {"instId": inst, "tradeId": "fixture1", "side": "buy",
            "px": "100", "sz": "1", "ts": str(stamp or b.CAPTURE_START_MS)}


def envelope(row=None, outer_inst=None):
    row = trade() if row is None else row
    return json.dumps({"arg": {"channel": "trades", "instId": outer_inst or row["instId"]},
                       "data": [row]})


def stop(runtime, ws):
    runtime.stop = True
    return "pong"


class ScriptedSocket:
    def __init__(self, runtime, number, actions):
        self.runtime = runtime
        self.number = number
        self.actions = list(actions)
        self.sent = []
        self.timeout = None
        self.timeouts = []
        self.closed = False
        self.request = None

    def settimeout(self, seconds):
        if not 0 < seconds <= 1:
            raise AssertionError("recv not bounded by positive timeout")
        self.timeout = seconds
        self.timeouts.append(seconds)

    def send(self, payload):
        self.sent.append(payload)
        if payload != "ping":
            self.request = json.loads(payload)
            self.runtime.requests.append(deepcopy(self.request))

    def recv(self):
        if self.timeout is None:
            raise AssertionError("recv must set timeout")
        # Default pongs let a fully acknowledged session finish the frozen window.
        delay, payload = self.actions.pop(0) if self.actions else (self.timeout, "pong")
        self.runtime.advance(delay)
        if isinstance(payload, BaseException):
            raise payload
        return payload(self.runtime, self) if callable(payload) else payload

    def close(self):
        self.closed = True


class MemoryRuntime:
    offline_synthetic = True

    def __init__(self, scenarios=None, *, now=b.CAPTURE_START_MS, prior=None, stop_on_disconnect=False):
        self.current_ms = now
        self.monotonic_value = 0.0
        self.scenarios = list(scenarios or [[]])
        self.persisted = deepcopy(prior)
        self.saves = []
        self.events = []
        self.captures = []
        self.requests = []
        self.sockets = []
        self.connects = 0
        self.metadata_calls = 0
        self.stop_on_disconnect = stop_on_disconnect
        self.stop = False
        self.sleeps = []
        self.rows = metadata_fixtures()
        self.connect_delay = 0.0

    def advance(self, seconds):
        self.monotonic_value = round(self.monotonic_value + seconds, 9)
        self.current_ms += int(round(seconds * 1000))

    def now_ms(self):
        return self.current_ms

    def monotonic(self):
        return self.monotonic_value

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.advance(seconds)

    def should_stop(self):
        return self.stop

    def load_state(self):
        return deepcopy(self.persisted)

    def save_state(self, state):
        self.persisted = deepcopy(state)
        self.saves.append(deepcopy(state))

    def log(self, event):
        self.events.append(deepcopy(event))
        if event["event"] == "DISCONNECTED" and self.stop_on_disconnect:
            self.stop = True

    def write_trades(self, message):
        self.captures.append(deepcopy(message))

    def instrument_response(self, inst, typ):
        self.metadata_calls += 1
        return {"code": "0", "data": [deepcopy(self.rows[inst])]}

    def connect(self, url):
        if url != b.WS_URL:
            raise AssertionError("unexpected endpoint")
        self.connects += 1
        self.advance(self.connect_delay)
        if not self.scenarios:
            raise AssertionError("unplanned connection attempt")
        scenario = self.scenarios.pop(0)
        if isinstance(scenario, BaseException):
            raise scenario
        ws = ScriptedSocket(self, self.connects, scenario)
        self.sockets.append(ws)
        return ws


def run(runtime, expected=None):
    # Any hidden network or state-path regression fails, rather than touching it.
    blocked = AssertionError("real network/filesystem evidence access forbidden")
    with patch("builtins.open", side_effect=blocked), \
         patch("socket.socket", side_effect=blocked), \
         patch("socket.create_connection", side_effect=blocked), \
         patch("urllib.request.urlopen", side_effect=blocked):
        return b.Collector(runtime, expectations() if expected is None else expected).run()


class CollectorIntegrationTests(unittest.TestCase):
    def test_all_four_fresh_acks_and_trade_flow(self):
        runtime = MemoryRuntime([ack_all() + [(0.1, envelope())]])
        result = run(runtime)
        self.assertEqual(result["status"], b.COMPLETE)
        self.assertEqual(result["normalized_trade_rows"], 1)
        self.assertEqual(len(runtime.captures), 1)
        self.assertTrue(result["ever_subscription_ack"])
        self.assertFalse(result["subscription_ack"])  # Socket is closed now.
        self.assertIsNone(result["open_connection_gap"])
        self.assertEqual(result["connection_gaps"], [{"start_ms": b.CAPTURE_START_MS,
                         "end_ms": b.CAPTURE_START_MS + 400, "duration_ms": 400}])
        self.assertEqual(len(runtime.requests[0]["args"]), 4)
        self.assertRegex(runtime.requests[0]["id"], r"^[A-Za-z0-9]{1,32}$")
        self.assertTrue(runtime.sockets[0].closed)
        self.assertTrue(any(x == "ping" for x in runtime.sockets[0].sent))

    def test_missing_ack_expires_on_socket_timeouts(self):
        runtime = MemoryRuntime([[(1, TimeoutError())] * 15], stop_on_disconnect=True)
        result = run(runtime)
        self.assertEqual(result["status"], b.REVIEW)
        self.assertFalse(result["ever_subscription_ack"])
        self.assertEqual(runtime.monotonic_value, 15)
        self.assertEqual(result["connection_gaps"], [])
        self.assertEqual(result["open_connection_gap"]["start_ms"], b.CAPTURE_START_MS)
        self.assertEqual(runtime.events[-1]["failure_class"], "AckDeadline")

    def test_partial_and_duplicate_acks_do_not_extend_deadline(self):
        runtime = MemoryRuntime([[(0, ack(b.INSTRUMENT_IDS[0]))] +
                                [(1, ack(b.INSTRUMENT_IDS[0]))] * 15], stop_on_disconnect=True)
        result = run(runtime)
        self.assertFalse(result["ever_subscription_ack"])
        self.assertEqual(runtime.monotonic_value, 15)
        self.assertEqual(len([e for e in runtime.events if e["event"] == "ACK_DUPLICATE"]), 14)

    def test_wrong_request_channel_instrument_connection_and_error_code(self):
        for bad in (ack(b.INSTRUMENT_IDS[3], request_id="oldGeneration"),
                    ack(b.INSTRUMENT_IDS[3], arg={"channel": "books", "instId": b.INSTRUMENT_IDS[3]}),
                    ack("OTHER-USD-SWAP"), ack(b.INSTRUMENT_IDS[3], conn_id="differentSocket"),
                    ack(b.INSTRUMENT_IDS[3], code="60033"), ack(b.INSTRUMENT_IDS[3], connId=None)):
            with self.subTest(bad=bad):
                runtime = MemoryRuntime([ack_all()[:3] + [(0.1, bad)] + [(1, "pong")] * 15],
                                        stop_on_disconnect=True)
                result = run(runtime)
                self.assertFalse(result["ever_subscription_ack"])
                self.assertEqual(result["connection_gaps"], [])
                self.assertTrue(any(e["event"] == "ACK_REJECTED" for e in runtime.events))

    def test_continuous_non_ack_traffic_cannot_bypass_deadline(self):
        messages = ["pong", "not json", "[]", "null", json.dumps({"event": "notice"}),
                    envelope(), json.dumps({"arg": {"channel": "books"}, "data": []})]
        for message in messages:
            with self.subTest(message=message):
                runtime = MemoryRuntime([[(1, message)] * 15], stop_on_disconnect=True)
                result = run(runtime)
                self.assertEqual(runtime.monotonic_value, 15)
                self.assertFalse(result["ever_subscription_ack"])
                self.assertEqual(result["normalized_trade_rows"], 0)
                self.assertEqual(runtime.events[-1]["failure_class"], "AckDeadline")

    def test_exact_deadline_and_late_recv_ack_rejected(self):
        for seconds in (15.0, 15.001, 20.0):
            with self.subTest(seconds=seconds):
                actions = [(0, ack(inst)) for inst in b.INSTRUMENT_IDS[:3]]
                runtime = MemoryRuntime([actions + [(seconds, ack(b.INSTRUMENT_IDS[3]))]], stop_on_disconnect=True)
                result = run(runtime)
                self.assertFalse(result["ever_subscription_ack"])
                self.assertEqual(result["connection_gaps"], [])

    def test_just_before_deadline_is_accepted(self):
        actions = [(0, ack(inst)) for inst in b.INSTRUMENT_IDS[:3]]
        runtime = MemoryRuntime([actions + [(14.999, ack(b.INSTRUMENT_IDS[3]))]])
        result = run(runtime)
        self.assertEqual(result["status"], b.COMPLETE)
        self.assertEqual(result["connection_gaps"][0]["duration_ms"], 14999)

    def test_recv_timeout_is_shortened_near_ack_deadline(self):
        runtime = MemoryRuntime([[(14.9, "pong"), (0.1, TimeoutError())]], stop_on_disconnect=True)
        run(runtime)
        self.assertAlmostEqual(runtime.sockets[0].timeouts[-1], 0.1)

    def test_reconnect_resets_ack_and_rejects_prior_generation(self):
        first = ack_all() + [(0.1, "")]
        second = [(0.1, ack(inst, request_id="b14ap0g1")) for inst in b.INSTRUMENT_IDS]
        runtime = MemoryRuntime([first, second + [(1, "pong")] * 15])
        def log(event):
            runtime.events.append(deepcopy(event))
            if event["event"] == "DISCONNECTED" and event["generation"] == 2:
                runtime.stop = True
        runtime.log = log
        result = run(runtime)
        self.assertEqual([x["id"] for x in runtime.requests], ["b14ap0g1", "b14ap0g2"])
        self.assertEqual(len(result["connection_gaps"]), 1)
        self.assertFalse(result["subscription_ack"])
        self.assertEqual(result["open_connection_gap"]["start_ms"], b.CAPTURE_START_MS + 500)
        second_states = [s for s in runtime.saves if s["connection_generation"] == 2]
        self.assertTrue(second_states)
        self.assertTrue(all(not s["subscription_ack"] for s in second_states))

    def test_failed_connect_partial_reconnect_preserve_earliest_gap(self):
        # A full session disconnects; a connect fails; a partial session times out;
        # only the last session's fourth fresh ACK may close that entire outage.
        first = ack_all() + [(0.1, "")]
        partial = [(0.1, ack(b.INSTRUMENT_IDS[0]))] + [(1, "pong")] * 15
        runtime = MemoryRuntime([first, ConnectionError("synthetic"), partial, ack_all()])
        result = run(runtime)
        self.assertEqual(result["status"], b.COMPLETE)
        self.assertEqual(result["reconnect_count"], 3)
        self.assertEqual(len(result["connection_gaps"]), 2)
        ready_events = [e for e in runtime.events if e["event"] == "SUBSCRIPTION_READY"]
        outage = result["connection_gaps"][1]
        self.assertEqual(outage["start_ms"], b.CAPTURE_START_MS + 500)
        self.assertEqual(outage["end_ms"], ready_events[-1]["ts_ms"])
        self.assertEqual(runtime.sleeps[:3], [1.0, 2.0, 4.0])
        self.assertIsNone(result["open_connection_gap"])
        for s in runtime.saves:
            if s["connection_generation"] in (2, 3):
                self.assertFalse(s["subscription_ack"])
                self.assertEqual(s["open_connection_gap"]["start_ms"], outage["start_ms"])

    def test_first_connect_failures_remain_one_open_gap(self):
        runtime = MemoryRuntime([ConnectionError("a"), ConnectionError("b"), ack_all()])
        result = run(runtime)
        self.assertEqual(result["status"], b.COMPLETE)
        self.assertEqual(len(result["connection_gaps"]), 1)
        self.assertEqual(result["connection_gaps"][0]["start_ms"], b.CAPTURE_START_MS)
        self.assertEqual(result["connection_gaps"][0]["duration_ms"], 3400)

    def test_source_error_socket_close_and_staleness_fail_closed(self):
        for actions in ([(0.1, json.dumps({"event": "error", "code": "60033"}))],
                        [(0.1, "")], [(0.1, None)], [(1, TimeoutError())] * 60):
            with self.subTest(actions=actions[:1]):
                runtime = MemoryRuntime([ack_all() + actions], stop_on_disconnect=True)
                result = run(runtime)
                self.assertEqual(result["status"], b.REVIEW)
                self.assertFalse(result["subscription_ack"])
                self.assertIsNotNone(result["open_connection_gap"])
                self.assertTrue(runtime.sockets[0].closed)

    def test_unexpected_programming_error_is_not_retried(self):
        runtime = MemoryRuntime([ack_all() + [(0.1, TypeError("programmer defect"))]])
        with self.assertRaisesRegex(TypeError, "programmer defect"):
            run(runtime)
        self.assertEqual(runtime.connects, 1)
        self.assertTrue(runtime.sockets[0].closed)
        self.assertFalse(runtime.persisted["subscription_ack"])
        self.assertEqual(runtime.persisted["status"], b.REVIEW)
        self.assertIsNotNone(runtime.persisted["open_connection_gap"])

    def test_invalid_monotonic_clock_aborts_without_retry(self):
        for value in (float("nan"), float("inf"), -1.0, 0.1):
            with self.subTest(value=value):
                def bad_clock(runtime, ws):
                    runtime.monotonic_value = value
                    return "pong"
                runtime = MemoryRuntime([ack_all() + [(0.1, bad_clock)]])
                with self.assertRaises(b.ClockError):
                    run(runtime)
                self.assertEqual(runtime.connects, 1)
                self.assertEqual(runtime.persisted["status"], b.REVIEW)
                self.assertFalse(runtime.persisted["subscription_ack"])
                self.assertTrue(runtime.sockets[0].closed)

    def test_invalid_or_backward_wall_clock_aborts_without_retry(self):
        for value in (None, True, 1790321340, b.CAPTURE_START_MS - 1):
            with self.subTest(value=value):
                def bad_clock(runtime, ws):
                    runtime.current_ms = value
                    return "pong"
                runtime = MemoryRuntime([ack_all() + [(0.1, bad_clock)]])
                with self.assertRaises(b.ClockError):
                    run(runtime)
                self.assertEqual(runtime.connects, 1)
                self.assertEqual(runtime.persisted["status"], b.REVIEW)
                self.assertFalse(runtime.persisted["subscription_ack"])
                self.assertTrue(runtime.sockets[0].closed)

    def test_pre_ack_trade_and_mismatched_envelope_not_admitted(self):
        other = trade(b.INSTRUMENT_IDS[1])
        actions = [(0.1, envelope())] + ack_all() + [(0.1, envelope(other, b.INSTRUMENT_IDS[0]))]
        runtime = MemoryRuntime([actions])
        result = run(runtime)
        self.assertEqual(result["normalized_trade_rows"], 0)
        self.assertEqual(result["invalid_trade_rows"], 1)
        self.assertEqual(runtime.captures, [])

    def test_invalid_trade_rows_and_non_object_messages(self):
        actions = ack_all()
        for field, value in (("px", "NaN"), ("sz", "0"), ("side", "unknown"),
                             ("side", []), ("side", {}), ("ts", "1790321340"), ("ts", True), ("tradeId", "")):
            row = trade(); row[field] = value
            actions.append((0.1, envelope(row)))
        actions.extend([(0.1, "[]"), (0.1, "null"), (0.1, "{broken")])
        runtime = MemoryRuntime([actions])
        result = run(runtime)
        self.assertEqual(result["invalid_trade_rows"], 8)
        self.assertEqual(result["normalized_trade_rows"], 0)

    def test_receive_and_event_time_bounds_both_required(self):
        runtime = MemoryRuntime([ack_all() + [(0.1, envelope())]], now=b.CAPTURE_START_MS - 1000)
        result = run(runtime)
        self.assertEqual(result["normalized_trade_rows"], 0)
        for stamp in (b.CAPTURE_START_MS - 1, b.CAPTURE_END_MS + 1):
            with self.subTest(stamp=stamp):
                rt = MemoryRuntime([ack_all() + [(0.1, envelope(trade(stamp=stamp)))]])
                self.assertEqual(run(rt)["normalized_trade_rows"], 0)

    def test_receipt_timestamp_survives_sink_latency_at_capture_boundaries(self):
        for received_ms, delay, expected_count in ((b.CAPTURE_START_MS - 1, 0.002, 0),
                                                  (b.CAPTURE_END_MS - 1, 0.002, 1)):
            with self.subTest(received_ms=received_ms):
                def slow_message(runtime, ws):
                    runtime.current_ms = received_ms
                    runtime.pending_save_delay = delay
                    return envelope()
                rt = MemoryRuntime([ack_all() + [(0.1, slow_message)]], now=b.CAPTURE_START_MS - 1000)
                rt.pending_save_delay = 0
                original_save = rt.save_state
                def delayed_save(state):
                    original_save(state)
                    latency = rt.pending_save_delay
                    rt.pending_save_delay = 0
                    rt.advance(latency)
                rt.save_state = delayed_save
                result = run(rt)
                self.assertEqual(result["normalized_trade_rows"], expected_count)
                if expected_count:
                    self.assertEqual(rt.captures[0]["recv_ms"], received_ms)

    def test_end_crossed_during_receive_does_not_admit_final_ack(self):
        # Keep the session unready and move wall clock independently to the end.
        def cross_end(runtime, ws):
            runtime.current_ms = b.CAPTURE_END_MS + 1
            return ack(b.INSTRUMENT_IDS[3])(runtime, ws)
        runtime = MemoryRuntime([ack_all()[:3] + [(0.1, cross_end)]])
        result = run(runtime)
        self.assertEqual(result["status"], b.REVIEW)
        self.assertFalse(result["ever_subscription_ack"])
        self.assertEqual(result["connection_gaps"], [])

    def test_end_crossed_during_connect_does_not_subscribe(self):
        runtime = MemoryRuntime([ack_all()])
        runtime.connect_delay = (b.CAPTURE_END_MS - b.CAPTURE_START_MS) / 1000 + 1
        result = run(runtime)
        self.assertEqual(result["status"], b.REVIEW)
        self.assertEqual(runtime.requests, [])
        self.assertIsNotNone(result["open_connection_gap"])

    def test_waiting_heartbeat_and_stopped_before_connection(self):
        runtime = MemoryRuntime([ack_all()], now=b.CONNECT_AT_MS - 60000)
        result = run(runtime)
        self.assertEqual(runtime.sleeps[:2], [30, 30])
        self.assertEqual(result["status"], b.COMPLETE)
        rt = MemoryRuntime(now=b.CONNECT_AT_MS - 1000)
        rt.stop = True
        self.assertEqual(run(rt)["status"], b.REVIEW)
        self.assertEqual(rt.connects, 0)

    def test_deterministic_full_flow_result(self):
        def scenario():
            rt = MemoryRuntime([ack_all() + [(0.1, "")], ConnectionError("fixture"),
                                ack_all() + [(0.1, envelope())]])
            result = run(rt)
            return json.dumps({"state": result, "logs": rt.events, "requests": rt.requests,
                               "captures": rt.captures}, sort_keys=True, separators=(",", ":"))
        self.assertEqual(scenario(), scenario())


class RestartTests(unittest.TestCase):
    def ready_prior(self):
        prior = b.new_state(b.CAPTURE_START_MS - 1000)
        prior.update(status=b.RUNNING, connection_generation=7, subscription_ack=True,
                     acknowledged_instruments=list(b.INSTRUMENT_IDS), ever_subscription_ack=True,
                     normalized_trade_rows=5, raw_trade_messages=2, reconnect_count=6)
        return prior

    def test_restart_resets_ready_and_increments_generation_before_send(self):
        prior = self.ready_prior()
        rt = MemoryRuntime([ack_all()], prior=prior)
        result = run(rt)
        self.assertEqual(result["status"], b.COMPLETE)
        self.assertEqual(rt.requests[0]["id"], "b14ap0g8")
        self.assertEqual(result["normalized_trade_rows"], 5)
        self.assertEqual(result["raw_trade_messages"], 2)
        self.assertEqual(result["process_restart_count"], 1)
        self.assertEqual(result["process_restart_gaps"], [{"start_ms": b.CAPTURE_START_MS - 1000,
                         "end_ms": b.CAPTURE_START_MS, "duration_ms": 1000}])
        self.assertFalse(rt.saves[0]["subscription_ack"])
        self.assertEqual(rt.saves[0]["acknowledged_instruments"], [])
        self.assertEqual(result["connection_gaps"][0]["start_ms"], b.CAPTURE_START_MS - 1000)
        self.assertTrue(prior["subscription_ack"])  # Caller fixture was not mutated.

    def test_restart_keeps_earliest_open_gap(self):
        prior = self.ready_prior()
        prior["open_connection_gap"] = {"start_ms": b.CAPTURE_START_MS - 5000, "end_ms": None}
        rt = MemoryRuntime([ack_all()], prior=prior)
        result = run(rt)
        self.assertEqual(result["connection_gaps"][0]["start_ms"], b.CAPTURE_START_MS - 5000)

    def test_complete_is_no_write_no_qualification_no_connection(self):
        prior = b.new_state(b.CAPTURE_START_MS)
        prior["status"] = b.COMPLETE
        rt = MemoryRuntime(prior=prior, now=b.CAPTURE_END_MS + 1000)
        self.assertEqual(run(rt), prior)
        self.assertEqual((rt.metadata_calls, rt.connects, len(rt.saves)), (0, 0, 0))

    def test_ended_non_complete_and_missing_state_are_terminal(self):
        for prior in (None, self.ready_prior()):
            for stamp in (b.CAPTURE_END_MS, b.CAPTURE_END_MS + 1000):
                with self.subTest(prior=prior is not None, stamp=stamp):
                    rt = MemoryRuntime(prior=prior, now=stamp)
                    result = run(rt)
                    self.assertEqual(result["status"], b.REVIEW)
                    self.assertFalse(result["subscription_ack"])
                    self.assertEqual((rt.connects, rt.metadata_calls), (0, 0))
                    rt2 = MemoryRuntime(prior=result, now=stamp + 1000)
                    self.assertEqual(run(rt2)["status"], b.REVIEW)
                    self.assertEqual((rt2.connects, rt2.metadata_calls), (0, 0))

    def test_terminal_review_before_end_does_not_retry(self):
        prior = b.new_state(b.CAPTURE_START_MS)
        prior["status"] = b.REVIEW
        rt = MemoryRuntime(prior=prior)
        self.assertEqual(run(rt)["status"], b.REVIEW)
        self.assertEqual((rt.connects, rt.metadata_calls), (0, 0))

    def test_invalid_state_and_event_identity_fail_closed(self):
        for field, value in (("schema", "legacy"), ("event_identity", {}),
                             ("connection_generation", -1), ("connection_generation", True),
                             ("last_heartbeat_ms", "not-a-time"), ("pnl_calculated", True),
                             ("open_connection_gap", {"start_ms": 1790321340, "end_ms": None})):
            with self.subTest(field=field):
                prior = self.ready_prior(); prior[field] = value
                rt = MemoryRuntime(prior=prior)
                with self.assertRaises(b.CollectorError):
                    run(rt)
                self.assertEqual(rt.connects, 0)

    def test_generation_overflow_cannot_create_invalid_request_id(self):
        prior = self.ready_prior(); prior["connection_generation"] = 10 ** 30
        rt = MemoryRuntime(prior=prior)
        with self.assertRaisesRegex(b.CollectorError, "generation exhausted"):
            run(rt)
        self.assertEqual(rt.connects, 0)
        self.assertEqual(rt.requests, [])


class QualificationTests(unittest.TestCase):
    def test_positive_all_instrument_identities(self):
        exp = expectations()
        for inst, row in metadata_fixtures().items():
            with self.subTest(inst=inst):
                result = b.qualify_instrument({"code": "0", "data": [row]}, exp[inst], b.CAPTURE_START_MS)
                self.assertEqual(result["instId"], inst)

    def test_exact_identity_and_unit_mismatches_fail_before_transport(self):
        cases = {"instId": "BTC-USD-261030", "instType": "SPOT", "instFamily": "ETH-USD",
                 "ctType": "linear", "settleCcy": "USDT", "ctValCcy": "BTC",
                 "ctVal": "10", "ctMult": "2", "state": "suspend",
                 "expTime": str(b.EVENT_EXPIRY_MS + 1), "listTime": str(b.EVENT_EXPIRY_MS + 1)}
        for key, value in cases.items():
            with self.subTest(field=key):
                rt = MemoryRuntime([ack_all()]); rt.rows[b.INSTRUMENT_IDS[0]][key] = value
                self.assertEqual(run(rt)["status"], b.REVIEW)
                self.assertEqual(rt.connects, 0)
                self.assertEqual(rt.requests, [])

    def test_missing_fields_invalid_units_and_timestamps(self):
        row = metadata_fixtures()[b.INSTRUMENT_IDS[0]]
        exp = expectations()[b.INSTRUMENT_IDS[0]]
        for key in (*b.IDENTITY_FIELDS, "state", "listTime", "expTime"):
            with self.subTest(missing=key):
                bad = dict(row); del bad[key]
                with self.assertRaises(b.CollectorError):
                    b.qualify_instrument({"code": "0", "data": [bad]}, exp, b.CAPTURE_START_MS)
        for field in ("ctVal", "ctMult"):
            for value in (None, "", "NaN", "sNaN", "Infinity", "-Infinity", "0", "-1", 100, True, " 100 "):
                with self.subTest(field=field, value=value):
                    bad = dict(row); bad[field] = value
                    with self.assertRaises(b.CollectorError):
                        b.qualify_instrument({"code": "0", "data": [bad]}, exp, b.CAPTURE_START_MS)
        for field in ("listTime", "expTime"):
            for value in (None, "", "NaN", "0", "-1", "1790323200", "1790323200000000", 1.0, True, "1790323200000.0"):
                with self.subTest(field=field, value=value):
                    bad = dict(row); bad[field] = value
                    with self.assertRaises(b.CollectorError):
                        b.qualify_instrument({"code": "0", "data": [bad]}, exp, b.CAPTURE_START_MS)

    def test_expiry_listing_and_swap_expiry_semantics(self):
        row = metadata_fixtures()[b.INSTRUMENT_IDS[0]]
        exp = expectations()[b.INSTRUMENT_IDS[0]]
        for stamp in (b.EVENT_EXPIRY_MS, b.EVENT_EXPIRY_MS + 1):
            with self.assertRaises(b.CollectorError):
                b.qualify_instrument({"code": "0", "data": [row]}, exp, stamp)
        swap = metadata_fixtures()[b.INSTRUMENT_IDS[1]]
        swap["expTime"] = str(b.EVENT_EXPIRY_MS)
        with self.assertRaises(b.CollectorError):
            b.qualify_instrument({"code": "0", "data": [swap]}, expectations()[b.INSTRUMENT_IDS[1]], b.CAPTURE_START_MS)

    def test_response_schema_duplicate_rows_and_error_codes(self):
        row = metadata_fixtures()[b.INSTRUMENT_IDS[0]]
        exp = expectations()[b.INSTRUMENT_IDS[0]]
        for response in (None, [], {"code": "1", "data": [row]}, {"code": 0, "data": [row]},
                         {"code": "0", "data": []}, {"code": "0", "data": [row, row]},
                         {"code": "0", "data": [None]}, {"code": "0", "data": {}}):
            with self.subTest(response=response):
                with self.assertRaises(b.CollectorError):
                    b.qualify_instrument(response, exp, b.CAPTURE_START_MS)

    def test_invalid_expected_mapping_cannot_select_another_product(self):
        for field, value in (("instType", "SPOT"), ("instFamily", "BTC-USDT"),
                             ("ctType", "linear"), ("ctMult", "NaN")):
            with self.subTest(field=field):
                exp = expectations(); exp[b.INSTRUMENT_IDS[0]][field] = value
                rt = MemoryRuntime()
                self.assertEqual(run(rt, exp)["status"], b.REVIEW)
                self.assertEqual(rt.connects, 0)
        exp = expectations(); del exp[b.INSTRUMENT_IDS[0]]
        self.assertEqual(run(MemoryRuntime(), exp)["status"], b.REVIEW)


class FirewallTests(unittest.TestCase):
    def test_no_live_adapter_and_cli_fail_closed(self):
        rt = MemoryRuntime(); rt.offline_synthetic = False
        with self.assertRaisesRegex(b.CollectorError, "OFFLINE_REPAIR_ONLY"):
            b.Collector(rt, expectations())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(b.main(), 2)
        self.assertIn("no live collector", out.getvalue())

    def test_historical_constants_remain_frozen(self):
        # Legacy file identities are checked separately by static preflight.
        self.assertEqual(b.INSTRUMENTS, (("BTC-USD-260925", "FUTURES"),
                                        ("BTC-USD-SWAP", "SWAP"),
                                        ("ETH-USD-260925", "FUTURES"),
                                        ("ETH-USD-SWAP", "SWAP")))
        self.assertEqual(b.EVENT_EXPIRY_MS, 1790323200000)
        self.assertEqual(b.T0_MS, 1790321400000)
        self.assertEqual(b.CAPTURE_START_MS, 1790321340000)
        self.assertEqual(b.CAPTURE_END_MS, 1790323320000)
        self.assertEqual(b.CONNECT_AT_MS, 1790321310000)
        self.assertEqual(b.HEADROOM_HURDLE_BPS, 50.0)
        self.assertEqual(b.WS_URL, "wss://ws.okx.com/ws/v5/public")

    def test_summary_contains_no_outcome_or_fixture_prices(self):
        rt = MemoryRuntime([ack_all()])
        result = run(rt)
        for key in ("basis_calculated", "convergence_calculated", "pnl_calculated"):
            self.assertIs(result[key], False)
        self.assertEqual(rt.captures, [])
        self.assertNotIn('"px"', json.dumps(result))
        self.assertNotIn('"px"', json.dumps(rt.events))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("B14A_OFFLINE_CORRECTNESS_V04_SYNTHETIC_PASS")
    raise SystemExit(0 if result.wasSuccessful() else 1)
