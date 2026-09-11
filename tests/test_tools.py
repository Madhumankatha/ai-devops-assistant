from app.tools import create_tool_registry


def test_tool_registry_contains_kubernetes_tools():
    registry = create_tool_registry()

    tools = registry.definitions()

    names = {tool.name for tool in tools}

    assert "get_pod_status" in names
    assert "get_pod_logs" in names
    assert "get_kubernetes_events" in names
    assert "get_deployment_status" in names


def test_get_pod_status():
    registry = create_tool_registry()

    result = registry.execute(
        "get_pod_status",
        {
            "namespace": "production",
        },
    )

    assert result.success is True
    assert result.data["namespace"] == "production"
    assert len(result.data["pods"]) == 2


def test_get_pod_logs():
    registry = create_tool_registry()

    result = registry.execute(
        "get_pod_logs",
        {
            "pod_name": "payment-service-123",
            "namespace": "production",
        },
    )

    assert result.success is True
    assert result.data["pod"] == "payment-service-123"


def test_unknown_tool_is_rejected():
    registry = create_tool_registry()

    result = registry.execute(
        "delete_cluster",
        {},
    )

    assert result.success is False
    assert "Unknown tool" in result.error