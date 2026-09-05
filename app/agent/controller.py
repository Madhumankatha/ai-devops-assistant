import json
import logging
from typing import Any

from app.tools import create_tool_registry

logger = logging.getLogger(__name__)


class DevOpsAgent:
    """
    Controlled Agentic AI loop for Kubernetes investigation.

    Architecture:

        User
          ↓
        Qwen
          ↓
        Tool decision
          ↓
        Tool Registry
          ↓
        Read-only DevOps tool
          ↓
        Tool result
          ↓
        Qwen
          ↓
        Final RCA

    The model can request tools, but it cannot execute arbitrary
    Python, shell commands, or kubectl commands.
    """

    def __init__(
        self,
        llm: Any,
        max_iterations: int = 5,
    ) -> None:
        self.llm = llm
        self.registry = create_tool_registry()
        self.max_iterations = max_iterations

    # ------------------------------------------------------------------
    # Tool definitions
    # ------------------------------------------------------------------

    def _tool_definitions(self) -> list[dict[str, Any]]:
        """
        Convert registered tools into a model-friendly format.
        """

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in self.registry.definitions()
        ]

    def _tool_names(self) -> set[str]:
        """
        Return the names of tools the agent is allowed to execute.
        """

        return {
            tool.name
            for tool in self.registry.definitions()
        }

    # ------------------------------------------------------------------
    # JSON parsing
    # ------------------------------------------------------------------

    def _extract_json(self, text: str) -> dict[str, Any]:
        """
        Extract the first JSON object from the model response.

        Small local models sometimes return Markdown fences or
        additional explanatory text, so we intentionally make
        parsing tolerant.
        """

        if not text:
            raise ValueError(
                "Agent returned an empty response."
            )

        text = text.strip()

        # Remove Markdown code fences.

        if text.startswith("```"):
            lines = text.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines).strip()

            if text.lower().startswith("json"):
                text = text[4:].strip()

        # Locate JSON object.

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise ValueError(
                f"Agent returned invalid JSON: {text}"
            )

        json_text = text[start:end + 1]

        try:
            result = json.loads(json_text)

        except json.JSONDecodeError as exc:
            logger.error(
                "Invalid JSON from Qwen: %s",
                json_text,
            )

            raise ValueError(
                f"Agent returned malformed JSON: {json_text}"
            ) from exc

        if not isinstance(result, dict):
            raise ValueError(
                "Agent JSON response must be an object."
            )

        return result

    # ------------------------------------------------------------------
    # Prompt
    # ------------------------------------------------------------------

    def _system_prompt(self) -> str:
        """
        System prompt optimized for a small local model.
        """

        tools = json.dumps(
            self._tool_definitions(),
            indent=2,
        )

        return f"""
You are an AI DevOps investigation agent.

Your job is to investigate Kubernetes incidents using
read-only diagnostic tools.

AVAILABLE TOOLS:

{tools}

IMPORTANT RULES:

1. Use ONLY the tools listed above.
2. Never invent tool results.
3. Never execute shell commands.
4. Never execute kubectl commands directly.
5. Never delete resources.
6. Never restart resources.
7. Never scale resources.
8. Never modify Kubernetes resources.
9. Use evidence collected from tools.
10. If more evidence is needed, request another tool.
11. When enough evidence is available, return the final RCA.
12. Return ONLY valid JSON.
13. Do not return Markdown.
14. Do not explain your JSON outside the JSON object.

TOOL REQUEST FORMAT:

{{
  "action": "get_pod_status",
  "arguments": {{
    "namespace": "production"
  }}
}}

Another example:

{{
  "action": "get_pod_logs",
  "arguments": {{
    "pod_name": "payment-service-123",
    "namespace": "production",
    "tail_lines": 100
  }}
}}

FINAL RESPONSE FORMAT:

{{
  "action": "final",
  "summary": "Short incident summary",
  "root_cause": "Evidence-supported root cause",
  "evidence": [
    "Evidence 1",
    "Evidence 2"
  ],
  "recommended_actions": [
    "Recommended action 1",
    "Recommended action 2"
  ],
  "confidence": 0.90
}}

IMPORTANT:

The "action" field must contain either:

1. The exact name of one available tool

OR

2. "final"

Never use:

"action": "tool"

Always use the actual tool name.
"""

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    def _execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute a tool through the controlled registry.

        The registry is the security boundary.
        """

        allowed_tools = self._tool_names()

        if tool_name not in allowed_tools:
            logger.warning(
                "Blocked unauthorized tool request: %s",
                tool_name,
            )

            return {
                "tool_name": tool_name,
                "success": False,
                "data": None,
                "error": (
                    f"Tool '{tool_name}' is not allowed."
                ),
            }

        logger.info(
            "Executing tool=%s arguments=%s",
            tool_name,
            arguments,
        )

        result = self.registry.execute(
            tool_name,
            arguments,
        )

        return {
            "tool_name": result.tool_name,
            "success": result.success,
            "data": result.data,
            "error": result.error,
        }

    # ------------------------------------------------------------------
    # Investigation
    # ------------------------------------------------------------------

    def investigate(
        self,
        service: str,
        namespace: str,
        question: str,
    ) -> dict[str, Any]:
        """
        Run the Agentic DevOps investigation loop.
        """

        conversation: list[dict[str, str]] = [
            {
                "role": "system",
                "content": self._system_prompt(),
            },
            {
                "role": "user",
                "content": (
                    f"Investigate this Kubernetes incident.\n\n"
                    f"Service: {service}\n"
                    f"Namespace: {namespace}\n"
                    f"Question: {question}\n\n"
                    f"Start the investigation by selecting "
                    f"the most useful read-only tool."
                ),
            },
        ]

        executed_tools: list[dict[str, Any]] = []

        for iteration in range(1, self.max_iterations + 1):

            logger.info(
                "Agent iteration=%s service=%s namespace=%s",
                iteration,
                service,
                namespace,
            )

            # ----------------------------------------------------------
            # Ask Qwen
            # ----------------------------------------------------------

            response = self.llm.create_chat_completion(
                messages=conversation,
                temperature=0.1,
                max_tokens=700,
            )

            try:
                content = response["choices"][0]["message"]["content"]

            except (KeyError, IndexError, TypeError) as exc:
                raise RuntimeError(
                    "Unexpected response format from Qwen."
                ) from exc

            logger.debug(
                "Qwen response: %s",
                content,
            )

            # ----------------------------------------------------------
            # Parse decision
            # ----------------------------------------------------------

            decision = self._extract_json(content)

            action = decision.get("action")

            if not action:
                raise ValueError(
                    "Agent response does not contain an 'action' field."
                )

            # ----------------------------------------------------------
            # FINAL
            # ----------------------------------------------------------

            if action == "final":

                result = {
                    "summary": decision.get(
                        "summary",
                        "Investigation completed.",
                    ),
                    "root_cause": decision.get(
                        "root_cause",
                        "Insufficient evidence.",
                    ),
                    "evidence": decision.get(
                        "evidence",
                        [],
                    ),
                    "recommended_actions": decision.get(
                        "recommended_actions",
                        [],
                    ),
                    "confidence": decision.get(
                        "confidence",
                        0.0,
                    ),
                    "tools_used": executed_tools,
                    "iterations": iteration,
                }

                logger.info(
                    "Agent investigation completed | "
                    "service=%s | tools=%s | iterations=%s",
                    service,
                    len(executed_tools),
                    iteration,
                )

                return result

            # ----------------------------------------------------------
            # TOOL REQUEST
            # ----------------------------------------------------------

            allowed_tools = self._tool_names()

            # Preferred format:
            #
            # {
            #   "action": "get_pod_status",
            #   "arguments": {}
            # }

            if action in allowed_tools:

                tool_name = action

                arguments = decision.get(
                    "arguments",
                    {},
                )

                if not isinstance(arguments, dict):
                    arguments = {}

                tool_result = self._execute_tool(
                    tool_name,
                    arguments,
                )

                executed_tools.append(
                    {
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "success": tool_result["success"],
                    }
                )

                conversation.append(
                    {
                        "role": "assistant",
                        "content": content,
                    }
                )

                conversation.append(
                    {
                        "role": "user",
                        "content": (
                            "TOOL RESULT:\n"
                            + json.dumps(
                                tool_result,
                                indent=2,
                            )
                            + "\n\n"
                            "Use this evidence to continue "
                            "the investigation."
                        ),
                    }
                )

                continue

            # ----------------------------------------------------------
            # BACKWARD-COMPATIBLE FORMAT
            # ----------------------------------------------------------
            #
            # Some model responses may still produce:
            #
            # {
            #   "action": "tool",
            #   "tool_name": "get_pod_status",
            #   "arguments": {}
            # }
            #

            if action == "tool":

                tool_name = decision.get(
                    "tool_name"
                )

                arguments = decision.get(
                    "arguments",
                    {},
                )

                if not tool_name:
                    raise ValueError(
                        "Tool action did not specify tool_name."
                    )

                if not isinstance(arguments, dict):
                    arguments = {}

                tool_result = self._execute_tool(
                    tool_name,
                    arguments,
                )

                executed_tools.append(
                    {
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "success": tool_result["success"],
                    }
                )

                conversation.append(
                    {
                        "role": "assistant",
                        "content": content,
                    }
                )

                conversation.append(
                    {
                        "role": "user",
                        "content": (
                            "TOOL RESULT:\n"
                            + json.dumps(
                                tool_result,
                                indent=2,
                            )
                            + "\n\n"
                            "Use this evidence to continue "
                            "the investigation."
                        ),
                    }
                )

                continue

            # ----------------------------------------------------------
            # UNKNOWN ACTION
            # ----------------------------------------------------------

            logger.error(
                "Unknown agent action: %s",
                action,
            )

            conversation.append(
                {
                    "role": "assistant",
                    "content": content,
                }
            )

            conversation.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous response contained an "
                        "invalid action.\n\n"
                        f"Invalid action: {action}\n\n"
                        "Choose ONLY one of these actions:\n"
                        f"{sorted(allowed_tools)}\n"
                        "or:\n"
                        "final\n\n"
                        "Return ONLY valid JSON."
                    ),
                }
            )

        # --------------------------------------------------------------
        # MAX ITERATIONS
        # --------------------------------------------------------------

        logger.warning(
            "Agent reached max iterations | service=%s | "
            "iterations=%s",
            service,
            self.max_iterations,
        )

        return {
            "summary": (
                "Investigation reached the maximum number "
                "of agent iterations."
            ),
            "root_cause": (
                "Insufficient evidence to determine the "
                "root cause."
            ),
            "evidence": [],
            "recommended_actions": [
                "Review the collected Kubernetes diagnostics.",
                "Run another investigation with additional context.",
            ],
            "confidence": 0.0,
            "tools_used": executed_tools,
            "iterations": self.max_iterations,
        }