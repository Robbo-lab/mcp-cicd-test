from __future__ import annotations

import asyncio
import os
import time
from typing import Any

from dotenv import load_dotenv
from fastmcp import Client
from google import genai

from mcp_prompts.converter_prompts import explain_conversion_prompt

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8003/mcp")

KM_TO_MILES_TOOL = "kilometers_to_miles"


def require_env(value: str | None, name: str) -> str:
    """Return an environment variable or raise a clear error."""
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


async def handle_mcp_progress(
    progress: float,
    total: float | None,
    message: str | None,
) -> None:
    """Print MCP progress notifications so they are visible during the demo."""

    if total is None:
        progress_text = f"{progress}"
    else:
        progress_text = f"{progress}/{total}"

    print(f"[MCP progress] {progress_text}: {message or 'update'}")


async def call_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> tuple[Any, float]:
    """
    Send an MCP request to the existing converter MCP server and return its response.

    The calculation happens on the MCP server. This client only orchestrates the
    request/response flow and forwards the structured tool result to Gemini.
    """

    async with Client(
        MCP_SERVER_URL,
        auth="demo-token",
        progress_handler=handle_mcp_progress,
    ) as mcp_client:
        started_at = time.perf_counter()
        result = await mcp_client.call_tool(tool_name, arguments)
        elapsed_ms = (time.perf_counter() - started_at) * 1000

    return result, elapsed_ms


def build_gemini_prompt(
    user_question: str,
    input_value: str,
    input_unit: str,
    target_unit: str,
    mcp_result: Any,
) -> str:
    """
    Build the model-side context sent to Gemini.

    This reuses the existing explain_conversion_prompt helper so the Gemini
    client follows the same teaching prompt pattern as the MCP prompt module.
    Gemini receives the verified MCP response after the tool call completes.
    Gemini explains the result, but it is not asked to perform the calculation.
    """

    prompt_messages = explain_conversion_prompt(
        input_value=input_value,
        input_unit=input_unit,
        target_unit=target_unit,
    )

    sections = [
        """
NOTE FOR THE USER:
This is a simulation of an orchestration client. In a real deployment, this kind of client could be hosted as part of a backend service such as a FastAPI app, a serverless function, or an internal API layer that receives user requests, calls MCP tools, and then sends the verified tool result to Gemini for explanation.
""".strip()
    ]
    sections.extend(f"{message.role.upper()}:\n{message.content}" for message in prompt_messages)
    sections.append(
        f"""
STUDENT QUESTION:
{user_question}

VERIFIED MCP TOOL RESULT:
{mcp_result}

Use the verified MCP tool result as the source of truth for the calculation.
Include a short note that Gemini acted as the agent, but the calculation came from the MCP tool.
""".strip()
    )

    return "\n\n".join(sections)


async def main() -> None:
    """
    Run the Gemini + MCP integration demo.

    Workflow:
    1. Send a request to the MCP server at MCP_SERVER_URL.
    2. Receive a structured MCP tool result back into this client.
    3. Send that result to Gemini for explanation only.
    """

    api_key = require_env(GEMINI_API_KEY, "GEMINI_API_KEY")

    user_question = "Can you explain how to convert 10 km to miles?"

    print("User question:")
    print(user_question)

    print(f"\nCalling MCP tool: {KM_TO_MILES_TOOL}")
    mcp_result, elapsed_ms = await call_mcp_tool(
        KM_TO_MILES_TOOL,
        {"kilometers": 10},
    )

    print(f"MCP structured result ({elapsed_ms:.2f} ms):")
    print(mcp_result)

    prompt = build_gemini_prompt(
        user_question=user_question,
        input_value="10",
        input_unit="km",
        target_unit="miles",
        mcp_result=mcp_result,
    )

    # Gemini is called only after the MCP server has returned a structured result.
    gemini_client = genai.Client(api_key=api_key)

    print("\nGemini streamed explanation:\n")

    stream = gemini_client.models.generate_content_stream(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    for chunk in stream:
        if chunk.text:
            print(chunk.text, end="")

    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
