#!/usr/bin/env python3
"""Offline regression specification for installer v0.2 host-tool trust rules."""

from __future__ import annotations

import importlib.util
import stat
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/research/deploy-sc001-b13c-health-adapter-v0.2.py"


def load_installer():
    spec = importlib.util.spec_from_file_location("sc001_health_installer_v0_2", INSTALLER)
    if spec is None or spec.loader is None:
        raise AssertionError("installer import specification unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def meta(kind, mode, uid=0, gid=0):
    return SimpleNamespace(st_mode=kind | mode, st_uid=uid, st_gid=gid)


class FakeFilesystem:
    def __init__(self, nodes, links=None):
        self.nodes = {str(Path(k)): v for k, v in nodes.items()}
        self.links = {str(Path(k)): v for k, v in (links or {}).items()}

    def lstat(self, path):
        key = str(Path(path))
        if key not in self.nodes:
            raise FileNotFoundError(key)
        return self.nodes[key]

    def readlink(self, path):
        key = str(Path(path))
        if key not in self.links:
            raise OSError(key)
        return self.links[key]


class HostToolSymlinkPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_installer()

    @staticmethod
    def nodes():
        return {
            "/usr/bin": meta(stat.S_IFDIR, 0o755),
            "/usr/bin/python3": meta(stat.S_IFLNK, 0o777),
            "/usr/bin/python3.12": meta(stat.S_IFREG, 0o755),
        }

    def check(self, fs, path="/usr/bin/python3", root="/usr/bin", allow=True):
        self.module._require_host_tool(
            Path(path), Path(root), allow_symlink=allow,
            lstat_fn=fs.lstat, readlink_fn=fs.readlink,
        )

    def fails(self, code, fs, path="/usr/bin/python3", root="/usr/bin", allow=True):
        with self.assertRaises(self.module.DeployError) as caught:
            self.check(fs, path, root, allow)
        self.assertEqual(caught.exception.code, code)

    def test_standard_ubuntu_python_symlink_passes(self):
        self.check(FakeFilesystem(self.nodes(), {"/usr/bin/python3": "python3.12"}))

    def test_regular_executable_behavior_is_preserved(self):
        nodes = self.nodes(); nodes["/usr/bin/python3"] = meta(stat.S_IFREG, 0o755)
        self.check(FakeFilesystem(nodes))

    def test_safe_internal_chain_passes(self):
        nodes = self.nodes()
        nodes["/usr/bin/python3.12"] = meta(stat.S_IFLNK, 0o777)
        nodes["/usr/bin/python3.12-real"] = meta(stat.S_IFREG, 0o755)
        self.check(FakeFilesystem(nodes, {"/usr/bin/python3": "python3.12", "/usr/bin/python3.12": "python3.12-real"}))

    def test_link_owner_must_be_root(self):
        nodes = self.nodes(); nodes["/usr/bin/python3"] = meta(stat.S_IFLNK, 0o777, uid=1000)
        self.fails("HOST_TOOL_TRUST", FakeFilesystem(nodes, {"/usr/bin/python3": "python3.12"}))

    def test_target_owner_must_be_root(self):
        nodes = self.nodes(); nodes["/usr/bin/python3.12"] = meta(stat.S_IFREG, 0o755, uid=1000)
        self.fails("HOST_TOOL_TRUST", FakeFilesystem(nodes, {"/usr/bin/python3": "python3.12"}))

    def test_target_must_not_be_writable(self):
        nodes = self.nodes(); nodes["/usr/bin/python3.12"] = meta(stat.S_IFREG, 0o775)
        self.fails("HOST_TOOL_TRUST", FakeFilesystem(nodes, {"/usr/bin/python3": "python3.12"}))

    def test_target_must_be_executable(self):
        nodes = self.nodes(); nodes["/usr/bin/python3.12"] = meta(stat.S_IFREG, 0o644)
        self.fails("HOST_TOOL_TRUST", FakeFilesystem(nodes, {"/usr/bin/python3": "python3.12"}))

    def test_dangling_target_is_missing(self):
        nodes = self.nodes(); del nodes["/usr/bin/python3.12"]
        self.fails("HOST_TOOL_MISSING", FakeFilesystem(nodes, {"/usr/bin/python3": "python3.12"}))

    def test_non_regular_target_is_rejected(self):
        nodes = self.nodes(); nodes["/usr/bin/python3.12"] = meta(stat.S_IFDIR, 0o755)
        self.fails("HOST_TOOL_TYPE", FakeFilesystem(nodes, {"/usr/bin/python3": "python3.12"}))

    def test_relative_escape_is_rejected(self):
        self.fails("HOST_TOOL_TYPE", FakeFilesystem(self.nodes(), {"/usr/bin/python3": "../../tmp/python3"}))

    def test_absolute_escape_is_rejected(self):
        self.fails("HOST_TOOL_TYPE", FakeFilesystem(self.nodes(), {"/usr/bin/python3": "/opt/python3"}))

    def test_cycle_is_rejected(self):
        nodes = self.nodes(); nodes["/usr/bin/python3.12"] = meta(stat.S_IFLNK, 0o777)
        self.fails("HOST_TOOL_TYPE", FakeFilesystem(nodes, {"/usr/bin/python3": "python3.12", "/usr/bin/python3.12": "python3"}))

    def test_visudo_symlink_remains_forbidden(self):
        nodes = {"/usr/sbin": meta(stat.S_IFDIR, 0o755), "/usr/sbin/visudo": meta(stat.S_IFLNK, 0o777), "/usr/sbin/visudo.real": meta(stat.S_IFREG, 0o755)}
        self.fails("HOST_TOOL_TYPE", FakeFilesystem(nodes, {"/usr/sbin/visudo": "visudo.real"}), "/usr/sbin/visudo", "/usr/sbin", False)

    def test_untrusted_tool_directory_is_rejected(self):
        nodes = self.nodes(); nodes["/usr/bin"] = meta(stat.S_IFDIR, 0o777)
        self.fails("HOST_TOOL_TRUST", FakeFilesystem(nodes, {"/usr/bin/python3": "python3.12"}))


if __name__ == "__main__":
    unittest.main()
