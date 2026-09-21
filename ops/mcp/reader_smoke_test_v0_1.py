from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

from mcp import Client

SERVER_PATH = Path("/opt/botmarket-research/app/reader_server.py")


def load_module():
    spec = importlib.util.spec_from_file_location("botmarket_reader_server", SERVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load reader server")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


async def main() -> None:
    mod = load_module()
    server = mod.mcp

    async with Client(server) as client:
        tools = await client.list_tools()
        names = sorted(t.name for t in tools)
        expected = ["list_files", "list_roots", "read_text"]
        if names != expected:
            raise RuntimeError(f"unexpected tools: {names}")

        roots = await client.call_tool("list_roots", {})
        if roots.is_error:
            raise RuntimeError("list_roots returned error")

        listing = await client.call_tool(
            "list_files",
            {"root": "b15_identity_inventory", "path": ".", "limit": 20},
        )
        if listing.is_error:
            raise RuntimeError("list_files returned error")

        read = await client.call_tool(
            "read_text",
            {
                "root": "b15_identity_inventory",
                "path": "20260920T210446Z/run_manifest.json",
                "max_bytes": 4096,
            },
        )
        if read.is_error:
            raise RuntimeError("read_text returned error")

    # Negative filesystem test is deliberately performed on the same resolver
    # used by the tools, without relying on client-specific error semantics.
    try:
        mod._resolve(
            "b15_identity_inventory",
            "../../etc/passwd",
            require_file=True,
        )
    except (ValueError, FileNotFoundError):
        pass
    else:
        raise RuntimeError("path traversal negative test unexpectedly succeeded")

    print("tools =", names)
    print("PASS: list_roots")
    print("PASS: list_files")
    print("PASS: read_text")
    print("PASS: path traversal blocked")
    print("READER_MCP_INPROCESS_SMOKE_PASS")


if __name__ == "__main__":
    asyncio.run(main())
