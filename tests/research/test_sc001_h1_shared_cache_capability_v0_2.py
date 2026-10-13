#!/usr/bin/env python3
"""Synthetic-only full-path safety regressions. Never invokes a real host service.

Frozen installer heredocs are parsed as text, never run as shell. All permission
syscalls and subprocesses are mocked; filesystem fixtures are temporary-owned.
Generated launcher logic is executed with only its five path constants redirected.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import socket
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).parents[2]
DEPLOY = ROOT / "scripts/research/deploy_sc001_h1_shared_cache_capability_v0_2.py"
SOURCE = ROOT / "scripts/mcp/install-botmarket-test-executor-v1.sh"
SOURCE_SHA = "0e9afe9b9a3e12beb7aa451a7608eda3ffa30a46ba9b07faf0a869bfda518968"
RESOURCE_ID = "b97ffeefed4dd1b4caa771df734b59b5a6dc2b6a9ada3b3c9b8ce0c6de6319bf"
ACQUISITION_SHA = "1eb597e3186023540a5ab9929f433f7f5a81b9d587f10386cf2e3e55f625c760"
CAPS = {"max_timeout_seconds": 900, "max_single_dataset_bytes": 5 * 1024**3,
        "max_peak_workspace_increment": 15 * 1024**3}
CAP_ERRORS = {"max_timeout_seconds": "SHARED_CACHE_TIMEOUT_CAP",
              "max_single_dataset_bytes": "SHARED_CACHE_DATASET_CAP",
              "max_peak_workspace_increment": "SHARED_CACHE_PEAK_CAP"}


def load_deployer():
    spec = importlib.util.spec_from_file_location("h1_synthetic_deployer", DEPLOY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def frozen_artifacts():
    data = SOURCE.read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA:
        raise AssertionError("frozen installer identity mismatch")
    text = data.decode()
    values = {"JOBS": "/var/lib/botmarket-test-executor/jobs",
              "STATE": "/var/lib/botmarket-test-executor",
              "APP": "/opt/botmarket-test-executor", "PY": "/opt/botmarket-research/venv/bin/python",
              "JOB_USER": "botmarket-testjob", "JOB_GROUP": "botmarket-test-jobs"}
    result = {}
    for name, anchor, delimiter, expand in (
        ("policy", 'cat > "$POLICY" <<\'JSON\'\n', "JSON", False),
        ("runner", 'cat > "$APP/job_runner.py" <<PY\n', "PY", True),
        ("launcher", 'cat > "$LAUNCHER" <<PY\n', "PY", True),
        ("server", 'cat > "$APP/server.py" <<\'PY\'\n', "PY", False),
    ):
        if text.count(anchor) != 1:
            raise AssertionError("source heredoc anchor drift")
        body = text.split(anchor, 1)[1].split("\n" + delimiter + "\n", 1)[0] + "\n"
        if expand:
            # Match only the frozen, reviewed heredoc substitutions; no shell.
            body = re.sub(r"\$([A-Z_]+)", lambda m: values[m.group(1)], body)
            body = body.replace("\\\\", "\\").replace("\\$", "$").replace("\\`", "`")
        result[name] = body.encode()
    return result


def root_stat(real, mode=None, uid=0):
    values = list(real)
    values[0] = real.st_mode if mode is None else mode
    values[4] = uid
    return os.stat_result(values)


class SyntheticCase(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.tmp = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="h1-offline-")))
        self.mod = load_deployer()
        self.real_fstat = os.fstat
        self.real_exists = Path.exists
        self.real_open = os.open
        self.security_calls = {}
        for name in ("chmod", "chown", "fchmod", "fchown"):
            self.security_calls[name] = self.stack.enter_context(mock.patch.object(os, name))
        self.stack.enter_context(mock.patch.object(os, "geteuid", return_value=0))
        self.stack.enter_context(mock.patch.object(socket, "socket", side_effect=AssertionError("NETWORK_FORBIDDEN")))
        self.stack.enter_context(mock.patch.object(subprocess, "Popen", side_effect=AssertionError("PROCESS_FORBIDDEN")))
        self.run_mock = self.stack.enter_context(mock.patch.object(subprocess, "run", side_effect=AssertionError("PROCESS_FORBIDDEN")))
        self.fstat_mock = self.stack.enter_context(mock.patch.object(os, "fstat", side_effect=lambda fd: root_stat(self.real_fstat(fd))))


class InstallerFlowTests(SyntheticCase):
    def setUp(self):
        super().setUp()
        sources = frozen_artifacts()
        self.files = tuple(self.tmp / (name + ".fixture") for name in ("policy", "runner", "launcher", "server"))
        self.originals = dict(zip(self.files, sources.values()))
        for path, data in self.originals.items():
            path.write_bytes(data)
        for name, path in zip(("POLICY", "RUNNER", "LAUNCHER", "SERVER"), self.files):
            self.stack.enter_context(mock.patch.object(self.mod, name, path))
        self.stack.enter_context(mock.patch.object(self.mod, "FILES", self.files))
        self.stack.enter_context(mock.patch.object(self.mod, "PATCHERS", dict(zip(self.files, (
            self.mod.patch_policy, self.mod.patch_runner, self.mod.patch_launcher, self.mod.patch_server)))))
        for name in ("BACKUPS", "RECEIPTS", "SHARED_ROOT", "GRANTS"):
            self.stack.enter_context(mock.patch.object(self.mod, name, self.tmp / name.lower()))
        self.stack.enter_context(mock.patch.object(self.mod.grp, "getgrnam", return_value=SimpleNamespace(gr_gid=9876)))
        self.plan, self.targets = self.mod.build_plan(SOURCE)
        self.plan_hash = self.mod.sha256_bytes(self.mod.canonical_bytes(self.plan))
        self.receipt = self.mod.RECEIPTS / (self.plan_hash + ".json")
        self.args = argparse.Namespace(source_installer=SOURCE, ack=self.mod.ACK,
                                       approval_ref="SYNTHETIC_ONLY_NOT_AUTHORITY",
                                       expected_plan_sha256=self.plan_hash, receipt=self.receipt)
        self.events = []
        self.fail_action = None
        self.run_mock.side_effect = self.service

    def service(self, argv, **kwargs):
        self.assertEqual(argv[0], "systemctl")
        self.assertIn(argv[1], ("stop", "daemon-reload", "start"))
        if argv[1] != "daemon-reload":
            self.assertEqual(argv[2], self.mod.SERVICE)
        self.assertTrue(self.receipt.is_file(), "receipt must precede any service action")
        self.events.append(tuple(argv))
        if argv[1] == self.fail_action:
            self.fail_action = None
            raise subprocess.CalledProcessError(1, argv)
        return subprocess.CompletedProcess(argv, 0)

    def assert_originals(self):
        for path, data in self.originals.items():
            self.assertEqual(path.read_bytes(), data)

    def assert_targets(self):
        for path, data in self.targets.items():
            self.assertEqual(path.read_bytes(), data)

    def prepare_failed(self, action="start"):
        self.fail_action = action
        with self.assertRaises(subprocess.CalledProcessError):
            self.mod.apply(self.args)
        receipt = json.loads(self.receipt.read_text())
        self.assertEqual(receipt["state"], "PREPARED")
        self.assert_targets()
        self.events.clear()
        return receipt

    def assert_denied_without_mutation(self):
        before = {p: p.read_bytes() for p in self.files}
        self.events.clear()
        with self.assertRaises((self.mod.GateError, OSError, ValueError, KeyError)):
            self.mod.rollback(self.args)
        self.assertEqual(self.events, [])
        self.assertEqual(before, {p: p.read_bytes() for p in self.files})

    def test_real_patchers_compile_all_generated_artifacts(self):
        self.assertEqual(self.mod.RESOURCE_ID, RESOURCE_ID)
        self.assertEqual(self.mod.ACQUISITION_SHA256, ACQUISITION_SHA)
        for name, expected in CAPS.items():
            self.assertEqual(getattr(self.mod, name.upper()), expected)
        policy = json.loads(self.targets[self.files[0]])
        self.assertEqual(policy["shared_cache"]["ordinary_jobs_access"], "NONE")
        self.assertFalse(policy["shared_cache"]["grants_created_by_install"])
        self.assertEqual(policy["max_timeout_seconds"], 900)
        for path in self.files[1:]:
            compile(self.targets[path], str(path), "exec")
        with self.assertRaises(self.mod.GateError):
            self.mod.patch_launcher(self.targets[self.files[2]].decode())

    def test_successful_apply_and_rollback_actual_paths(self):
        applied = self.mod.apply(self.args)
        self.assertEqual(applied["state"], "APPLIED")
        self.assertEqual(json.loads(self.receipt.read_text()), applied)
        self.assert_targets()
        result = self.mod.rollback(self.args)
        self.assert_originals()
        self.assertFalse(result["shared_root_deleted"])
        self.assertFalse(result["verified_cache_deleted"])
        self.assertTrue(self.mod.GRANTS.is_dir())
        self.assertEqual(list(self.mod.GRANTS.iterdir()), [])

    def test_failed_restart_keeps_durable_receipt_then_restores_all(self):
        self.prepare_failed("start")
        sentinel = self.mod.SHARED_ROOT / "synthetic-preserve.txt"
        sentinel.write_text("synthetic")
        self.mod.rollback(self.args)
        self.assert_originals()
        self.assertEqual(sentinel.read_text(), "synthetic")
        self.assertEqual([e[1] for e in self.events], ["stop", "daemon-reload", "start"])

    def test_failed_reload_keeps_receipt_then_restores_all(self):
        self.prepare_failed("daemon-reload")
        self.mod.rollback(self.args)
        self.assert_originals()

    def test_failed_stop_is_recoverable_from_prepared_receipt(self):
        self.fail_action = "stop"
        with self.assertRaises(subprocess.CalledProcessError):
            self.mod.apply(self.args)
        self.assert_originals()
        self.assertEqual(json.loads(self.receipt.read_text())["state"], "PREPARED")
        self.mod.rollback(self.args)
        self.assert_originals()

    def test_partial_target_write_failure_uses_before_after_hashes(self):
        write = self.mod.atomic_write
        def fail_second(path, *args):
            if path == self.files[1]:
                raise OSError("synthetic target write failure")
            return write(path, *args)
        with mock.patch.object(self.mod, "atomic_write", side_effect=fail_second):
            with self.assertRaises(OSError):
                self.mod.apply(self.args)
        self.assertEqual(self.files[0].read_bytes(), self.targets[self.files[0]])
        self.assertEqual(self.files[1].read_bytes(), self.originals[self.files[1]])
        self.mod.rollback(self.args)
        self.assert_originals()

    def test_actual_atomic_write_failure_during_apply_is_rollback_safe(self):
        real_open = Path.open
        failing_fd = []
        def track_open(path, *args, **kwargs):
            stream = real_open(path, *args, **kwargs)
            if path == self.mod.temporary_path(self.files[1]):
                failing_fd[:] = [stream.fileno()]
            return stream
        def mode_effect(fd, mode):
            if failing_fd and fd == failing_fd[0]:
                raise OSError("synthetic failure after second target temp open")
        with mock.patch.object(Path, "open", autospec=True, side_effect=track_open), mock.patch.object(os, "fchmod", side_effect=mode_effect):
            with self.assertRaises(OSError):
                self.mod.apply(self.args)
        self.assertEqual(self.files[0].read_bytes(), self.targets[self.files[0]])
        self.assertEqual(self.files[1].read_bytes(), self.originals[self.files[1]])
        self.assertFalse(self.mod.temporary_path(self.files[1]).exists())
        self.mod.rollback(self.args)
        self.assert_originals()

    def test_preexisting_target_temp_stops_apply_before_mutation(self):
        tmp = self.mod.temporary_path(self.files[1])
        tmp.write_bytes(b"preexisting")
        with self.assertRaises(self.mod.GateError):
            self.mod.apply(self.args)
        self.assert_originals()
        self.assertEqual(self.events, [])
        self.assertEqual(tmp.read_bytes(), b"preexisting")

    def test_preexisting_restore_temp_stops_before_any_restore(self):
        self.prepare_failed()
        tmp = self.mod.temporary_path(self.files[-1])
        tmp.write_bytes(b"preexisting")
        self.assert_denied_without_mutation()
        self.assertEqual(tmp.read_bytes(), b"preexisting")

    def test_preexisting_untrusted_authority_directory_prevents_apply(self):
        for name in ("BACKUPS", "RECEIPTS"):
            directory = getattr(self.mod, name)
            directory.mkdir(exist_ok=True)
            inode = directory.stat().st_ino
            for uid, bits in ((42, 0), (0, 0o020), (0, 0o002)):
                with self.subTest(directory=name, uid=uid, bits=bits):
                    def metadata(fd):
                        original = self.real_fstat(fd)
                        return root_stat(original, original.st_mode | bits, uid) if original.st_ino == inode else root_stat(original)
                    self.fstat_mock.side_effect = metadata
                    with self.assertRaises(self.mod.GateError):
                        self.mod.apply(self.args)
                    self.assert_originals()
                    self.assertEqual(self.events, [])
            self.fstat_mock.side_effect = lambda fd: root_stat(self.real_fstat(fd))

    def test_symlinked_authority_directory_prevents_apply(self):
        other = self.tmp / "other-authority"
        other.mkdir()
        self.mod.RECEIPTS.symlink_to(other, target_is_directory=True)
        with self.assertRaises(self.mod.GateError):
            self.mod.apply(self.args)
        self.assert_originals()
        self.assertEqual(self.events, [])
        self.assertEqual(list(other.iterdir()), [])

    def test_receipt_write_failure_prevents_service_or_target_mutation(self):
        write = self.mod.atomic_write
        def fail_receipt(path, *args):
            if path == self.receipt:
                raise OSError("synthetic receipt failure")
            return write(path, *args)
        with mock.patch.object(self.mod, "atomic_write", side_effect=fail_receipt):
            with self.assertRaises(OSError):
                self.mod.apply(self.args)
        self.assert_originals()
        self.assertEqual(self.events, [])

    def test_final_receipt_failure_preserves_prepared_recovery(self):
        write = self.mod.atomic_write
        def fail_final(path, data, *args):
            if path == self.receipt and json.loads(data)["state"] == "APPLIED":
                raise OSError("synthetic final receipt failure")
            return write(path, data, *args)
        with mock.patch.object(self.mod, "atomic_write", side_effect=fail_final):
            with self.assertRaises(OSError):
                self.mod.apply(self.args)
        self.assertEqual(json.loads(self.receipt.read_text())["state"], "PREPARED")
        self.mod.rollback(self.args)
        self.assert_originals()

    def test_missing_receipt_is_denied_before_service(self):
        self.prepare_failed()
        self.receipt.unlink()
        self.assert_denied_without_mutation()

    def test_tampered_receipt_fields_are_denied(self):
        receipt = self.prepare_failed()
        mutations = {"schema": "wrong", "task_id": "wrong", "state": "ROLLBACK_OK",
                     "plan_sha256": "0" * 64, "backup": str(self.tmp), "files": [],
                     "approval_ref": "", "shared_root_preserve_on_rollback": False,
                     "grants_created": True, "market_data_accessed": True}
        for key, value in mutations.items():
            with self.subTest(field=key):
                bad = dict(receipt, **{key: value})
                self.receipt.write_text(json.dumps(bad))
                self.assert_denied_without_mutation()
        self.receipt.write_text(json.dumps(receipt))
        self.mod.rollback(self.args)
        self.assert_originals()

    def test_receipt_nonobject_and_invalid_json_denied(self):
        self.prepare_failed()
        for text in ("[]", "null", "{broken"):
            with self.subTest(text=text):
                self.receipt.write_text(text)
                self.assert_denied_without_mutation()

    def test_receipt_symlink_denied(self):
        self.prepare_failed()
        other = self.tmp / "receipt-copy.json"
        self.receipt.rename(other)
        self.receipt.symlink_to(other)
        self.assert_denied_without_mutation()

    def test_wrong_expected_plan_and_wrong_receipt_path_denied(self):
        self.prepare_failed()
        with mock.patch.object(self.args, "expected_plan_sha256", "0" * 64):
            self.assert_denied_without_mutation()
        with mock.patch.object(self.args, "receipt", self.tmp / "unknown.json"):
            self.assert_denied_without_mutation()

    def test_missing_plan_denied_before_service(self):
        receipt = self.prepare_failed()
        (Path(receipt["backup"]) / "plan.json").unlink()
        self.assert_denied_without_mutation()

    def test_missing_last_backup_prevents_any_restore(self):
        receipt = self.prepare_failed()
        name = hashlib.sha256(str(self.files[-1]).encode()).hexdigest() + ".bak"
        (Path(receipt["backup"]) / name).unlink()
        self.assert_denied_without_mutation()

    def test_missing_installed_target_prevents_any_restore(self):
        self.prepare_failed()
        self.files[-1].unlink()
        before = {p: p.read_bytes() for p in self.files[:-1]}
        with self.assertRaises(self.mod.GateError):
            self.mod.rollback(self.args)
        self.assertEqual(self.events, [])
        self.assertEqual(before, {p: p.read_bytes() for p in self.files[:-1]})
        self.assertFalse(self.files[-1].exists())

    def test_untrusted_authority_directory_prevents_rollback(self):
        self.prepare_failed()
        inode = self.mod.RECEIPTS.stat().st_ino
        for uid, bits in ((42, 0), (0, 0o020), (0, 0o002)):
            with self.subTest(uid=uid, bits=bits):
                def metadata(fd):
                    original = self.real_fstat(fd)
                    return root_stat(original, original.st_mode | bits, uid) if original.st_ino == inode else root_stat(original)
                self.fstat_mock.side_effect = metadata
                self.assert_denied_without_mutation()

    def test_tampered_plan_denied_before_service(self):
        receipt = self.prepare_failed()
        plan_path = Path(receipt["backup"]) / "plan.json"
        obj = json.loads(plan_path.read_text())
        obj["files"][0]["path"] = str(self.tmp / "outside.txt")
        plan_path.write_text(json.dumps(obj))
        self.assert_denied_without_mutation()

    def test_last_backup_tamper_prevents_even_first_restore(self):
        receipt = self.prepare_failed()
        name = hashlib.sha256(str(self.files[-1]).encode()).hexdigest() + ".bak"
        (Path(receipt["backup"]) / name).write_bytes(b"tampered")
        self.assert_denied_without_mutation()

    def test_last_installed_target_tamper_prevents_all_restore(self):
        self.prepare_failed()
        self.files[-1].write_bytes(b"tampered")
        self.assert_denied_without_mutation()

    def test_untrusted_receipt_owner_or_write_mode_denied(self):
        self.prepare_failed()
        for uid, bits in ((42, 0), (0, 0o020), (0, 0o002)):
            with self.subTest(uid=uid, bits=bits):
                def metadata(fd):
                    original = self.real_fstat(fd)
                    return root_stat(original, original.st_mode | bits, uid) if stat.S_ISREG(original.st_mode) else root_stat(original)
                self.fstat_mock.side_effect = metadata
                self.assert_denied_without_mutation()

    def test_atomic_write_fsyncs_file_and_parent_after_replace(self):
        path = self.tmp / "atomic-fixture"
        trace = []
        real_fsync, real_replace = os.fsync, os.replace
        self.security_calls["fchown"].side_effect = lambda *args: trace.append("ownership")
        self.security_calls["fchmod"].side_effect = lambda *args: trace.append("mode")
        def fsync(fd):
            trace.append("dir-fsync" if stat.S_ISDIR(self.real_fstat(fd).st_mode) else "file-fsync")
            return real_fsync(fd)
        def replace(src, dst):
            trace.append("replace")
            return real_replace(src, dst)
        with mock.patch.object(os, "fsync", side_effect=fsync), mock.patch.object(os, "replace", side_effect=replace):
            self.mod.atomic_write(path, b"synthetic", 0o400, 0, 0)
        self.assertEqual(trace, ["ownership", "mode", "file-fsync", "replace", "dir-fsync"])
        self.assertEqual(path.read_bytes(), b"synthetic")
        self.security_calls["fchmod"].assert_called()
        self.security_calls["fchown"].assert_called()

    def test_atomic_write_failure_cleans_own_temp_and_preserves_original(self):
        path = self.tmp / "atomic-failure"
        path.write_bytes(b"original")
        with mock.patch.object(os, "fchmod", side_effect=OSError("synthetic permission syscall failure")):
            with self.assertRaises(OSError):
                self.mod.atomic_write(path, b"changed", 0o400, 0, 0)
        self.assertEqual(path.read_bytes(), b"original")
        self.assertFalse(path.with_name(path.name + ".sc001-004j-r1.tmp").exists())
        self.mod.atomic_write(path, b"recovered", 0o400, 0, 0)
        self.assertEqual(path.read_bytes(), b"recovered")

    def test_atomic_write_rejects_preexisting_temp_without_deleting_it(self):
        path = self.tmp / "atomic-stale"
        path.write_bytes(b"original")
        tmp = path.with_name(path.name + ".sc001-004j-r1.tmp")
        tmp.write_bytes(b"preexisting")
        with self.assertRaises(FileExistsError):
            self.mod.atomic_write(path, b"changed", 0o400, 0, 0)
        self.assertEqual(path.read_bytes(), b"original")
        self.assertEqual(tmp.read_bytes(), b"preexisting")

    def test_wrong_plan_or_ack_has_no_service_effect(self):
        for field, value in (("expected_plan_sha256", "0" * 64), ("ack", "OLD_ACK"), ("approval_ref", "")):
            with self.subTest(field=field), mock.patch.object(self.args, field, value):
                with self.assertRaises(self.mod.GateError):
                    self.mod.apply(self.args)
                self.assertEqual(self.events, [])
                self.assert_originals()

    def test_source_binding_and_cli_rollback_requires_plan_hash(self):
        bad = self.tmp / "wrong-installer"
        bad.write_bytes(b"no")
        with self.assertRaises(self.mod.GateError):
            self.mod.verify_source_installer(bad)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.mod.parser().parse_args(["rollback", "--receipt", "unused", "--ack", "unused", "--approval-ref", "unused"])


class LauncherFlowTests(SyntheticCase):
    def setUp(self):
        super().setUp()
        raw = frozen_artifacts()["launcher"].decode()
        generated = self.mod.patch_launcher(raw)
        tree = ast.parse(generated)
        redirect = {"BASE", "RUNNER", "SHARED_ROOT", "GRANTS", "PUBLIC_RESOLV"}
        removed = {node.targets[0].id for node in tree.body if isinstance(node, ast.Assign)
                   and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                   and node.targets[0].id in redirect}
        self.assertEqual(removed, redirect)
        tree.body = [node for node in tree.body if not (isinstance(node, ast.Assign)
                     and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                     and node.targets[0].id in redirect)]
        self.code = compile(tree, "actual-generated-launcher.py", "exec")
        self.paths = {name: self.tmp / name.lower() for name in redirect}
        self.paths["BASE"].mkdir()
        self.paths["SHARED_ROOT"].mkdir()
        self.paths["GRANTS"].mkdir()
        self.paths["RUNNER"].write_text("# synthetic runner; never executed\n")
        self.paths["PUBLIC_RESOLV"].write_text("# synthetic resolver; never used\n")
        self.job_id = "job_20261013T000000Z_12345678"
        self.job = self.paths["BASE"] / self.job_id
        self.package = self.job / "package"
        self.output = self.job / "output"
        (self.package / "tests").mkdir(parents=True)
        self.output.mkdir()
        self.entry = self.package / "tests/synthetic.py"
        self.entry.write_text("raise AssertionError('NEVER_RUN')\n")
        self.entry_hash = hashlib.sha256(self.entry.read_bytes()).hexdigest()
        self.token = "synthetic-token-001"
        self.smoke = self.paths["SHARED_ROOT"] / "_capability_smoke" / self.token
        self.smoke.mkdir(parents=True)
        self.manifest = {"schema": "botmarket.test_job.v1", "job_id": self.job_id,
                         "trading_credentials_available": False, "repo_head": "a" * 40,
                         "entrypoint": "tests/synthetic.py", "entrypoint_sha256": self.entry_hash,
                         "args": [], "network_profile": "offline", "timeout_seconds": 1,
                         "shared_cache_role": "SMOKE_WRITE", "shared_cache_resource_id": "SYNTHETIC",
                         "shared_cache_grant_token": self.token, "shared_cache_task_id": "SYNTHETIC-TEST"}
        self.grant = {"schema": "sc001.shared_cache_grant.v0.1", "status": "AUTHORIZED",
                      "task_id": "SYNTHETIC-TEST", "role": "SMOKE_WRITE", "resource_id": "SYNTHETIC",
                      "network_profile": "offline", "entrypoint_sha256": self.entry_hash,
                      "t3_user_approval_ref": "SYNTHETIC_NOT_AUTHORITY", "expires_utc": "2099-01-01T00:00:00Z", **CAPS}
        self.grant_path = self.paths["GRANTS"] / (self.token + ".json")
        self.launches = []
        self.run_mock.side_effect = self.service
        self.stack.enter_context(mock.patch.object(sys, "argv", ["synthetic-launcher", self.job_id]))
        # No real host existence probes from the launcher isolation-path list.
        self.stack.enter_context(mock.patch.object(Path, "exists", autospec=True,
            side_effect=lambda path: self.real_exists(path) if path.is_relative_to(self.tmp) else False))

    def service(self, argv, **kwargs):
        self.assertIn(argv[0], ("systemctl", "systemd-run"))
        self.launches.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, stdout="not-found" if argv[0] == "systemctl" else "", stderr="")

    def run_launcher(self, expected=None, *, write_grant=True):
        (self.job / "job.json").write_text(json.dumps(self.manifest))
        if write_grant:
            self.grant_path.write_text(json.dumps(self.grant))
        self.launches.clear()
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            if expected is None:
                exec(self.code, {"__name__": "synthetic_launcher", **self.paths})
            else:
                with self.assertRaises(SystemExit) as error:
                    exec(self.code, {"__name__": "synthetic_launcher", **self.paths})
                self.assertEqual(error.exception.code, 2)
        if expected is not None:
            self.assertIn(expected, stderr.getvalue())
            self.assertEqual(self.launches, [], "grant denial must precede any subprocess")
        else:
            self.assertEqual(len(self.launches), 2)
            return json.loads(stdout.getvalue()), self.launches[-1]

    def test_valid_root_owned_grant_reaches_real_launcher_sandbox_command(self):
        receipt, command = self.run_launcher()
        self.assertEqual(receipt["shared_cache_role"], "SMOKE_WRITE")
        self.assertIn("--property=NoNewPrivileges=yes", command)
        self.assertIn("--property=PrivateNetwork=yes", command)
        self.assertIn("--property=MemoryMax=1073741824", command)
        self.assertIn("--property=ReadWritePaths=" + str(self.output) + " " + str(self.smoke), command)

    def test_all_caps_minimum_and_maximum_are_accepted(self):
        for boundary in (1, "ceiling"):
            for key, ceiling in CAPS.items():
                self.grant[key] = ceiling if boundary == "ceiling" else 1
            with self.subTest(boundary=boundary):
                self.run_launcher()

    def test_every_required_cap_missing_is_denied(self):
        for field in CAPS:
            value = self.grant.pop(field)
            with self.subTest(field=field):
                self.run_launcher(CAP_ERRORS[field])
            self.grant[field] = value

    def test_every_cap_rejects_invalid_types_zero_negative_and_over_limit(self):
        for field, ceiling in CAPS.items():
            for value in (None, 0, -1, False, True, "1", "900", 1.0, 0.5, [], {}, ceiling + 1):
                self.grant[field] = value
                with self.subTest(field=field, value=value):
                    self.run_launcher(CAP_ERRORS[field])
            self.grant[field] = ceiling

    def test_requested_timeout_at_hard_boundary_is_accepted(self):
        self.manifest["timeout_seconds"] = 900
        receipt, command = self.run_launcher()
        self.assertEqual(receipt["timeout_seconds"], 900)
        self.assertIn("--property=RuntimeMaxSec=930", command)

    def test_requested_timeout_above_grant_is_denied(self):
        self.manifest["timeout_seconds"] = 2
        self.grant["max_timeout_seconds"] = 1
        self.run_launcher("SHARED_CACHE_TIMEOUT_CAP")

    def test_nonroot_and_each_write_bit_are_denied(self):
        for uid, bits in ((13, 0), (0, 0o020), (0, 0o002)):
            with self.subTest(uid=uid, bits=bits):
                def metadata(fd):
                    original = self.real_fstat(fd)
                    if stat.S_ISREG(original.st_mode):
                        return root_stat(original, original.st_mode | bits, uid)
                    return root_stat(original)
                self.fstat_mock.side_effect = metadata
                self.run_launcher("SHARED_CACHE_GRANT_PERMISSIONS")

    def test_safe_file_modes_are_accepted(self):
        for mode in (0o400, 0o440, 0o600, 0o640, 0o644):
            with self.subTest(mode=mode):
                self.fstat_mock.side_effect = lambda fd, mode=mode: root_stat(self.real_fstat(fd),
                    stat.S_IFREG | mode if stat.S_ISREG(self.real_fstat(fd).st_mode) else self.real_fstat(fd).st_mode)
                self.run_launcher()

    def test_untrusted_grant_directory_denied(self):
        for uid, bits in ((15, 0), (0, 0o020), (0, 0o002)):
            with self.subTest(uid=uid, bits=bits):
                def metadata(fd):
                    original = self.real_fstat(fd)
                    return root_stat(original, original.st_mode | bits, uid) if stat.S_ISDIR(original.st_mode) else root_stat(original)
                self.fstat_mock.side_effect = metadata
                self.run_launcher("SHARED_CACHE_GRANT_DIRECTORY")

    def test_leaf_symlinks_in_directory_outside_and_dangling_are_denied(self):
        for name, target in (("inside", self.paths["GRANTS"] / "other.json"),
                             ("outside", self.tmp / "outside.json"),
                             ("dangling", self.tmp / "absent.json")):
            with self.subTest(name=name):
                if name != "dangling":
                    target.write_text(json.dumps(self.grant))
                self.grant_path.symlink_to(target)
                self.run_launcher("SHARED_CACHE_GRANT_READ", write_grant=False)
                self.grant_path.unlink()

    def test_symlinked_grant_directory_is_denied(self):
        original = self.paths["GRANTS"]
        replacement = self.tmp / "other-grants"
        original.rename(replacement)
        original.symlink_to(replacement, target_is_directory=True)
        self.run_launcher("SHARED_CACHE_GRANT_DIRECTORY")

    def test_hostile_tokens_and_missing_grant_are_denied(self):
        for token in ("../escape", "/tmp/escape", "short", "a" * 97, "bad token", None):
            with self.subTest(token=token):
                self.manifest["shared_cache_grant_token"] = token
                self.run_launcher("SHARED_CACHE_TOKEN", write_grant=False)
        self.manifest["shared_cache_grant_token"] = self.token
        self.run_launcher("SHARED_CACHE_GRANT_READ", write_grant=False)

    def test_directory_instead_of_grant_is_denied(self):
        self.grant_path.mkdir()
        self.run_launcher("SHARED_CACHE_GRANT_PERMISSIONS", write_grant=False)

    def test_fifo_grant_is_nonblocking_and_denied(self):
        os.mkfifo(self.grant_path)
        self.run_launcher("SHARED_CACHE_GRANT_PERMISSIONS", write_grant=False)

    def test_nonobject_malformed_and_oversized_grants_denied(self):
        for raw, expected in (("[]", "SHARED_CACHE_GRANT_SCHEMA"), ("null", "SHARED_CACHE_GRANT_SCHEMA"),
                              ("{broken", "SHARED_CACHE_GRANT_READ"), (" " * 65537, "SHARED_CACHE_GRANT_SIZE")):
            with self.subTest(expected=expected):
                self.grant_path.write_text(raw)
                self.run_launcher(expected, write_grant=False)

    def test_unopened_path_replacement_cannot_change_verified_descriptor(self):
        self.grant_path.write_text(json.dumps(self.grant))
        opened = []
        def open_race(path, flags, *args, **kwargs):
            fd = self.real_open(path, flags, *args, **kwargs)
            if path == self.token + ".json":
                opened.append((flags, kwargs.get("dir_fd")))
                hostile = dict(self.grant, max_timeout_seconds=0)
                replacement = self.paths["GRANTS"] / "replacement.json"
                replacement.write_text(json.dumps(hostile))
                os.replace(replacement, self.grant_path)
            return fd
        with mock.patch.object(os, "open", side_effect=open_race):
            self.run_launcher(write_grant=False)
        self.assertEqual(len(opened), 1)
        self.assertTrue(opened[0][0] & os.O_NOFOLLOW)
        self.assertTrue(opened[0][0] & os.O_NONBLOCK)
        self.assertIsInstance(opened[0][1], int)

    def test_ordinary_none_requires_no_grant_and_masks_shared_root(self):
        self.manifest.update(shared_cache_role="NONE", shared_cache_resource_id=None, shared_cache_grant_token=None)
        receipt, command = self.run_launcher(write_grant=False)
        self.assertEqual(receipt["shared_cache_role"], "NONE")
        self.assertIn("--property=InaccessiblePaths=" + str(self.paths["SHARED_ROOT"]), command)
        self.assertEqual([x for x in command if x.startswith("--property=ReadWritePaths=")],
                         ["--property=ReadWritePaths=" + str(self.output)])

    def test_smoke_read_only_and_consume_are_read_only(self):
        self.manifest["shared_cache_role"] = self.grant["role"] = "SMOKE_READ_ONLY"
        _, command = self.run_launcher()
        self.assertIn("--property=ReadOnlyPaths=" + str(self.smoke), command)
        self.manifest["shared_cache_role"] = self.grant["role"] = "CONSUME_READ_ONLY"
        self.manifest["shared_cache_resource_id"] = self.grant["resource_id"] = RESOURCE_ID
        self.grant.update(verified_dataset_record="synthetic", evidence_access_receipt="synthetic")
        _, command = self.run_launcher()
        self.assertIn("--property=ReadOnlyPaths=" + str(self.paths["SHARED_ROOT"]), command)
        self.assertEqual([x for x in command if x.startswith("--property=ReadWritePaths=")],
                         ["--property=ReadWritePaths=" + str(self.output)])

    def test_acquire_requires_frozen_entrypoint_and_prerequisites(self):
        self.manifest["shared_cache_role"] = self.grant["role"] = "ACQUIRE_WRITE"
        self.manifest["shared_cache_resource_id"] = self.grant["resource_id"] = RESOURCE_ID
        self.run_launcher("SHARED_CACHE_ACQUIRE_BINDING")

    def test_scope_binding_expiry_and_smoke_network_preserved(self):
        for field, value, expected in (("task_id", "wrong", "SHARED_CACHE_GRANT_SCOPE"),
            ("entrypoint_sha256", "0" * 64, "SHARED_CACHE_GRANT_BINDING"),
            ("t3_user_approval_ref", "", "SHARED_CACHE_T3_REF"),
            ("expires_utc", "2000-01-01T00:00:00Z", "SHARED_CACHE_GRANT_EXPIRED")):
            original = self.grant[field]
            with self.subTest(field=field):
                self.grant[field] = value
                self.run_launcher(expected)
            self.grant[field] = original
        self.manifest["network_profile"] = self.grant["network_profile"] = "public_research"
        self.run_launcher("SHARED_CACHE_SMOKE_MUST_BE_OFFLINE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
