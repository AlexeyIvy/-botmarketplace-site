from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_PATH = REPO_ROOT / "ops/mcp/sc001_b13c_health_adapter_v0_1.py"

spec = importlib.util.spec_from_file_location("sc001_b13c_health_adapter_v0_1", ADAPTER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("adapter import specification unavailable")
adapter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = adapter
spec.loader.exec_module(adapter)


def valid_state(**changes):
    state = {
        "stage": adapter.EXPECTED_STAGE,
        "version": adapter.EXPECTED_VERSION,
        "status": "B13C_COLLECTION_RUNNING",
        "connection_status": "CONNECTED",
        "last_heartbeat_ms": 1_000_000,
        "source_qualified_symbols": 12,
        "reconnect_count": 3,
        "cumulative_gap_ms": 4_000,
        "process_restart_count": 1,
        "cumulative_process_gap_ms": 2_000,
    }
    state.update(changes)
    return state


def state_bytes(state):
    return (json.dumps(state, separators=(",", ":")) + "\n").encode("utf-8")


class ProjectionContractTests(unittest.TestCase):
    def test_public_surface_accepts_no_input(self):
        self.assertEqual(list(inspect.signature(adapter.get_health).parameters), [])
        self.assertEqual(adapter.__all__, ["get_health"])

    def test_allowlist_projection_drops_forbidden_and_unknown_fields(self):
        state = valid_state(
            symbols=["SYNTHETIC_SECRET_SYMBOL"],
            total_raw_messages=999,
            total_normalized_events=888,
            invalid_event_count=777,
            last_message_ms=999_999,
            price="SYNTHETIC_PRICE_MARKER",
            event_size="SYNTHETIC_SIZE_MARKER",
            cluster={"marker": "SYNTHETIC_CLUSTER_MARKER"},
            raw_exception="SYNTHETIC_EXCEPTION_MARKER",
            log_tail="SYNTHETIC_LOG_MARKER",
            nested={"secret": "SYNTHETIC_SECRET_MARKER"},
        )
        result = adapter._state_health(state_bytes(state), 1_000_010)
        self.assertEqual(result["availability"], "AVAILABLE")
        self.assertEqual(result["error"], "NONE")
        self.assertEqual(
            set(result),
            {
                "availability",
                "error",
                "collector_status",
                "connection_state",
                "heartbeat",
                "qualified_symbol_count",
                "reconnect_diagnostics",
                "process_gap_diagnostics",
            },
        )
        rendered = json.dumps(result, sort_keys=True)
        for marker in (
            "SYNTHETIC_SECRET_SYMBOL",
            "SYNTHETIC_PRICE_MARKER",
            "SYNTHETIC_SIZE_MARKER",
            "SYNTHETIC_CLUSTER_MARKER",
            "SYNTHETIC_EXCEPTION_MARKER",
            "SYNTHETIC_LOG_MARKER",
            "SYNTHETIC_SECRET_MARKER",
        ):
            self.assertNotIn(marker, rendered)
        for forbidden_key in (
            "symbols",
            "total_raw_messages",
            "total_normalized_events",
            "invalid_event_count",
            "last_message_ms",
            "price",
            "event_size",
            "cluster",
            "raw_exception",
            "log_tail",
            "nested",
        ):
            self.assertNotIn(forbidden_key, result)

    def test_valid_projection_has_exact_operational_values(self):
        result = adapter._state_health(state_bytes(valid_state()), 1_000_010)
        self.assertEqual(result["collector_status"], "B13C_COLLECTION_RUNNING")
        self.assertEqual(result["connection_state"], "CONNECTED")
        self.assertEqual(result["heartbeat"], {"state": "CURRENT", "age_ms": 10})
        self.assertEqual(result["qualified_symbol_count"], 12)
        self.assertEqual(
            result["reconnect_diagnostics"],
            {"reconnect_count": 3, "cumulative_gap_ms": 4_000},
        )
        self.assertEqual(
            result["process_gap_diagnostics"],
            {
                "process_restart_count": 1,
                "cumulative_process_gap_ms": 2_000,
            },
        )

    def test_stale_heartbeat_is_explicit(self):
        observed = 1_000_000 + adapter.HEARTBEAT_STALE_AFTER_MS + 1
        result = adapter._state_health(state_bytes(valid_state()), observed)
        self.assertEqual(
            result["heartbeat"],
            {
                "state": "STALE",
                "age_ms": adapter.HEARTBEAT_STALE_AFTER_MS + 1,
            },
        )
        self.assertEqual(result["availability"], "AVAILABLE")

    def test_future_heartbeat_is_anomaly_not_fresh(self):
        result = adapter._state_health(
            state_bytes(valid_state(last_heartbeat_ms=1_000_001)), 1_000_000
        )
        self.assertEqual(result["heartbeat"], {"state": "FUTURE", "age_ms": None})
        self.assertEqual(result["availability"], "PARTIAL")
        self.assertEqual(result["error"], "STATE_HEARTBEAT_FUTURE")

    def test_missing_heartbeat_never_falls_back_to_last_message(self):
        state = valid_state(last_message_ms=999_999)
        del state["last_heartbeat_ms"]
        result = adapter._state_health(state_bytes(state), 1_000_000)
        self.assertEqual(result["heartbeat"], {"state": "UNAVAILABLE", "age_ms": None})
        self.assertEqual(result["availability"], "PARTIAL")
        self.assertEqual(result["error"], "STATE_FIELDS_UNAVAILABLE")

    def test_missing_counter_is_unknown_not_zero(self):
        state = valid_state()
        del state["reconnect_count"]
        result = adapter._state_health(state_bytes(state), 1_000_010)
        self.assertIsNone(result["reconnect_diagnostics"]["reconnect_count"])
        self.assertEqual(result["availability"], "PARTIAL")
        self.assertEqual(result["error"], "STATE_FIELDS_UNAVAILABLE")

    def test_connected_state_never_claims_completeness(self):
        process = {
            "availability": "AVAILABLE",
            "error": "NONE",
            "active_state": "active",
            "sub_state": "running",
            "running": True,
        }
        with (
            mock.patch.object(
                adapter,
                "_read_regular_bytes",
                return_value=state_bytes(valid_state()),
            ),
            mock.patch.object(adapter, "_query_fixed_process_state", return_value=process),
            mock.patch.object(adapter.time, "time_ns", return_value=1_000_010_000_000),
        ):
            result = adapter.get_health()
        self.assertEqual(result["state"]["connection_state"], "CONNECTED")
        self.assertEqual(result["evidence_eligibility"], "NOT_EVALUATED")
        rendered = json.dumps(result).lower()
        self.assertNotIn("complete", rendered)
        self.assertNotIn("pass", rendered)

    def test_wrong_identity_fails_closed(self):
        for change in (
            {"stage": "WRONG"},
            {"version": "9.9"},
            {"stage": None},
            {"version": 3},
        ):
            with self.subTest(change=change):
                result = adapter._state_health(
                    state_bytes(valid_state(**change)), 1_000_010
                )
                self.assertEqual(result["availability"], "UNAVAILABLE")
                self.assertEqual(result["error"], "STATE_WRONG_IDENTITY")
                self.assertTrue(all(result[k] is None for k in ("collector_status", "connection_state", "qualified_symbol_count")))

    def test_malformed_and_duplicate_json_fail_closed(self):
        cases = (
            (b"{", "STATE_INVALID_JSON"),
            (b"[]", "STATE_INVALID_JSON"),
            (b"\xff", "STATE_INVALID_UTF8"),
            (
                b'{"stage":"x","stage":"y","version":"0.3"}',
                "STATE_DUPLICATE_KEY",
            ),
        )
        for payload, code in cases:
            with self.subTest(code=code):
                result = adapter._state_health(payload, 1_000_010)
                self.assertEqual(result["availability"], "UNAVAILABLE")
                self.assertEqual(result["error"], code)

    def test_strict_types_reject_bool_negative_and_out_of_range(self):
        cases = (
            {"source_qualified_symbols": True},
            {"source_qualified_symbols": 13},
            {"reconnect_count": -1},
            {"cumulative_gap_ms": False},
            {"process_restart_count": "1"},
            {"last_heartbeat_ms": 10**16 + 1},
            {"connection_status": "MAYBE"},
            {"status": "UNKNOWN_RUNNING"},
        )
        for change in cases:
            with self.subTest(change=change):
                result = adapter._state_health(
                    state_bytes(valid_state(**change)), 1_000_010
                )
                self.assertEqual(result["availability"], "UNAVAILABLE")
                self.assertEqual(result["error"], "STATE_TYPE_ERROR")


class FilesystemBoundaryTests(unittest.TestCase):
    def test_regular_file_read_is_bounded_and_exact(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "state.json"
            payload = state_bytes(valid_state())
            path.write_bytes(payload)
            self.assertEqual(adapter._read_regular_bytes(path), payload)

    def test_oversized_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "state.json"
            path.write_bytes(b"x" * (adapter.MAX_STATE_BYTES + 1))
            with self.assertRaises(adapter.AdapterError) as ctx:
                adapter._read_regular_bytes(path)
            self.assertEqual(ctx.exception.code, "STATE_TOO_LARGE")

    def test_final_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "target.json"
            target.write_bytes(state_bytes(valid_state()))
            link = root / "state.json"
            link.symlink_to(target)
            with self.assertRaises(adapter.AdapterError) as ctx:
                adapter._read_regular_bytes(link)
            self.assertEqual(ctx.exception.code, "STATE_SYMLINK_REJECTED")

    def test_parent_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            real = root / "real"
            real.mkdir()
            (real / "state.json").write_bytes(state_bytes(valid_state()))
            alias = root / "alias"
            alias.symlink_to(real, target_is_directory=True)
            with self.assertRaises(adapter.AdapterError) as ctx:
                adapter._read_regular_bytes(alias / "state.json")
            self.assertIn(ctx.exception.code, {"STATE_SYMLINK_REJECTED", "STATE_NONREGULAR"})

    def test_fifo_and_directory_are_rejected_without_blocking(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fifo = root / "state.fifo"
            os.mkfifo(fifo)
            for path in (fifo, root):
                with self.subTest(path=path):
                    with self.assertRaises(adapter.AdapterError) as ctx:
                        adapter._read_regular_bytes(path)
                    self.assertEqual(ctx.exception.code, "STATE_NONREGULAR")

    def test_missing_and_relative_paths_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing.json"
            with self.assertRaises(adapter.AdapterError) as ctx:
                adapter._read_regular_bytes(missing)
            self.assertEqual(ctx.exception.code, "STATE_MISSING")
        with self.assertRaises(adapter.AdapterError) as ctx:
            adapter._read_regular_bytes(Path("relative.json"))
        self.assertEqual(ctx.exception.code, "STATE_PATH_INVALID")


class FixedProcessContractTests(unittest.TestCase):
    def test_process_query_uses_only_fixed_nonmutating_command(self):
        calls = []

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="ActiveState=active\nSubState=running\n",
                stderr="",
            )

        result = adapter._query_fixed_process_state(fake_run)
        self.assertEqual(result["availability"], "AVAILABLE")
        self.assertTrue(result["running"])
        self.assertEqual(len(calls), 1)
        command, kwargs = calls[0]
        self.assertEqual(command, adapter.FIXED_SYSTEMD_COMMAND)
        self.assertEqual(command[0:2], ("systemctl", "show"))
        self.assertEqual(command[2], adapter.FIXED_SYSTEMD_UNIT)
        self.assertNotIn("restart", command)
        self.assertNotIn("start", command)
        self.assertNotIn("stop", command)
        self.assertNotIn("daemon-reload", command)
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)

    def test_process_failures_are_bounded_and_do_not_leak_raw_text(self):
        def raising_run(*args, **kwargs):
            raise OSError("SYNTHETIC_SECRET_EXCEPTION")

        result = adapter._query_fixed_process_state(raising_run)
        self.assertEqual(result["error"], "PROCESS_QUERY_FAILED")
        self.assertNotIn("SYNTHETIC_SECRET_EXCEPTION", json.dumps(result))

        malformed = lambda *a, **k: subprocess.CompletedProcess(
            args=a, returncode=0, stdout="unexpected secret output", stderr=""
        )
        result = adapter._query_fixed_process_state(malformed)
        self.assertEqual(result["error"], "PROCESS_RESPONSE_INVALID")
        self.assertNotIn("unexpected secret output", json.dumps(result))

    def test_get_health_uses_fixed_path_and_fixed_process_method(self):
        seen = []

        def fake_read(path):
            seen.append(path)
            return state_bytes(valid_state())

        process = {
            "availability": "AVAILABLE",
            "error": "NONE",
            "active_state": "active",
            "sub_state": "running",
            "running": True,
        }
        with (
            mock.patch.object(adapter, "_read_regular_bytes", side_effect=fake_read),
            mock.patch.object(adapter, "_query_fixed_process_state", return_value=process),
            mock.patch.object(adapter.time, "time_ns", return_value=1_000_010_000_000),
        ):
            result = adapter.get_health()
        self.assertEqual(seen, [adapter.FIXED_STATE_PATH])
        self.assertEqual(result["collector_id"], adapter.COLLECTOR_ID)
        self.assertEqual(result["process"], process)
        self.assertEqual(result["observed_at_ms"], 1_000_010)

    def test_process_response_requires_exact_keys_and_safe_tokens(self):
        outputs = (
            "ActiveState=active\n",
            "ActiveState=active\nActiveState=inactive\nSubState=running\n",
            "ActiveState=active\nSubState=running;restart\n",
            "ActiveState=active\nSubState=running\nExtra=value\n",
        )
        for stdout in outputs:
            with self.subTest(stdout=stdout):
                runner = lambda *a, **k: subprocess.CompletedProcess(
                    args=a, returncode=0, stdout=stdout, stderr=""
                )
                result = adapter._query_fixed_process_state(runner)
                self.assertEqual(result["availability"], "UNAVAILABLE")
                self.assertEqual(result["error"], "PROCESS_RESPONSE_INVALID")


class IsolationStaticTests(unittest.TestCase):
    def test_source_has_no_network_or_mutation_primitives(self):
        source = ADAPTER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue(
            {"socket", "urllib", "http", "requests", "websocket", "asyncio"}.isdisjoint(imports)
        )

        forbidden_attributes = {
            "chmod",
            "chown",
            "fchmod",
            "fchown",
            "kill",
            "remove",
            "unlink",
            "replace",
            "rename",
            "write",
            "send",
            "connect",
            "popen",
            "system",
        }
        called_attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue(forbidden_attributes.isdisjoint(called_attributes))

        self.assertNotIn("raw/", source)
        self.assertNotIn("events/", source)
        self.assertNotIn("connection_events.jsonl", source)
        self.assertNotIn("systemd.log", source)
        self.assertNotIn("shell=True", source)

    def test_constants_freeze_size_freshness_path_and_unit(self):
        self.assertEqual(adapter.MAX_STATE_BYTES, 65_536)
        self.assertEqual(adapter.HEARTBEAT_STALE_AFTER_MS, 90_000)
        self.assertEqual(
            str(adapter.FIXED_STATE_PATH),
            "/home/botmarket/sc001_data/"
            "SC001_B13C_PROSPECTIVE_LIQUIDATIONS/collector_state.json",
        )
        self.assertEqual(adapter.FIXED_SYSTEMD_UNIT, "sc001-b13c-liquidation.service")
        self.assertEqual(adapter.FIXED_SYSTEMD_COMMAND.count(adapter.FIXED_SYSTEMD_UNIT), 1)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    token = (
        "P1_HEALTH_ADAPTER_SYNTHETIC_PASS"
        if result.wasSuccessful()
        else "P1_HEALTH_ADAPTER_SYNTHETIC_FAIL"
    )
    print(token)
    print(f"tests_run = {result.testsRun}")
    print(f"failures = {len(result.failures)}")
    print(f"errors = {len(result.errors)}")
    raise SystemExit(0 if result.wasSuccessful() else 1)
