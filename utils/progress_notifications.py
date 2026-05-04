from __future__ import annotations

from fastmcp import Context


async def report_tool_progress(server_context: Context, message: str) -> None:
    """Emit one simple progress notification for teaching/demo flows."""

    await server_context.report_progress(1, 1, message)
