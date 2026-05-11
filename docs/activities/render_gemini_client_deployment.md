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

## Required Environment Variables

Set these in Render for the Gemini client service:

```text
GEMINI_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-2.5-flash
MCP_SERVER_URL=https://mcp-cicd-test.onrender.com/mcp/
```

## Local Run

Install Gemini client dependencies:

```bash
python -m pip install -r gemini_client/requirements.txt
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

## Render Settings

Create a separate Render `Web Service` for the Gemini client.

Use:

Build Command:

```bash
pip install -r gemini_client/requirements.txt
```

Start Command:

```bash
uvicorn gemini_client.simulated_gemini_http_server:app --host 0.0.0.0 --port $PORT
```

Health Check Path:

```text
/health
```

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
