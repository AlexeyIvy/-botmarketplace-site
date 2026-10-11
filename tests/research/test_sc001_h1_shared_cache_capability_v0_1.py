#!/usr/bin/env python3
"""Focused static/unit checks plus the future two-job offline smoke entrypoint.

No smoke is run by SC001-H1-004J.  A later exact T3 authorization must install
the capability, create a root-owned grant, and invoke writer then reader in two
different Test Executor jobs.  The same token/namespace is retained while the
root-owned grant is changed from SMOKE_WRITE to SMOKE_READ_ONLY.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import unittest
from pathlib import Path

RESOURCE_ID = "b97ffeefed4dd1b4caa771df734b59b5a6dc2b6a9ada3b3c9b8ce0c6de6319bf"
SHARED_ROOT = Path("/var/lib/botmarket-test-executor/shared-data/sc001")
SMOKE_PARENT = SHARED_ROOT / "_capability_smoke"
TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{7,95}$")
DEPLOY = Path(__file__).parents[2] / "scripts/research/deploy_sc001_h1_shared_cache_capability_v0_1.py"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, obj: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("x", encoding="utf-8") as stream:
        json.dump(obj, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def load_deployer():
    spec = importlib.util.spec_from_file_location("sc001_h1_capability_deployer", DEPLOY)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load deployer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StaticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_deployer()

    def test_frozen_identities_and_limits(self):
        self.assertEqual(self.mod.RESOURCE_ID, RESOURCE_ID)
        self.assertEqual(self.mod.MAX_SINGLE_DATASET_BYTES, 5 * 1024**3)
        self.assertEqual(self.mod.MAX_PEAK_WORKSPACE_INCREMENT, 15 * 1024**3)
        self.assertEqual(self.mod.MAX_TIMEOUT_SECONDS, 900)
        self.assertEqual(
            self.mod.ACQUISITION_SHA256,
            "1eb597e3186023540a5ab9929f433f7f5a81b9d587f10386cf2e3e55f625c760",
        )

    def test_replace_once_fails_closed(self):
        self.assertEqual(self.mod.replace_once("a-b", "-", ":", "x"), "a:b")
        with self.assertRaises(self.mod.GateError):
            self.mod.replace_once("a-b-b", "-", ":", "x")
        with self.assertRaises(self.mod.GateError):
            self.mod.replace_once("ab", "-", ":", "x")

    def test_policy_patch_preserves_hard_limits_and_adds_no_grant(self):
        policy = {
            "schema": "botmarket.test_executor_policy.v1",
            "max_timeout_seconds": 900,
            "max_concurrent_jobs": 1,
            "memory_max_bytes": 1073741824,
            "tasks_max": 64,
            "cpu_quota_percent": 200,
            "trading_credentials_available_to_jobs": False,
            "arbitrary_shell_tool": False,
            "repo_write": False,
            "sudo_inside_job": False,
        }
        patched = json.loads(self.mod.patch_policy(json.dumps(policy)))
        cap = patched["shared_cache"]
        self.assertEqual(cap["resource_id"], RESOURCE_ID)
        self.assertEqual(cap["ordinary_jobs_access"], "NONE")
        self.assertFalse(cap["grants_created_by_install"])
        self.assertEqual(cap["max_single_dataset_bytes"], 5 * 1024**3)
        self.assertEqual(cap["max_peak_workspace_increment"], 15 * 1024**3)
        self.assertEqual(cap["max_timeout_seconds"], 900)

    def test_canonical_plan_hash_is_stable(self):
        obj = {"z": 1, "a": ["x", False]}
        self.assertEqual(self.mod.canonical_bytes(obj), b'{"a":["x",false],"z":1}\n')

    def test_deployer_does_not_offer_grant_install_command(self):
        actions = self.mod.parser()._subparsers._group_actions
        choices = set()
        for action in actions:
            choices.update(getattr(action, "choices", {}))
        self.assertEqual(choices, {"plan", "apply", "rollback"})


def checked_environment(phase: str, token: str) -> tuple[Path, Path]:
    if not TOKEN_RE.fullmatch(token):
        raise RuntimeError("SMOKE_TOKEN")
    if os.environ.get("BM_TEST_NETWORK_PROFILE") != "offline":
        raise RuntimeError("BM_NETWORK_NOT_OFFLINE")
    if os.environ.get("SC001_NETWORK_PROFILE") != "offline":
        raise RuntimeError("SC001_NETWORK_NOT_OFFLINE")
    expected_role = "SMOKE_WRITE" if phase == "writer" else "SMOKE_READ_ONLY"
    if os.environ.get("SC001_SHARED_CACHE_ROLE") != expected_role:
        raise RuntimeError("SMOKE_ROLE")
    root_text = os.environ.get("SC001_DATA_ROOT")
    output_text = os.environ.get("BM_TEST_OUTPUT_DIR")
    if not root_text or not output_text:
        raise RuntimeError("SMOKE_ENV_MISSING")
    root = Path(root_text)
    output = Path(output_text)
    expected = SMOKE_PARENT / token
    if root != expected or root.resolve() != expected:
        raise RuntimeError("SMOKE_ROOT")
    if not root.is_dir() or root.is_symlink():
        raise RuntimeError("SMOKE_ROOT_TYPE")
    if not output.is_dir() or output.is_symlink():
        raise RuntimeError("SMOKE_OUTPUT_TYPE")
    if root == output or output in root.parents or root in output.parents:
        raise RuntimeError("SMOKE_OUTPUT_SEPARATION")
    return root, output


def must_deny_write(path: Path) -> None:
    try:
        with path.open("xb") as stream:
            stream.write(b"must-not-persist")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError:
        return
    try:
        path.unlink()
    finally:
        raise RuntimeError(f"WRITE_BOUNDARY_FAILURE:{path}")


def writer(token: str) -> dict:
    root, output = checked_environment("writer", token)
    sentinel = root / "sentinel.bin"
    part = root / "sentinel.bin.part"
    if sentinel.exists() or part.exists():
        raise RuntimeError("SMOKE_NAMESPACE_NOT_FRESH")
    must_deny_write(SHARED_ROOT / ("escape-" + token))
    payload = ("SC001-H1-004J:" + token + "\n").encode()
    with part.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(part, sentinel)
    result = {
        "schema": "sc001.h1_shared_cache_smoke_writer.v0.1",
        "phase": "writer",
        "token": token,
        "sentinel_sha256": sha256_bytes(payload),
        "sentinel_bytes": len(payload),
        "network_profile": "offline",
        "market_data_bytes": 0,
    }
    atomic_json(output / "shared_cache_smoke_writer.json", result)
    return result


def reader(token: str, expected_sha256: str) -> dict:
    root, output = checked_environment("reader", token)
    sentinel = root / "sentinel.bin"
    if not sentinel.is_file() or sentinel.is_symlink():
        raise RuntimeError("SMOKE_SENTINEL_MISSING")
    data = sentinel.read_bytes()
    actual = sha256_bytes(data)
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256) or actual != expected_sha256:
        raise RuntimeError("SMOKE_SENTINEL_SHA")
    must_deny_write(root / "read_only_probe")
    result = {
        "schema": "sc001.h1_shared_cache_smoke_reader.v0.1",
        "phase": "reader",
        "token": token,
        "sentinel_sha256": actual,
        "sentinel_bytes": len(data),
        "network_profile": "offline",
        "persistence_across_jobs": True,
        "read_only_mount": True,
        "market_data_bytes": 0,
    }
    atomic_json(output / "shared_cache_smoke_reader.json", result)
    return result


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=("writer", "reader"))
    p.add_argument("--token")
    p.add_argument("--expected-sha256")
    p.add_argument("--unit-tests", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    if args.unit_tests:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(StaticContractTests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    if not args.phase or not args.token:
        raise SystemExit("--phase and --token are required for smoke")
    if args.phase == "writer":
        result = writer(args.token)
    else:
        if not args.expected_sha256:
            raise SystemExit("--expected-sha256 is required for reader")
        result = reader(args.token, args.expected_sha256)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
