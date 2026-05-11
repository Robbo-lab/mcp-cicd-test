from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from gemini_client.simulated_gemini_client import (
    GEMINI_MODEL,
    MCP_SERVER_URL,
    build_gemini_prompt,
    call_mcp_tool,
    generate_gemini_explanation,
    require_env,
)

load_dotenv()

app = FastAPI(
    title="Gemini MCP Client",
    description="HTTP wrapper for the Gemini client that calls the deployed MCP server.",
    version="1.0.0",
)


class ExplainRequest(BaseModel):
    question: str = Field(..., description="Learner question for Gemini to answer.")
    input_value: str = Field(..., description="Original numeric input as text.")
    input_unit: str = Field(..., description="Source unit.")
    target_unit: str = Field(..., description="Target unit.")
    tool_name: str = Field(..., description="MCP tool to call.")
    tool_arguments: dict[str, Any] = Field(..., description="Arguments for the MCP tool call.")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "gemini-mcp-client",
        "status": "ok",
        "health": "/health",
        "explain": "/explain",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "mcp_server_url": MCP_SERVER_URL,
        "gemini_model": GEMINI_MODEL,
    }


@app.post("/explain")
async def explain(request: ExplainRequest) -> dict[str, Any]:
    api_key = require_env(os.getenv("GEMINI_API_KEY"), "GEMINI_API_KEY")

    mcp_result, elapsed_ms = await call_mcp_tool(
        request.tool_name,
        request.tool_arguments,
    )

    prompt = build_gemini_prompt(
        user_question=request.question,
        input_value=request.input_value,
        input_unit=request.input_unit,
        target_unit=request.target_unit,
        mcp_result=mcp_result,
    )

    explanation = generate_gemini_explanation(
        api_key=api_key,
        prompt=prompt,
        model=os.getenv("GEMINI_MODEL", GEMINI_MODEL),
    )

    return {
        "question": request.question,
        "tool_name": request.tool_name,
        "tool_arguments": request.tool_arguments,
        "mcp_server_url": os.getenv("MCP_SERVER_URL", MCP_SERVER_URL),
        "mcp_elapsed_ms": round(elapsed_ms, 2),
        "mcp_result": mcp_result,
        "explanation": explanation,
    }
