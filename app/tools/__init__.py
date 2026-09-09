from app.tools.kubernetes import (
    get_deployment_status,
    get_kubernetes_events,
    get_pod_logs,
    get_pod_status,
)
from app.tools.prometheus import (
    get_error_rate,
    get_latency,
    get_service_metrics,
)
from app.tools.registry import ToolRegistry


def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    # ============================================================
    # Kubernetes tools
    # ============================================================

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
                    "description": "Kubernetes namespace.",
                }
            },
            "required": ["namespace"],
        },
        handler=get_pod_status,
    )

    registry.register(
        name="get_pod_logs",
        description=(
            "Retrieve recent logs from a Kubernetes pod."
        ),
        parameters={
            "type": "object",
            "properties": {
                "pod_name": {
                    "type": "string",
                    "description": "Kubernetes pod name.",
                },
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace.",
                },
                "tail_lines": {
                    "type": "integer",
                    "description": "Number of recent log lines.",
                },
            },
            "required": ["pod_name"],
        },
        handler=get_pod_logs,
    )

    registry.register(
        name="get_kubernetes_events",
        description=(
            "Get recent Kubernetes events for a namespace."
        ),
        parameters={
            "type": "object",
            "properties": {
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace.",
                }
            },
            "required": ["namespace"],
        },
        handler=get_kubernetes_events,
    )

    registry.register(
        name="get_deployment_status",
        description=(
            "Get the status of a Kubernetes deployment."
        ),
        parameters={
            "type": "object",
            "properties": {
                "deployment_name": {
                    "type": "string",
                    "description": "Kubernetes deployment name.",
                },
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace.",
                },
            },
            "required": ["deployment_name"],
        },
        handler=get_deployment_status,
    )

    # ============================================================
    # Prometheus tools
    # ============================================================

    registry.register(
        name="get_service_metrics",
        description=(
            "Get service-level metrics including CPU usage, "
            "memory usage, request rate, error rate, and "
            "p95 latency."
        ),
        parameters={
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Service name.",
                },
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace.",
                },
            },
            "required": ["service", "namespace"],
        },
        handler=get_service_metrics,
    )

    registry.register(
        name="get_error_rate",
        description=(
            "Get the current error rate percentage "
            "for a service."
        ),
        parameters={
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Service name.",
                },
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace.",
                },
            },
            "required": ["service", "namespace"],
        },
        handler=get_error_rate,
    )

    registry.register(
        name="get_latency",
        description=(
            "Get the p95 request latency for a service."
        ),
        parameters={
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Service name.",
                },
                "namespace": {
                    "type": "string",
                    "description": "Kubernetes namespace.",
                },
            },
            "required": ["service", "namespace"],
        },
        handler=get_latency,
    )

    return registry
