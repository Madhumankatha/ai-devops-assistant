import json
import logging
from typing import Any

from app.tools import create_tool_registry

logger = logging.getLogger(__name__)


class DevOpsAgent:
    """
    Controlled Agentic AI loop for Kubernetes investigation.

    The model selects only read-only tools registered in ToolRegistry.
    Collected tool results are preserved and are always synthesized into
    a final RCA, including when the agent reaches max_iterations.
    """

    def __init__(self, llm: Any, max_iterations: int = 5) -> None:
        self.llm = llm
        self.registry = create_tool_registry()
        self.max_iterations = max_iterations

    def _tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in self.registry.definitions()
        ]

    def _tool_names(self) -> set[str]:
        return {tool.name for tool in self.registry.definitions()}

    def _extract_json(self, text: str) -> dict[str, Any]:
        if not text:
            raise ValueError("Agent returned an empty response.")

        text = text.strip()

        if text.startswith("```"):
            lines = text.splitlines()[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"Agent returned invalid JSON: {text}")

        try:
            result = json.loads(text[start:end + 1])
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON from Qwen: %s", text)
            raise ValueError("Agent returned malformed JSON.") from exc

        if not isinstance(result, dict):
            raise ValueError("Agent JSON response must be an object.")

        return result

    def _system_prompt(self) -> str:
        tools = json.dumps(self._tool_definitions(), indent=2)
        return f"""
You are an AI DevOps investigation agent.

Investigate Kubernetes incidents using ONLY read-only diagnostic tools.

AVAILABLE TOOLS:
{tools}

RULES:
1. Use only the available tools.
2. Never invent tool results.
3. Never execute shell or kubectl commands.
4. Never modify, restart, delete, or scale resources.
5. Use collected evidence when deciding what to investigate next.
6. Correlate Kubernetes state, logs, events, and service metrics.
7. Distinguish observations from inferences and hypotheses.
8. When evidence is sufficient, return action=final.
9. If the question asks for metrics/telemetry correlation, make sure
   service metrics, error rate, and latency are collected before finalizing.
10. If you cannot finish before the iteration limit, the system will
   synthesize the collected evidence separately.
11. Return ONLY valid JSON.

TOOL FORMAT:
{{
  "action": "get_pod_status",
  "arguments": {{"namespace": "production"}}
}}

FINAL FORMAT:
{{
  "action": "final",
  "summary": "Short incident summary",
  "root_cause": "Evidence-supported root cause",
  "evidence": ["Evidence 1", "Evidence 2"],
  "recommended_actions": ["Action 1", "Action 2"],
  "confidence": 0.90
}}

The action field must be an exact tool name or "final".
"""

    def _execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name not in self._tool_names():
            logger.warning("Blocked unauthorized tool request: %s", tool_name)
            return {
                "tool_name": tool_name,
                "success": False,
                "data": None,
                "error": f"Tool '{tool_name}' is not allowed.",
            }

        logger.info("Executing tool=%s arguments=%s", tool_name, arguments)
        result = self.registry.execute(tool_name, arguments)
        return {
            "tool_name": result.tool_name,
            "success": result.success,
            "data": result.data,
            "error": result.error,
        }

    def _should_collect_telemetry(self, question: str) -> bool:
        """Return True when the incident request explicitly needs telemetry correlation."""
        normalized = question.lower()
        telemetry_terms = (
            "metric",
            "metrics",
            "telemetry",
            "error rate",
            "latency",
            "cpu",
            "memory",
            "prometheus",
            "correlate",
            "correlation",
        )
        return any(term in normalized for term in telemetry_terms)

    def _collect_required_telemetry(
        self,
        service: str,
        namespace: str,
        executed_tools: list[dict[str, Any]],
        collected_evidence: list[dict[str, Any]],
    ) -> None:
        """Ensure telemetry coverage for questions that explicitly request correlation."""
        required = (
            ("get_service_metrics", {"service": service, "namespace": namespace}),
            ("get_error_rate", {"service": service, "namespace": namespace}),
            ("get_latency", {"service": service, "namespace": namespace}),
        )

        already_executed = {item["tool_name"] for item in executed_tools}

        for tool_name, arguments in required:
            if tool_name in already_executed:
                continue

            logger.info(
                "Collecting required telemetry tool=%s service=%s namespace=%s",
                tool_name,
                service,
                namespace,
            )
            tool_result = self._execute_tool(tool_name, arguments)

            executed_tools.append({
                "tool_name": tool_name,
                "arguments": arguments,
                "success": tool_result["success"],
            })
            collected_evidence.append(tool_result)

    def _synthesize_final_analysis(
        self,
        service: str,
        namespace: str,
        question: str,
        evidence: list[dict[str, Any]],
        tools_used: list[dict[str, Any]],
        iterations: int,
    ) -> dict[str, Any]:
        """Synthesize all collected evidence into the final RCA."""

        evidence_text = json.dumps(evidence, indent=2, default=str)

        prompt = f"""
You are a senior Site Reliability Engineer performing a production incident investigation.

Service: {service}
Namespace: {namespace}
Question: {question}

TRUSTED DIAGNOSTIC EVIDENCE:
{evidence_text}

Produce the final incident RCA using ONLY this evidence.

RULES:
- Observation = directly returned by a diagnostic tool.
- Inference = conclusion supported by multiple observations.
- Hypothesis = plausible but unconfirmed explanation.
- Identify the strongest supported root cause.
- Do not treat high CPU or memory as root cause without supporting evidence.
- Correlate Kubernetes state, logs, events, CPU, memory, error rate, request rate, and latency.
- Never invent facts, logs, metrics, pods, events, or resources.
- If evidence is insufficient, explicitly say so.

Return ONLY valid JSON with this exact structure:
{{
  "summary": "short incident summary",
  "root_cause": "strongest supported root cause",
  "impact": "service/customer impact",
  "evidence": [
    {{
      "type": "observation",
      "source": "tool name",
      "detail": "fact supported by tool output"
    }}
  ],
  "contributing_factors": [],
  "hypotheses": [],
  "recommended_actions": [],
  "confidence": 0.0
}}
"""

        response = self.llm.generate(prompt)
        return self._parse_final_analysis(
            response=response,
            tools_used=tools_used,
            iterations=iterations,
        )

    def _parse_final_analysis(
        self,
        response: str,
        tools_used: list[dict[str, Any]],
        iterations: int,
    ) -> dict[str, Any]:
        try:
            analysis = self._extract_json(response)
        except ValueError:
            logger.exception("Failed to parse final RCA response")
            return {
                "summary": "Diagnostic evidence was collected, but the final RCA could not be parsed.",
                "root_cause": "Unable to parse the final RCA response.",
                "impact": "Unknown.",
                "evidence": [],
                "contributing_factors": [],
                "hypotheses": [],
                "recommended_actions": [
                    "Review the collected diagnostic evidence.",
                    "Retry the investigation.",
                ],
                "confidence": 0.0,
                "tools_used": tools_used,
                "iterations": iterations,
            }

        analysis.setdefault("summary", "Incident investigation completed.")
        analysis.setdefault("root_cause", "Insufficient evidence to determine root cause.")
        analysis.setdefault("impact", "Unknown.")
        analysis.setdefault("evidence", [])
        analysis.setdefault("contributing_factors", [])
        analysis.setdefault("hypotheses", [])
        analysis.setdefault("recommended_actions", [])
        analysis.setdefault("confidence", 0.0)
        analysis["tools_used"] = tools_used
        analysis["iterations"] = iterations
        return analysis

    def investigate(self, service: str, namespace: str, question: str) -> dict[str, Any]:
        conversation: list[dict[str, str]] = [
            {"role": "system", "content": self._system_prompt()},
            {
                "role": "user",
                "content": (
                    "Investigate this Kubernetes incident.\n\n"
                    f"Service: {service}\n"
                    f"Namespace: {namespace}\n"
                    f"Question: {question}\n\n"
                    "Start with the most useful read-only diagnostic tool."
                ),
            },
        ]

        executed_tools: list[dict[str, Any]] = []
        collected_evidence: list[dict[str, Any]] = []
        telemetry_required = self._should_collect_telemetry(question)

        for iteration in range(1, self.max_iterations + 1):
            logger.info(
                "Agent iteration=%s service=%s namespace=%s",
                iteration,
                service,
                namespace,
            )

            response = self.llm.create_chat_completion(
                messages=conversation,
                temperature=0.1,
                max_tokens=700,
            )

            try:
                content = response["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as exc:
                raise RuntimeError("Unexpected response format from Qwen.") from exc

            decision = self._extract_json(content)
            action = decision.get("action")

            if not action:
                raise ValueError("Agent response does not contain an 'action' field.")

            if action == "final":
                if telemetry_required:
                    self._collect_required_telemetry(
                        service=service,
                        namespace=namespace,
                        executed_tools=executed_tools,
                        collected_evidence=collected_evidence,
                    )
                    return self._synthesize_final_analysis(
                        service=service,
                        namespace=namespace,
                        question=question,
                        evidence=collected_evidence,
                        tools_used=executed_tools,
                        iterations=iteration,
                    )

                return self._parse_final_analysis(
                    response=json.dumps(decision),
                    tools_used=executed_tools,
                    iterations=iteration,
                )

            allowed_tools = self._tool_names()
            tool_name = action

            if action == "tool":
                tool_name = decision.get("tool_name")

            if not tool_name:
                raise ValueError("Tool action did not specify a tool name.")

            if tool_name not in allowed_tools:
                logger.warning("Unknown agent action: %s", tool_name)
                conversation.append({"role": "assistant", "content": content})
                conversation.append({
                    "role": "user",
                    "content": (
                        "Invalid action. Choose only one of these exact tool names "
                        f"or final: {sorted(allowed_tools)}"
                    ),
                })
                continue

            arguments = decision.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {}

            tool_result = self._execute_tool(tool_name, arguments)

            executed_tools.append({
                "tool_name": tool_name,
                "arguments": arguments,
                "success": tool_result["success"],
            })

            collected_evidence.append(tool_result)

            conversation.append({"role": "assistant", "content": content})
            conversation.append({
                "role": "user",
                "content": (
                    "TOOL RESULT:\n"
                    + json.dumps(tool_result, indent=2, default=str)
                    + "\n\n"
                    "Use this evidence to continue the investigation. "
                    "Select another useful tool or return action=final."
                ),
            })

        # Critical fix: never discard evidence when max_iterations is reached.
        logger.warning(
            "Agent reached max iterations; synthesizing collected evidence | service=%s",
            service,
        )

        if telemetry_required:
            self._collect_required_telemetry(
                service=service,
                namespace=namespace,
                executed_tools=executed_tools,
                collected_evidence=collected_evidence,
            )

        return self._synthesize_final_analysis(
            service=service,
            namespace=namespace,
            question=question,
            evidence=collected_evidence,
            tools_used=executed_tools,
            iterations=self.max_iterations,
        )
