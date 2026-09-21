from __future__ import annotations

import asyncio

from mcp import Client

URL = "http://127.0.0.1:8765/mcp"


async def main() -> None:
    async with Client(URL) as client:
        tools_result = await client.list_tools()
        names = sorted(t.name for t in tools_result.tools)
        expected = ["list_files", "list_roots", "read_text"]
        if names != expected:
            raise RuntimeError(f"unexpected tools: {names}")

        roots = await client.call_tool("list_roots", {})
        if roots.is_error:
            raise RuntimeError("list_roots returned tool error")

        listing = await client.call_tool(
            "list_files",
            {"root": "b15_identity_inventory", "path": ".", "limit": 20},
        )
        if listing.is_error:
            raise RuntimeError("list_files returned tool error")

        read = await client.call_tool(
            "read_text",
            {
                "root": "b15_identity_inventory",
                "path": "20260920T210446Z/run_manifest.json",
                "max_bytes": 4096,
            },
        )
        if read.is_error:
            raise RuntimeError("read_text returned tool error")

        escaped = await client.call_tool(
            "read_text",
            {
                "root": "b15_identity_inventory",
                "path": "../../etc/passwd",
                "max_bytes": 1024,
            },
        )
        if not escaped.is_error:
            raise RuntimeError("path traversal unexpectedly succeeded")

        print("url =", URL)
        print("tools =", names)
        print("PASS: HTTP list_roots")
        print("PASS: HTTP list_files")
        print("PASS: HTTP read_text")
        print("PASS: HTTP path traversal blocked")
        print("READER_MCP_STREAMABLE_HTTP_SMOKE_PASS")


if __name__ == "__main__":
    asyncio.run(main())
