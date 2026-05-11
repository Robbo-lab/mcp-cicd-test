# Render Deployment Activity for the Gemini Client

This activity documents how to deploy the Gemini client as a separate web service from the MCP server.

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
curl -s https://your-gemini-client.onrender.com/
curl -s https://your-gemini-client.onrender.com/health
```

Then test the Gemini plus MCP flow:

```bash
curl -s https://your-gemini-client.onrender.com/explain \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can you explain how to convert 10 km to miles?",
    "input_value": "10",
    "input_unit": "km",
    "target_unit": "miles",
    "tool_name": "kilometers_to_miles",
    "tool_arguments": {
      "kilometers": 10
    }
  }'
```

Expected response shape:

- `question`
- `tool_name`
- `tool_arguments`
- `mcp_server_url`
- `mcp_elapsed_ms`
- `mcp_result`
- `explanation`

## Example Request

```bash
curl -s https://your-gemini-client.onrender.com/explain \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can you explain how to convert 10 km to miles?",
    "input_value": "10",
    "input_unit": "km",
    "target_unit": "miles",
    "tool_name": "kilometers_to_miles",
    "tool_arguments": {
      "kilometers": 10
    }
  }'
```

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
