from dataclasses import dataclass, field
from typing import Any


@dataclass
class InvestigationState:
    """
    Structured state for an AI DevOps investigation.

    The LLM is not the source of truth. Tool results are stored
    here and supplied back to the model for reasoning.
    """

    service: str
    namespace: str
    question: str

    evidence: list[dict[str, Any]] = field(
        default_factory=list
    )

    tools_used: list[dict[str, Any]] = field(
        default_factory=list
    )

    investigated_pods: set[str] = field(
        default_factory=set
    )

    completed_tools: set[str] = field(
        default_factory=set
    )

    iteration: int = 0

    def add_tool_result(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """
        Store a tool execution and its result.
        """

        self.tools_used.append(
            {
                "tool_name": tool_name,
                "arguments": arguments,
                "success": result.get(
                    "success",
                    False,
                ),
            }
        )

        self.evidence.append(
            {
                "tool_name": tool_name,
                "arguments": arguments,
                "result": result,
            }
        )

        self.completed_tools.add(tool_name)

    def add_pod(
        self,
        pod_name: str,
    ) -> None:
        self.investigated_pods.add(
            pod_name
        )

    def evidence_summary(self) -> str:
        """
        Return structured evidence for LLM reasoning.
        """

        if not self.evidence:
            return "No evidence collected yet."

        sections: list[str] = []

        for index, item in enumerate(
            self.evidence,
            start=1,
        ):
            sections.append(
                (
                    f"Evidence #{index}\n"
                    f"Tool: {item['tool_name']}\n"
                    f"Arguments: "
                    f"{item['arguments']}\n"
                    f"Result: "
                    f"{item['result']}"
                )
            )

        return "\n\n".join(sections)

    def tools_summary(self) -> str:
        """
        Return a concise list of tools already executed.
        """

        if not self.tools_used:
            return "No tools executed."

        return "\n".join(
            [
                (
                    f"- {item['tool_name']} "
                    f"(success={item['success']})"
                )
                for item in self.tools_used
            ]
        )

    def metric_evidence(self) -> list[dict[str, Any]]:
        """
        Return only Prometheus-related evidence.
        """

        prometheus_tools = {
            "get_service_metrics",
            "get_error_rate",
            "get_latency",
        }

        return [
            item
            for item in self.evidence
            if item["tool_name"]
            in prometheus_tools
        ]

    def kubernetes_evidence(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return Kubernetes-related evidence.
        """

        kubernetes_tools = {
            "get_deployment_status",
            "get_pod_status",
            "get_pod_logs",
            "get_kubernetes_events",
        }

        return [
            item
            for item in self.evidence
            if item["tool_name"]
            in kubernetes_tools
        ]

    def build_correlation_context(self) -> str:
        """
        Build a compact correlation context for the final
        reasoning stage.
        """

        return (
            "=== KUBERNETES EVIDENCE ===\n"
            f"{self._format_items(self.kubernetes_evidence())}\n\n"
            "=== PROMETHEUS EVIDENCE ===\n"
            f"{self._format_items(self.metric_evidence())}\n"
        )

    @staticmethod
    def _format_items(
        items: list[dict[str, Any]],
    ) -> str:

        if not items:
            return "No evidence available."

        return "\n\n".join(
            [
                (
                    f"Tool: {item['tool_name']}\n"
                    f"Result: {item['result']}"
                )
                for item in items
            ]
        )
