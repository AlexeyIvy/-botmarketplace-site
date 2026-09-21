from __future__ import annotations

import asyncio
import sys
import time

from mcp import Client

URL = "http://127.0.0.1:8765/mcp"
EXPECTED_TOOLS = {"list_files", "list_roots", "read_text"}
TIMEOUT_SECONDS = 20.0
INTERVAL_SECONDS = 0.25


async def probe_once() -> None:
    async with Client(URL) as client:
        result = await client.list_tools()
        names = {tool.name for tool in result.tools}
        if names != EXPECTED_TOOLS:
            raise RuntimeError(
                f"unexpected tool surface: {sorted(names)}"
            )

        roots = await client.call_tool("list_roots", {})
        if roots.is_error:
            raise RuntimeError("list_roots returned tool error")


async def main() -> int:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    attempts = 0
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        attempts += 1
        try:
            await probe_once()
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(INTERVAL_SECONDS)
            continue

        print(f"READER_MCP_READY attempts={attempts} url={URL}")
        return 0

    print(
        "READER_MCP_NOT_READY "
        f"attempts={attempts} "
        f"last_error={type(last_error).__name__ if last_error else 'none'}: "
        f"{last_error}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
