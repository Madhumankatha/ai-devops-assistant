from typing import Any


class InvestigationPolicy:
    """
    Deterministic safety and investigation policy.

    Qwen decides what evidence it wants, but this policy
    limits the available investigation scope.
    """

    DEFAULT_SEQUENCE = [
        "get_deployment_status",
        "get_pod_status",
        "get_pod_logs",
        "get_kubernetes_events",
        "get_service_metrics",
        "get_error_rate",
        "get_latency",
    ]

    METRIC_TOOLS = {
        "get_service_metrics",
        "get_error_rate",
        "get_latency",
    }

    KUBERNETES_TOOLS = {
        "get_deployment_status",
        "get_pod_status",
        "get_pod_logs",
        "get_kubernetes_events",
    }

    def __init__(
        self,
        max_tool_calls: int = 7,
    ) -> None:
        self.max_tool_calls = max_tool_calls

    def should_continue(
        self,
        tools_used: list[dict[str, Any]],
    ) -> bool:
        return (
            len(tools_used)
            < self.max_tool_calls
        )

    def already_called(
        self,
        tool_name: str,
        tools_used: list[dict[str, Any]],
    ) -> bool:
        return any(
            item["tool_name"] == tool_name
            for item in tools_used
        )

    def allowed_next_tools(
        self,
        tools_used: list[dict[str, Any]],
    ) -> list[str]:

        used = {
            item["tool_name"]
            for item in tools_used
        }

        return [
            tool
            for tool in self.DEFAULT_SEQUENCE
            if tool not in used
        ]

    def has_kubernetes_evidence(
        self,
        tools_used: list[dict[str, Any]],
    ) -> bool:

        return any(
            item["tool_name"]
            in self.KUBERNETES_TOOLS
            for item in tools_used
        )

    def has_metric_evidence(
        self,
        tools_used: list[dict[str, Any]],
    ) -> bool:

        return any(
            item["tool_name"]
            in self.METRIC_TOOLS
            for item in tools_used
        )

    def should_collect_metrics(
        self,
        tools_used: list[dict[str, Any]],
    ) -> bool:
        """
        Metrics become useful after at least one Kubernetes
        diagnostic has been collected.
        """

        return (
            self.has_kubernetes_evidence(
                tools_used
            )
            and not self.has_metric_evidence(
                tools_used
            )
        )
