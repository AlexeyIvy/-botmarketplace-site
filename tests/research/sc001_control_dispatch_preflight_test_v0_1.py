#!/usr/bin/env python3
"""Offline adversarial tests for SC001 control-plane admission; no network."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/research/sc001_control_dispatch_preflight_v0_1.py"
SPEC = importlib.util.spec_from_file_location("control_preflight", SOURCE)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

HEAD = "a" * 40


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.script = "tests/research/example_test.py"
        path = self.root / self.script
        path.parent.mkdir(parents=True)
        path.write_text("import unittest\nif __name__ == '__main__': unittest.main()\n")
        self.sha = hashlib.sha256(path.read_bytes()).hexdigest()
        self.impl = "scripts/research/frozen_impl.py"
        impl_path = self.root / self.impl
        impl_path.parent.mkdir(parents=True)
        impl_path.write_text("VALUE = 1\n")
        self.impl_sha = hashlib.sha256(impl_path.read_bytes()).hexdigest()
        self.info = {
            "head": HEAD, "network_profiles": ["offline", "public_research"],
            "limits": {"max_timeout_seconds": 900, "max_concurrent_jobs": 1,
                       "max_runs_per_rolling_hour": 6, "max_runs_per_utc_day": 30},
            "current_counts": {"running": 0, "rolling_hour": 0, "utc_day": 0},
        }
        self.task = {
            "task_id": "SC001-H1-OFFLINE-001",
            "worker_id": "H1_HISTORICAL_INDICATORS",
            "authorization_class": "T0_OFFLINE_SYNTHETIC_TEST_ONLY",
            "frozen_inputs": {"test_path": self.script, "test_sha256": self.sha,
                              "implementation_path": self.impl,
                              "implementation_sha256": self.impl_sha},
            "exact_execution": {
                "entrypoint": self.script, "args": [], "repo_head_sha": HEAD,
                "timeout_seconds": 180, "max_executions": 1,
                "network_profile": "offline", "max_network_runs": 0,
            },
        }

    def check(self, auth=None):
        return mod.preflight(self.task, self.info, HEAD, self.root, auth)

    def assert_blocked(self, expected):
        result = self.check()
        self.assertEqual(result["status"], "ADMISSION_BLOCKED")
        self.assertIn(expected, result["errors"])
        self.assertFalse(result["execution_authorized_by_this_check"])

    def test_valid_offline_task_is_technical_pass_only(self):
        result = self.check()
        self.assertEqual(result["status"], "ADMISSION_PRECHECK_PASS")
        self.assertFalse(result["execution_authorized_by_this_check"])
        self.assertTrue(result["live_recheck_required_immediately_before_job"])

    def test_direct_output_dir_for_readonly_executor_is_rejected(self):
        self.task["exact_execution"]["args"] = ["--output-dir", "artifacts/unsafe"]
        self.assert_blocked("DIRECT_OUTPUT_DIRECTORY_CLI_NOT_EXECUTOR_BOUND")

    def test_python_command_instead_of_file_is_blocked(self):
        self.task["exact_execution"].pop("entrypoint")
        self.task["exact_execution"]["command"] = ["python3", "-m", "unittest"]
        self.assert_blocked("INVALID_EXECUTOR_ENTRYPOINT")

    def test_timeout_exceeding_live_cap_is_blocked(self):
        self.task["exact_execution"]["timeout_seconds"] = 1800
        self.assert_blocked("TIMEOUT_EXCEEDS_LIVE_CAP")

    def test_invalid_or_unsafe_entrypoints_are_blocked(self):
        for value in ("python3", "../secrets.py", "/tmp/a.py",
                      "tests/research/../../secrets.py", "tests/research/foo.txt"):
            with self.subTest(value=value):
                self.task["exact_execution"]["entrypoint"] = value
                self.assert_blocked("INVALID_EXECUTOR_ENTRYPOINT")

    def test_missing_and_mismatched_frozen_file_are_blocked(self):
        self.task["frozen_inputs"]["test_sha256"] = "0" * 64
        self.assert_blocked("FROZEN_FILE_HASH_MISMATCH")
        self.task["frozen_inputs"]["test_path"] = "tests/research/missing.py"
        self.assert_blocked("FROZEN_FILE_MISSING_OR_UNSAFE")

    def test_symlink_outside_repository_is_blocked(self):
        external = Path(self.tmp.name).parent / ("external-for-" + self.tmp.name.split("/")[-1])
        external.write_text("print('not an allowed test')\n")
        self.addCleanup(lambda: external.unlink(missing_ok=True))
        (self.root / "tests/research/sneaky.py").symlink_to(external)
        self.task["exact_execution"]["entrypoint"] = "tests/research/sneaky.py"
        self.assert_blocked("ENTRYPOINT_NOT_IN_REPOSITORY")

    def test_stale_main_and_executor_head_are_blocked(self):
        self.task["exact_execution"]["repo_head_sha"] = "b" * 40
        self.assert_blocked("TASK_HEAD_NOT_CANONICAL_MAIN")
        self.task["exact_execution"]["repo_head_sha"] = HEAD
        self.info["head"] = "b" * 40
        self.assert_blocked("EXECUTOR_HEAD_NOT_CANONICAL_MAIN")

    def test_missing_live_limits_and_busy_executor(self):
        self.info["current_counts"]["running"] = 1
        result = self.check()
        self.assertEqual(result["status"], "ADMISSION_RESOURCE_DEFER")
        self.assertIn("EXECUTOR_RUNNING_CAP_REACHED", result["resource_defer_reasons"])
        self.info["limits"].pop("max_timeout_seconds")
        self.assert_blocked("MISSING_LIVE_TIMEOUT_CAP")

    def test_boolean_numeric_budgets_fail_closed(self):
        self.task["exact_execution"]["timeout_seconds"] = True
        self.assert_blocked("INVALID_TIMEOUT")
        self.task["exact_execution"]["timeout_seconds"] = 100
        self.task["exact_execution"]["max_executions"] = True
        self.assert_blocked("EXECUTION_COUNT_NOT_ONE")

    def test_t1_authorization_required_and_fully_bound(self):
        self.task["authorization_class"] = "T1"
        self.task["exact_execution"]["network_profile"] = "public_research"
        self.task["exact_execution"]["max_network_runs"] = 1
        self.task["frozen_request_contract"] = {
            "max_requests_total": 9, "max_response_bytes_total": 1500}
        result = self.check()
        self.assertEqual(result["status"], "ADMISSION_BLOCKED")
        self.assertIn("MISSING_T1_AUTHORIZATION", result["errors"])
        auth = {
            "task_id": self.task["task_id"],
            "worker_id": self.task["worker_id"],
            "status": "AUTHORIZED_ONE_SHOT",
            "authorization_tier": "T1",
            "expires_at_utc": "2999-01-01T00:00:00Z",
            "canonical_main_head": HEAD,
            "exact_entrypoint": self.script,
            "exact_args": [],
            "budgets": {"max_wall_time_seconds": 180, "max_network_runs": 1,
                        "max_requests_total": 9, "max_total_network_bytes": 1500},
        }
        self.assertEqual(self.check(auth)["status"], "ADMISSION_PRECHECK_PASS")
        auth["budgets"]["max_wall_time_seconds"] = 1800
        self.assertIn("AUTHORIZATION_TIMEOUT_MISMATCH", self.check(auth)["errors"])
        auth["budgets"]["max_wall_time_seconds"] = 180
        auth["budgets"]["max_requests_total"] = 10
        self.assertIn("AUTHORIZATION_REQUEST_CAP_MISMATCH", self.check(auth)["errors"])

    def test_missing_explicit_execution_count_and_evidence_bindings(self):
        self.task["exact_execution"].pop("max_executions")
        self.assert_blocked("EXECUTION_COUNT_NOT_ONE")
        self.task["exact_execution"]["max_executions"] = 1
        self.task.pop("frozen_inputs")
        self.assert_blocked("MISSING_FROZEN_FILE_BINDINGS")
        self.task["exact_execution"].pop("max_network_runs")
        self.assert_blocked("INVALID_NETWORK_RUN_BUDGET")

    def test_t1_empty_code_binding_cannot_use_freeze_as_substitute(self):
        self.task["authorization_class"] = "T1"
        self.task["frozen_inputs"].pop("implementation_path")
        self.task["frozen_inputs"].pop("implementation_sha256")
        self.task["canonical_freeze"] = {"path": self.script, "sha256": self.sha}
        self.assert_blocked("MISSING_T1_CODE_TEST_BINDINGS")

    def test_t1_authorization_expiry_fail_closed(self):
        self.task["authorization_class"] = "T1"
        self.task["exact_execution"]["network_profile"] = "public_research"
        self.task["exact_execution"]["max_network_runs"] = 1
        self.task["frozen_request_contract"] = {
            "max_requests_total": 9, "max_response_bytes_total": 1500}
        authorization = {
            "task_id": self.task["task_id"], "worker_id": self.task["worker_id"],
            "status": "AUTHORIZED_ONE_SHOT", "authorization_tier": "T1",
            "expires_at_utc": "2020-01-01T00:00:00Z",
            "canonical_main_head": HEAD, "exact_entrypoint": self.script,
            "exact_args": [],
            "budgets": {"max_wall_time_seconds": 180, "max_network_runs": 1,
                        "max_requests_total": 9, "max_total_network_bytes": 1500},
        }
        self.assertIn("AUTHORIZATION_EXPIRED_OR_INVALID", self.check(authorization)["errors"])
        authorization["expires_at_utc"] = "not-a-date"
        self.assertIn("AUTHORIZATION_EXPIRED_OR_INVALID", self.check(authorization)["errors"])

    def test_t1_network_scope_cannot_be_downgraded_silently(self):
        self.task["authorization_class"] = "T1"
        self.assert_blocked("T1_NETWORK_PROFILE_OR_BUDGET_MISMATCH")

    def test_deterministic_continuation_identity(self):
        scope = "a" * 64
        key = mod.continuation_key("AlexeyIvy/-botmarketplace-site", 123,
                                   "OFFLINE_SELFTEST", scope)
        self.assertEqual(len(key), 64)
        self.assertEqual(key, mod.continuation_key("AlexeyIvy/-botmarketplace-site",
                                                  123, "OFFLINE_SELFTEST", scope))
        self.assertNotEqual(key, mod.continuation_key("AlexeyIvy/-botmarketplace-site",
                                                     124, "OFFLINE_SELFTEST", scope))
        self.assertNotEqual(key, mod.continuation_key("AlexeyIvy/-botmarketplace-site",
                                                     123, "T1_CAPTURE", scope))
        with self.assertRaises(ValueError):
            mod.continuation_key("x", 0, "OFFLINE_SELFTEST", scope)
        with self.assertRaises(ValueError):
            mod.continuation_key("AlexeyIvy/-botmarketplace-site", 1.5, "OFFLINE_SELFTEST", scope)
        with self.assertRaises(ValueError):
            mod.continuation_key("AlexeyIvy/-botmarketplace-site", True, "OFFLINE_SELFTEST", scope)


if __name__ == "__main__":
    unittest.main(verbosity=2)
