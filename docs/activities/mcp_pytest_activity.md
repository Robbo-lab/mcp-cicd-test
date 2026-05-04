# Pytest Activity

This activity explains how to run, use, and troubleshoot the MCP pytest suite in this repository.

## What These Tests Cover

The test suite exercises the HTTP + MCP server started by `converter_streamable_http_server.py`.

It covers:

- `tests/test_health.py` for the `/health` endpoint
- `tests/test_lifecycle.py` for MCP `initialize` and `notifications/initialized`
- `tests/test_tools.py` for `tools/list` and `tools/call`
- `tests/test_prompts.py` for `prompts/list` and `prompts/get`
- `tests/test_resources.py` for `resources/list` and `resources/read`
- `tests/test_errors.py` for malformed JSON-RPC requests
- `tests/test_streaming.py` for streamable HTTP response handling
- `tests/conftest.py` for shared fixtures and the `MCPTestClient` helper

## Prerequisites

- Python 3.10+ available locally
- A virtual environment
- Dependencies installed from `requirements.txt`

Current test dependencies already present in this repo:

- `pytest`
- `httpx`

## Setup

From the project root:

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

## MCP Test Settings

These tests assume the following MCP settings:

```bash
export MCP_BASE_URL="http://localhost:8003"
export MCP_PROTOCOL_VERSION="2025-06-18"
```

If you want to set them inline:

```bash
MCP_BASE_URL="http://localhost:8003" MCP_PROTOCOL_VERSION="2025-06-18" pytest -q
```

On Windows PowerShell:

```powershell
$env:MCP_BASE_URL="http://localhost:8003"
$env:MCP_PROTOCOL_VERSION="2025-06-18"
pytest -q
```

## Start the Server

Start the MCP HTTP server in one terminal:

```bash
python converter_streamable_http_server.py
```

The test suite expects the server to be available at:

- `http://localhost:8003/health`
- `http://localhost:8003/mcp/`

## Run All Tests

In a second terminal, from the project root:

```bash
pytest -q
```

## Run Individual Test Files

Run one file at a time when you are checking a specific MCP capability:

```bash
pytest -q tests/test_health.py
pytest -q tests/test_lifecycle.py
pytest -q tests/test_tools.py
pytest -q tests/test_prompts.py
pytest -q tests/test_resources.py
pytest -q tests/test_errors.py
pytest -q tests/test_streaming.py
```

Run a single test:

```bash
pytest -q tests/test_tools.py::test_tools_list
```

## What the Fixtures Do

`tests/conftest.py` provides:

- `base_url` from `MCP_BASE_URL`
- `mcp_url` fixed to `/mcp/`
- `protocol_version` from `MCP_PROTOCOL_VERSION`
- `mcp_headers` with JSON and MCP protocol headers
- `http_client` using `httpx.Client`
- `mcp_client` which initialises an MCP session before each test that needs it

The `MCPTestClient` helper:

- sends JSON-RPC requests
- stores the returned `mcp-session-id`
- automatically reuses the session header for later MCP calls

## How to Use the Tests During Development

1. Start the server with `python converter_streamable_http_server.py`
2. Run `pytest -q tests/test_health.py`
3. Run lifecycle tests to confirm the MCP handshake works
4. Run tools, prompts, and resources tests as you change the data you pass.
5. Run `pytest -q`

If you are changing only one MCP area, run the matching file first instead of the full suite.

## CI Workflow

The GitHub Actions workflow is:

- [.github/workflows/pytest.yml](/Users/robbozinoz/Documents/mcp_session11_example/.github/workflows/pytest.yml)

It does the following:

1. Checks out the repository
2. Sets up Python 3.12
3. Installs dependencies from `requirements.txt`
4. Starts `python converter_streamable_http_server.py`
5. Runs pytest with JUnit XML output
6. Uploads `server.log` and `pytest-results.xml`

## Troubleshooting

If tests fail immediately with connection errors:

- Confirm the server is running
- Confirm it is listening on port `8003`
- Confirm the MCP endpoint includes the trailing slash: `/mcp/`

If MCP tests fail but `/health` passes:

- Check that `MCP_PROTOCOL_VERSION` is set to `2025-06-18`
- Confirm the server returns an `mcp-session-id` header on `initialize`
- Check server logs for MCP request errors

If only `test_tools.py` fails:

- Verify the expected tool name still exists:
  `fahrenheit_to_celsius_fahrenheit_to_celsius_post`

If only `test_prompts.py` fails:

- Verify prompts still include:
  `explain_conversion`
  `api_usage`

If only `test_resources.py` fails:

- Verify a resource URI still contains `unit_reference`

If streaming tests fail:

- Check that the server still supports `Accept: text/event-stream`
- Check the response `content-type`

## Useful Commands

Collect tests without running them:

```bash
pytest --collect-only tests
```

Stop after the first failure:

```bash
pytest -q --maxfail=1
```

Show extra output while debugging:

```bash
pytest -q -s
```
