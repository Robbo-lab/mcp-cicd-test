from conftest import parse_mcp_response


def test_tools_list(mcp_client):
    response = mcp_client.rpc("tools/list", {}, id=2)

    assert response.status_code == 200
    body = parse_mcp_response(response)
    print(f"[test_tools_list] status_code={response.status_code}")
    print(f"[test_tools_list] body={body}")
    assert body["jsonrpc"] == "2.0"
    assert "result" in body
    assert "tools" in body["result"]

    tools = body["result"]["tools"]
    print(f"[test_tools_list] tools={tools}")
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert all("name" in tool for tool in tools)
    assert all("description" in tool for tool in tools)


def test_tools_call_fahrenheit_to_celsius(mcp_client):
    response = mcp_client.rpc(
        "tools/call",
        {
            "name": "fahrenheit_to_celsius_fahrenheit_to_celsius_post",
            "arguments": {"fahrenheit": 77},
        },
        id=3,
    )

    assert response.status_code == 200
    body = parse_mcp_response(response)
    print(f"[test_tools_call_fahrenheit_to_celsius] status_code={response.status_code}")
    print(f"[test_tools_call_fahrenheit_to_celsius] body={body}")
    assert "result" in body
    assert "error" not in body

    result = body["result"]
    print(f"[test_tools_call_fahrenheit_to_celsius] result={result}")
    assert isinstance(result, dict)
    assert "content" in result or "structuredContent" in result
