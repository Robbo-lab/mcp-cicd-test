from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request

from gemini_client.simulated_gemini_client import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    KM_TO_MILES_TOOL,
    MCP_SERVER_URL,
    build_gemini_prompt,
    call_mcp_tool,
    generate_gemini_explanation,
    require_env,
)

load_dotenv()

app = FastAPI(
    title="Gemini MCP Client Without Pydantic Models",
    description="HTTP wrapper for the Gemini client using manual request parsing.",
    version="1.0.0",
)


def require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if value is None or not isinstance(value, str) or not value.strip():
        raise HTTPException(status_code=422, detail=f"Missing or invalid string field: {key}")
    return value


def require_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise HTTPException(status_code=422, detail=f"Missing or invalid object field: {key}")
    return value


def parse_explain_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Parse the incoming HTTP request body without using a Pydantic model."""

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object.")

    return {
        "question": require_string(payload, "question"),
        "input_value": require_string(payload, "input_value"),
        "input_unit": require_string(payload, "input_unit"),
        "target_unit": require_string(payload, "target_unit"),
        "tool_name": require_string(payload, "tool_name"),
        "tool_arguments": require_object(payload, "tool_arguments"),
    }


async def run_demo(
    *,
    user_question: str,
    input_value: str,
    input_unit: str,
    target_unit: str,
    tool_name: str,
    tool_arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    Run the Gemini + MCP integration flow for one HTTP request.

    Workflow:
    1. Send a request to the MCP server at MCP_SERVER_URL.
    2. Receive a structured MCP tool result back into this client.
    3. Send that result to Gemini for explanation only.
    """

    api_key = require_env(GEMINI_API_KEY or os.getenv("GEMINI_API_KEY"), "GEMINI_API_KEY")

    mcp_result, elapsed_ms = await call_mcp_tool(
        tool_name,
        tool_arguments,
    )

    prompt = build_gemini_prompt(
        user_question=user_question,
        input_value=input_value,
        input_unit=input_unit,
        target_unit=target_unit,
        mcp_result=mcp_result,
    )

    explanation = generate_gemini_explanation(
        api_key=api_key,
        prompt=prompt,
        model=os.getenv("GEMINI_MODEL", GEMINI_MODEL),
    )

    return {
        "question": user_question,
        "tool_name": tool_name,
        "tool_arguments": tool_arguments,
        "mcp_server_url": os.getenv("MCP_SERVER_URL", MCP_SERVER_URL),
        "mcp_elapsed_ms": round(elapsed_ms, 2),
        "mcp_result": mcp_result,
        "explanation": explanation,
    }


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "gemini-mcp-client-no-pydantic",
        "status": "ok",
        "health": "/health",
        "explain": "/explain",
        "default_tool": KM_TO_MILES_TOOL,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "mcp_server_url": MCP_SERVER_URL,
        "gemini_model": GEMINI_MODEL,
    }


@app.post("/explain")
async def explain(request: Request) -> dict[str, Any]:
    payload = parse_explain_request(await request.json())
    return await run_demo(
        user_question=payload["question"],
        input_value=payload["input_value"],
        input_unit=payload["input_unit"],
        target_unit=payload["target_unit"],
        tool_name=payload["tool_name"],
        tool_arguments=payload["tool_arguments"],
    )
