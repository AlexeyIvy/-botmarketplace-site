"""SC001-E002 Q1 execution metadata preflight v0.3.

Infrastructure/parser-only repair after v0.2 failed closed on the current
OKX /api/v5/public/market-data-history response shape. No financial or
statistical rule changes. No alpha, no execution P&L, no Q2/Validation/Final.

This thin wrapper imports the v0.2 implementation, preserves all of its
historical contract/fee/funding rules, and replaces only the historical file
metadata extractor so it accepts the current public endpoint's standard
array/object nesting without assuming the old private data.details layout.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "sc001_e002_okx_q1_execution_metadata_preflight_v0_2.py"

spec = importlib.util.spec_from_file_location("sc001_exec_meta_v02", PARENT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load v0.2 preflight")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# Preserve all v0.2 economics/metadata constants, but isolate v0.3 outputs.
m.VERSION = "0.3"
m.ARCHIVE_DIR = m.OUTDIR / "funding_archives_v0_3"
m.REPORT = m.OUTDIR / "sc001_e002_okx_q1_execution_metadata_preflight_v0_3.json"
m.FUNDING = m.OUTDIR / "sc001_e002_okx_q1_funding_rates_v0_3.json"


def _walk_file_nodes(node):
    """Yield file-like dicts from any nested OKX public-response shape."""
    if isinstance(node, dict):
        filename = node.get("filename") or node.get("fileName")
        url = node.get("url") or node.get("fileUrl") or node.get("downloadUrl")
        if isinstance(filename, str) and isinstance(url, str):
            yield node
        for value in node.values():
            yield from _walk_file_nodes(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_file_nodes(value)


def historical_funding_files_v03() -> list[dict]:
    obj = m.get_json(
        "/api/v5/public/market-data-history",
        {
            "module": "3",
            "instType": "SWAP",
            "instFamilyList": m.INST_FAMILY,
            "dateAggrType": "monthly",
            "begin": str(m.ARCHIVE_BEGIN_MS),
            "end": str(m.ARCHIVE_END_MS),
        },
    )

    data = obj.get("data")
    print("market-data-history data shape =", type(data).__name__)
    if isinstance(data, list):
        print("market-data-history data items =", len(data))
    elif isinstance(data, dict):
        print("market-data-history data keys =", sorted(data.keys()))

    files: dict[str, dict] = {}
    raw_nodes = list(_walk_file_nodes(data))
    print("market-data-history file nodes discovered =", len(raw_nodes))

    for g in raw_nodes:
        filename = g.get("filename") or g.get("fileName")
        url = g.get("url") or g.get("fileUrl") or g.get("downloadUrl")
        if not isinstance(filename, str) or not isinstance(url, str):
            continue
        if not m.trusted_archive_url(url, filename):
            raise RuntimeError(f"untrusted historical funding archive URL: {filename} {url}")
        prev = files.get(filename)
        if prev is not None and prev.get("url") != url:
            raise RuntimeError(f"same funding filename returned with multiple URLs: {filename}")
        files[filename] = {
            "filename": filename,
            "url": url,
            "sizeMB_raw": g.get("sizeMB") or g.get("sizeMb") or g.get("size"),
        }

    if not files:
        # Fail closed, but include enough schema diagnostics to repair without
        # dumping the full response or any credentials (endpoint is public).
        if isinstance(data, list) and data:
            sample = data[0]
            if isinstance(sample, dict):
                raise RuntimeError(
                    "no archive file nodes found; first data item keys="
                    + repr(sorted(sample.keys()))
                )
            raise RuntimeError(
                "no archive file nodes found; first data item type="
                + type(sample).__name__
            )
        raise RuntimeError("no official OKX historical funding archive files returned")

    return [files[k] for k in sorted(files)]


m.historical_funding_files = historical_funding_files_v03

if __name__ == "__main__":
    m.main()
