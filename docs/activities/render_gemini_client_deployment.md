# Render Deployment Activity for the Gemini Client

This activity documents how to deploy the Gemini client as a separate web service from the MCP server.

Current deployed service URL:

```text
https://gemini-mcp-client.onrender.com
```

## App Location

The Gemini client now lives in:

- `gemini_client/`

Key files:

- `gemini_client/simulated_gemini_client.py`
- `gemini_client/simulated_gemini_http_server.py`
- `gemini_client/requirements.txt`
- `gemini_client/.env.example`

## Deployment Goal

Deploy the Gemini client as its own Render web service that:

- accepts HTTP requests
- calls the deployed MCP server
- sends the structured MCP result to Gemini
- returns a JSON response

## Important Repo Structure Note

Do not set the Render `Root Directory` to `gemini_client`.

This Gemini service currently imports shared code from the repository root, including the existing prompt module. If Render is restricted to `gemini_client` as the root directory, files outside that directory will not be available to the service at build time or runtime.

For this reason, the Gemini client service should currently be deployed from the repository root.

## Required Environment Variables

Set these in Render for the Gemini client service:

```text
GEMINI_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-2.5-flash
MCP_SERVER_URL=https://mcp-cicd-test.onrender.com/mcp/
```

Notes:

- `GEMINI_API_KEY` is required for the `/explain` endpoint
- `MCP_SERVER_URL` should point to the deployed MCP server, not localhost
- `GEMINI_MODEL` can remain `gemini-2.5-flash` unless you intentionally change models

## Local Run

Install dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

Run the web service:

```bash
uvicorn gemini_client.simulated_gemini_http_server:app --host 127.0.0.1 --port 8004
```

Test locally:

```text
http://localhost:8004/
http://localhost:8004/health
http://localhost:8004/docs
```

Optional local environment values:

```text
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
MCP_SERVER_URL=https://mcp-cicd-test.onrender.com/mcp/
```

## Render Settings

Create a separate Render `Web Service` for the Gemini client.

Use:

- Service type: `Web Service`
- Runtime: `Python`
- Root Directory: leave blank

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
uvicorn gemini_client.simulated_gemini_http_server:app --host 0.0.0.0 --port $PORT
```

Health Check Path:

```text
/health
```

Why these settings matter:

- the app binds to `0.0.0.0` so Render can route traffic to it
- the app uses `$PORT`, which Render injects at runtime
- the build runs from the repo root so shared modules remain importable

## Render Deployment Steps

1. Push the current repository state to GitHub.
2. In Render, click `New` -> `Web Service`.
3. Connect the same GitHub repository used for the MCP server.
4. Enter a service name such as `gemini-mcp-client`.
5. Leave `Root Directory` empty.
6. Set the build command to `pip install -r requirements.txt`.
7. Set the start command to `uvicorn gemini_client.simulated_gemini_http_server:app --host 0.0.0.0 --port $PORT`.
8. Set the health check path to `/health`.
9. Add the required environment variables.
10. Create the web service and wait for the first deploy to complete.

## Post-Deploy Verification

Test the base service endpoints first:

```bash
curl -s https://gemini-mcp-client.onrender.com/
curl -s https://gemini-mcp-client.onrender.com/health
```

Then test the Gemini plus MCP flow:

```bash
curl -s https://gemini-mcp-client.onrender.com/explain \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can you explain how to convert 10 km to miles?",
    "input_value": "10",
    "input_unit": "kilometers",
    "target_unit": "miles",
    "tool_name": "kilometers_to_miles",
    "tool_arguments": {
      "kilometers": 10
    }
  }'
```

This uses the explicitly registered MCP tool name `kilometers_to_miles`, which is listed in the session 14 MCP curl activity.

Expected response shape:

- `question`
- `tool_name`
- `tool_arguments`
- `mcp_server_url`
- `mcp_elapsed_ms`
- `mcp_result`
- `explanation`

## Example Request

Tool name based on the session 14 tool list:

```bash
curl -s https://gemini-mcp-client.onrender.com/explain \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can you explain how to convert 10 km to miles?",
    "input_value": "10",
    "input_unit": "kilometers",
    "target_unit": "miles",
    "tool_name": "kilometers_to_miles_kilometers_to_miles_post",
    "tool_arguments": {
      "kilometers": 10
    }
  }'
```

Known-good MCP tool names from `mcp_curl_tests_session14.md` include:

- `fahrenheit_to_celsius_fahrenheit_to_celsius_post`
- `kilometers_to_miles_kilometers_to_miles_post`
- `miles_to_kilometers_miles_to_kilometers_post`
- `kilometers_to_miles`

## Additional Gemini Client curl Examples

### Another conversion tool

This example uses the Fahrenheit to Celsius MCP tool through the Gemini client:

```bash
curl -s https://gemini-mcp-client.onrender.com/explain \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can you explain how to convert 77 degrees Fahrenheit to Celsius?",
    "input_value": "77",
    "input_unit": "fahrenheit",
    "target_unit": "celsius",
    "tool_name": "fahrenheit_to_celsius_fahrenheit_to_celsius_post",
    "tool_arguments": {
      "fahrenheit": 77
    }
  }'
```

### `api_usage` prompt example

The Gemini client `/explain` endpoint does not call MCP prompts directly. To test the `api_usage` prompt itself, call the deployed MCP server:

```bash
MCP_BASE="https://mcp-cicd-test.onrender.com"
MCP="$MCP_BASE/mcp/"
ACCEPT="Accept: application/json, text/event-stream"
PROTO="MCP-Protocol-Version: 2025-06-18"
SESSION=$(curl -sD - -o /dev/null "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -d '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}' \
  | awk 'BEGIN{IGNORECASE=1} /^mcp-session-id:/ {sub(/\r$/,""); print $2}')
```

```bash
curl -s "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":21,"method":"prompts/get","params":{"name":"api_usage","arguments":{"operation":"kilometers_to_miles"}}}'
```

### Resource example

The Gemini client `/explain` endpoint does not read MCP resources directly. To test a resource from the deployed MCP server, use:

```bash
curl -s "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":22,"method":"resources/read","params":{"uri":"resource://converter/unit_reference"}}'
```

Notes:

- use the Gemini client `/explain` endpoint for tool-backed explanation flows
- use the MCP `/mcp/` endpoint directly for prompt and resource testing

## Troubleshooting

If the service fails to start:

- confirm the start command uses `gemini_client.simulated_gemini_http_server:app`
- confirm the build command uses the repo root `requirements.txt`
- confirm the service root directory is blank, not `gemini_client`

If `/health` works but `/explain` fails:

- check that `GEMINI_API_KEY` is set in Render
- confirm `MCP_SERVER_URL` points to `https://mcp-cicd-test.onrender.com/mcp/`
- verify the deployed MCP service is awake and reachable

If the first request is slow:

- Render free services may spin down after inactivity
- retry after the service wakes up

## Successful Deployment Record

The Gemini client has now been deployed successfully at:

```text
https://gemini-mcp-client.onrender.com
```

Confirmed verification targets:

```text
https://gemini-mcp-client.onrender.com/
https://gemini-mcp-client.onrender.com/health
https://gemini-mcp-client.onrender.com/explain
```

Confirmed integration path:

- Gemini client service on Render
- deployed MCP server at `https://mcp-cicd-test.onrender.com/mcp/`
- Gemini API via `GEMINI_API_KEY`
