# Integrating Gemini with our MCP server - Converter Tools & Prompts

- User question
- Gemini agent client
- MCP request: tools/call
- Use registered MCP tool
- Get Structured MCP response
- Construct a prompt
- Get the Gemini streamed response

## 1. Environment variables

Create `.env.example` in the project root:

```bash
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
MCP_SERVER_URL=http://localhost:8003/mcp
```

Create the `.env` file:

```bash
cp .env.example .env
```

## 2. Start the Streamable HTTP server

```bash
python -m converter_streamable_http_server
```

## 3. Review the Gemini client flow

In `simulated_gemini_client.py`, the flow is:

1. Read environment variables.
2. Open an MCP client connection to `MCP_SERVER_URL`.
3. Call an existing MCP tool.
4. Receive a structured MCP result.
5. Pass that result into Gemini.
6. Stream Gemini’s explanation to the terminal.

The file simulates an orchestration call:

```python
result = await mcp_client.call_tool(
    "kilometers_to_miles",
    {"kilometers": 10},
)
```

## 4. Run the Gemini client

In a second terminal:

```bash
python -m simulated_gemini_client
```

Expected output in the terminal:

```text
User question:
Can you explain how to convert 10 km to miles?

Calling MCP tool: kilometers_to_miles
[MCP progress] 1/1: Running kilometers_to_miles MCP tool
MCP structured result (...)
...

Gemini streamed explanation:
...
```

## 5. Requests and Responses handling

### MCP request

The Gemini client sends an expected MCP request here:

```python
await mcp_client.call_tool(...)
```

### MCP response

The expected tool response is captured here:

```python
mcp_result, elapsed_ms = await call_mcp_tool(...)
```

This is structured tool output from the MCP server, not a model-generated answer.
Note the performance metrics

### Gemini call

Gemini is called only after the MCP result is available (which is passed through one of our prompts):

```python
prompt = build_gemini_prompt(...)
gemini_client = genai.Client(api_key=api_key)
```

### Gemini streaming

Gemini then streams explanation text:

```python
for chunk in stream:
    if chunk.text:
        print(chunk.text, end="")
```

This is model output chunking, not server-side calculation.

## 6. Common errors and fixes

### Error: `Missing required environment variable: GEMINI_API_KEY`

Check that `.env` exists and contains:

```bash
GEMINI_API_KEY=your_real_key_here
```

### Error: MCP server connection refused

Make sure the server is running:

```bash
python converter_streamable_http_server.py
```

### Error: Gemini authentication failed

Fix:

- Regenerate the API key if needed.
- Confirm the `.env` value has no extra spaces.
- Confirm the account/project has API access enabled.

## 7. Next step

1. Choose another MCP tool.
2. Parse a text question like `Convert 25 miles to km`.
3. Compare tool-backed answers with direct Gemini-only answers.
4. Update the prompt or change prompts to see how the response might change
