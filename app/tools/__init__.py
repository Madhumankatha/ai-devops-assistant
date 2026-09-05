from .kubernetes import (
    get_deployment_status,
    get_kubernetes_events,
    get_pod_logs,
    get_pod_status,
)
from .registry import ToolRegistry


def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        name="get_pod_status",
        description=(
            "Get the current status of Kubernetes pods "
            "in a namespace."
        ),
        parameters={
            "type": "object",
            "properties": {
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace",
                }
            },
        },
        handler=get_pod_status,
    )

    registry.register(
        name="get_pod_logs",
        description="Retrieve recent logs from a Kubernetes pod.",
        parameters={
            "type": "object",
            "properties": {
                "pod_name": {
                    "type": "string",
                },
                "namespace": {
                    "type": "string",
                },
                "tail_lines": {
                    "type": "integer",
                },
            },
            "required": ["pod_name"],
        },
        handler=get_pod_logs,
    )

    registry.register(
        name="get_kubernetes_events",
        description="Get recent Kubernetes events.",
        parameters={
            "type": "object",
            "properties": {
                "namespace": {
                    "type": "string",
                }
            },
        },
        handler=get_kubernetes_events,
    )

    registry.register(
        name="get_deployment_status",
        description="Get the status of a Kubernetes deployment.",
        parameters={
            "type": "object",
            "properties": {
                "deployment_name": {
                    "type": "string",
                },
                "namespace": {
                    "type": "string",
                },
            },
            "required": ["deployment_name"],
        },
        handler=get_deployment_status,
    )

    return registry