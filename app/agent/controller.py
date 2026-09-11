import json
import logging
from typing import Any

from app.rag import RunbookRetriever
from app.tools import create_tool_registry

logger = logging.getLogger(__name__)


class DevOpsAgent:
    """Controlled Agentic AI loop for Kubernetes investigation."""

    def __init__(self, llm: Any, max_iterations: int = 5) -> None:
        self.llm = llm
        self.registry = create_tool_registry()
        self.retriever = RunbookRetriever()
        self.max_iterations = max_iterations

    def _tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self.registry.definitions()
        ]

    def _tool_names(self) -> set[str]:
        return {tool.name for tool in self.registry.definitions()}

    def _extract_json(self, text: str) -> dict[str, Any]:
        if not isinstance(text, str):
            raise ValueError(f"Agent returned an unexpected response type: {type(text).__name__}")
        text = text.strip()
        if not text:
            raise ValueError("Agent returned an empty response.")
        if text.startswith("```"):
            lines = text.splitlines()[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError(f"Agent returned invalid JSON: {text}")
        try:
            result = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON from Qwen: %s", text)
            raise ValueError("Agent returned malformed JSON.") from exc
        if not isinstance(result, dict):
            raise ValueError("Agent JSON response must be an object.")
        return result

    def _system_prompt(self) -> str:
        tools = json.dumps(self._tool_definitions(), indent=2)
        return f'''You are an AI DevOps investigation agent.

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
9. If the question asks for metrics/telemetry correlation, make sure service metrics, error rate, and latency are collected before finalizing.
10. Return ONLY valid JSON.

TOOL FORMAT:
{{"action":"get_pod_status","arguments":{{"namespace":"production"}}}}

FINAL FORMAT:
{{"action":"final","summary":"Short incident summary","root_cause":"Evidence-supported root cause","evidence":["Evidence 1"],"recommended_actions":["Action 1"],"confidence":0.90}}

The action field must be an exact tool name or "final".'''

    def _execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name not in self._tool_names():
            return {"tool_name": tool_name, "success": False, "data": None, "error": f"Tool '{tool_name}' is not allowed."}
        logger.info("Executing tool=%s arguments=%s", tool_name, arguments)
        result = self.registry.execute(tool_name, arguments)
        return {"tool_name": result.tool_name, "success": result.success, "data": result.data, "error": result.error}

    def _should_collect_telemetry(self, question: str) -> bool:
        normalized = question.lower()
        return any(term in normalized for term in ("metric", "metrics", "telemetry", "error rate", "latency", "cpu", "memory", "prometheus", "correlate", "correlation"))

    def _collect_required_telemetry(self, service: str, namespace: str, executed_tools: list[dict[str, Any]], collected_evidence: list[dict[str, Any]]) -> None:
        required = (
            ("get_service_metrics", {"service": service, "namespace": namespace}),
            ("get_error_rate", {"service": service, "namespace": namespace}),
            ("get_latency", {"service": service, "namespace": namespace}),
        )
        already_executed = {item["tool_name"] for item in executed_tools}
        for tool_name, arguments in required:
            if tool_name in already_executed:
                continue
            logger.info("Collecting required telemetry tool=%s service=%s namespace=%s", tool_name, service, namespace)
            tool_result = self._execute_tool(tool_name, arguments)
            executed_tools.append({"tool_name": tool_name, "arguments": arguments, "success": tool_result["success"]})
            collected_evidence.append(tool_result)

    def _generate_text(self, prompt: str) -> str:
        response = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "Return only the requested JSON object."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=700,
        )
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Unexpected response format from Qwen during RCA synthesis.") from exc
        if not isinstance(content, str):
            raise RuntimeError(f"Qwen RCA synthesis returned non-text content: {type(content).__name__}")
        return content

    def _normalize_evidence(self, evidence: Any) -> list[str]:
        if not isinstance(evidence, list):
            return []
        normalized: list[str] = []
        for item in evidence:
            if isinstance(item, str):
                normalized.append(item)
            elif isinstance(item, dict):
                detail = item.get("detail") or item.get("description") or item.get("message")
                source = item.get("source") or item.get("tool") or item.get("tool_name")
                if detail is not None:
                    normalized.append(f"[{source}] {detail}" if source else str(detail))
                else:
                    normalized.append(json.dumps(item, default=str))
            else:
                normalized.append(str(item))
        return normalized

    def _normalize_actions(self, actions: Any) -> list[str]:
        if not isinstance(actions, list):
            return []
        return [item if isinstance(item, str) else str(item) for item in actions]

    def _retrieve_runbooks(self, service: str, question: str, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        evidence_text = json.dumps(evidence, default=str)
        query = f"{service} {question} {evidence_text}"
        matches = self.retriever.search(query, top_k=3)
        return [
            {
                "id": match.runbook_id,
                "title": match.title,
                "score": match.score,
                "content": match.content,
            }
            for match in matches
        ]

    def _synthesize_final_analysis(self, service: str, namespace: str, question: str, evidence: list[dict[str, Any]], tools_used: list[dict[str, Any]], iterations: int) -> dict[str, Any]:
        evidence_text = json.dumps(evidence, indent=2, default=str)
        runbooks = self._retrieve_runbooks(service, question, evidence)
        runbook_text = json.dumps(runbooks, indent=2, default=str)
        prompt = f'''You are a senior Site Reliability Engineer performing a production incident investigation.

Service: {service}
Namespace: {namespace}
Question: {question}

TRUSTED DIAGNOSTIC EVIDENCE:
{evidence_text}

RELEVANT LOCAL RUNBOOKS:
{runbook_text}

Use the runbooks as troubleshooting guidance, not as proof of facts. Produce the final incident RCA using ONLY the diagnostic evidence for factual claims. Correlate Kubernetes state, logs, events, CPU, memory, error rate, request rate, and latency. Use relevant runbook guidance to improve recommended actions. Never invent facts. Return ONLY valid JSON.

{{"summary":"short incident summary","root_cause":"strongest supported root cause","evidence":[{{"type":"observation","source":"tool name","detail":"fact supported by tool output"}}],"recommended_actions":["Action 1"],"confidence":0.0}}'''
        response = self._generate_text(prompt)
        return self._parse_final_analysis(response, tools_used, iterations, runbooks)

    def _parse_final_analysis(self, response: str, tools_used: list[dict[str, Any]], iterations: int, runbooks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        try:
            analysis = self._extract_json(response)
        except ValueError:
            logger.exception("Failed to parse final RCA response")
            return {
                "summary": "Diagnostic evidence was collected, but the final RCA could not be parsed.",
                "root_cause": "Unable to parse the final RCA response.",
                "evidence": [],
                "recommended_actions": ["Review the collected diagnostic evidence.", "Retry the investigation."],
                "confidence": 0.0,
                "tools_used": tools_used,
                "iterations": iterations,
                "runbooks": runbooks or [],
            }
        analysis["summary"] = str(analysis.get("summary", "Incident investigation completed."))
        analysis["root_cause"] = str(analysis.get("root_cause", "Insufficient evidence to determine root cause."))
        analysis["evidence"] = self._normalize_evidence(analysis.get("evidence", []))
        analysis["recommended_actions"] = self._normalize_actions(analysis.get("recommended_actions", []))
        try:
            analysis["confidence"] = float(analysis.get("confidence", 0.0))
        except (TypeError, ValueError):
            analysis["confidence"] = 0.0
        analysis["confidence"] = max(0.0, min(1.0, analysis["confidence"]))
        analysis["tools_used"] = tools_used
        analysis["iterations"] = iterations
        analysis["runbooks"] = runbooks or []
        return analysis

    def investigate(self, service: str, namespace: str, question: str) -> dict[str, Any]:
        conversation = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": f"Investigate this Kubernetes incident.\n\nService: {service}\nNamespace: {namespace}\nQuestion: {question}\n\nStart with the most useful read-only diagnostic tool."},
        ]
        executed_tools: list[dict[str, Any]] = []
        collected_evidence: list[dict[str, Any]] = []
        telemetry_required = self._should_collect_telemetry(question)

        for iteration in range(1, self.max_iterations + 1):
            logger.info("Agent iteration=%s service=%s namespace=%s", iteration, service, namespace)
            response = self.llm.create_chat_completion(messages=conversation, temperature=0.1, max_tokens=700)
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
                    self._collect_required_telemetry(service, namespace, executed_tools, collected_evidence)
                    return self._synthesize_final_analysis(service, namespace, question, collected_evidence, executed_tools, iteration)
                runbooks = self._retrieve_runbooks(service, question, collected_evidence)
                return self._parse_final_analysis(json.dumps(decision), executed_tools, iteration, runbooks)

            tool_name = decision.get("tool_name") if action == "tool" else action
            if not tool_name:
                raise ValueError("Tool action did not specify a tool name.")
            if tool_name not in self._tool_names():
                conversation.append({"role": "assistant", "content": content})
                conversation.append({"role": "user", "content": f"Invalid action. Choose only these exact tool names or final: {sorted(self._tool_names())}"})
                continue
            arguments = decision.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {}
            tool_result = self._execute_tool(tool_name, arguments)
            executed_tools.append({"tool_name": tool_name, "arguments": arguments, "success": tool_result["success"]})
            collected_evidence.append(tool_result)
            conversation.append({"role": "assistant", "content": content})
            conversation.append({"role": "user", "content": "TOOL RESULT:\n" + json.dumps(tool_result, indent=2, default=str) + "\n\nUse this evidence to continue the investigation. Select another useful tool or return action=final."})

        logger.warning("Agent reached max iterations; synthesizing collected evidence | service=%s", service)
        if telemetry_required:
            self._collect_required_telemetry(service, namespace, executed_tools, collected_evidence)
        return self._synthesize_final_analysis(service, namespace, question, collected_evidence, executed_tools, self.max_iterations)
