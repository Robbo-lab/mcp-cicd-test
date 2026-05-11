# Testing MCP Tools with curl on Render

### Converter Tools, Prompts, and Resources

Use these commands against the deployed Render service:

```text
https://mcp-cicd-test.onrender.com
```

The MCP endpoint for this deployment is:

```text
https://mcp-cicd-test.onrender.com/mcp/
```

The MCP endpoints do **not** require authentication.

---

## URL structure

- MCP JSON-RPC endpoint
  - `POST https://mcp-cicd-test.onrender.com/mcp/`
- Health check
  - `GET https://mcp-cicd-test.onrender.com/health`
- FastAPI docs
  - `GET https://mcp-cicd-test.onrender.com/docs`

---

## curl flag cheat sheet

- `-s` Silent mode
- `-D -` Print response headers
- `-o /dev/null` Discard response body
- `-v` Verbose output
- `-L` Follow redirects

---

## Optional environment helpers

```bash
BASE="https://mcp-cicd-test.onrender.com"
MCP="$BASE/mcp/"
ACCEPT="Accept: application/json, text/event-stream"
PROTO="MCP-Protocol-Version: 2025-06-18"
```

---

## 0. Quick service checks

### Root endpoint

```bash
curl -s "$BASE/"
```

### Health endpoint

```bash
curl -s "$BASE/health"
```

### FastAPI docs

```bash
curl -I "$BASE/docs"
```

---

## 1. Quick connectivity and MCP session capture

Run this first:

```bash
SESSION=$(curl -sD - -o /dev/null "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -d '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}' \
  | awk 'BEGIN{IGNORECASE=1} /^mcp-session-id:/ {sub(/\r$/,""); print $2}')
echo "SESSION=$SESSION"
```

If `SESSION` is empty:

- rerun without `-s`
- add `-v`
- confirm the service is awake if Render spun it down while idle

---

## 2. MCP handshake

```bash
curl -s "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{"roots":{"listChanged":true}},"clientInfo":{"name":"curl","version":"1.0"}}}'
```

---

## 3. List available tools

```bash
curl -s "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

Expected tools include entries similar to:

- `celsius_to_fahrenheit_celsius_to_fahrenheit_post`
- `fahrenheit_to_celsius_fahrenheit_to_celsius_post`
- `kilometers_to_miles_kilometers_to_miles_post`
- `miles_to_kilometers_miles_to_kilometers_post`
- `kilometers_to_miles`

---

## 4. Happy path tool call

```bash
curl -s "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"fahrenheit_to_celsius_fahrenheit_to_celsius_post","arguments":{"fahrenheit":77}}}'
```

Use this as the first functional MCP test.

---

## 5. Another valid tool call

```bash
curl -s "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"kilometers_to_miles_kilometers_to_miles_post","arguments":{"kilometers":10}}}'
```

---

## 6. Protocol error with unknown tool name

```bash
curl -s "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"rankine_to_celsius","arguments":{"value":100}}}'
```

This should fail at the MCP protocol layer because the tool does not exist.

---

## 7. Schema error with wrong argument name

```bash
curl -s "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"kilometers_to_miles_kilometers_to_miles_post","arguments":{"distance":10}}}'
```

This should fail because `distance` is not a valid parameter for that tool.

---

## 8. Prompt example

```bash
curl -s "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":11,"method":"prompts/get","params":{"name":"explain_conversion","arguments":{"input_value":"10","input_unit":"kilometers","target_unit":"miles"}}}'
```

---

## 9. List resources

```bash
curl -s "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":12,"method":"resources/list","params":{}}'
```

---

## 10. Read a known resource

```bash
curl -s "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":13,"method":"resources/read","params":{"uri":"resource://converter/unit_reference"}}'
```

---

## 11. Initialized notification

After initialization, you can send the client notification:

```bash
curl -s "$MCP" \
  -H "Content-Type: application/json" \
  -H "$ACCEPT" \
  -H "$PROTO" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

Expected result:

- status code `200`, `202`, or `204`

---

## 12. Notes for Render-hosted testing

- free Render services can spin down after idle time
- the first request may be slower because the service needs to wake up
- if session creation fails on the first attempt, retry once after the service responds to `/health`

---

## 13. Suggested test order

1. Check `/health`
2. Capture `SESSION`
3. Run `tools/list`
4. Run one valid `tools/call`
5. Run `prompts/get`
6. Run `resources/list`
7. Run `resources/read`
