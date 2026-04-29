from conftest import parse_mcp_response


def test_resources_list(mcp_client):
    response = mcp_client.rpc("resources/list", {}, id=20)
    assert response.status_code == 200

    body = parse_mcp_response(response)
    resources = body["result"]["resources"]
    print(f"[test_resources_list] status_code={response.status_code}")
    print(f"[test_resources_list] body={body}")
    print(f"[test_resources_list] resources={resources}")
    uris = {resource["uri"] for resource in resources}
    assert any("unit_reference" in uri for uri in uris)


def test_resource_unit_reference(mcp_client):
    list_response = mcp_client.rpc("resources/list", {}, id=21)
    list_body = parse_mcp_response(list_response)
    resources = list_body["result"]["resources"]
    print(f"[test_resource_unit_reference] list_status_code={list_response.status_code}")
    print(f"[test_resource_unit_reference] list_body={list_body}")
    print(f"[test_resource_unit_reference] resources={resources}")
    uri = next(r["uri"] for r in resources if "unit_reference" in r["uri"])
    print(f"[test_resource_unit_reference] selected_uri={uri}")

    read_response = mcp_client.rpc(
        "resources/read",
        {"uri": uri},
        id=22,
    )

    assert read_response.status_code == 200
    read_body = parse_mcp_response(read_response)
    result = read_body["result"]
    print(f"[test_resource_unit_reference] read_status_code={read_response.status_code}")
    print(f"[test_resource_unit_reference] read_body={read_body}")
    print(f"[test_resource_unit_reference] result={result}")
    assert "contents" in result
    assert len(result["contents"]) >= 1
