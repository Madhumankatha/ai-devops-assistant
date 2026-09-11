from collections.abc import Callable
from typing import Any

from app.schemas.tool import ToolDefinition, ToolResult


class ToolRegistry:
    """
    Central registry for all AI DevOps tools.

    The agent can only execute tools registered here.
    """

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[..., Any],
    ) -> None:
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")

        self._tools[name] = {
            "definition": ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
            ),
            "handler": handler,
        }

    def get(self, name: str) -> dict[str, Any] | None:
        return self._tools.get(name)

    def definitions(self) -> list[ToolDefinition]:
        return [
            tool["definition"]
            for tool in self._tools.values()
        ]

    def execute(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> ToolResult:

        tool = self.get(name)

        if tool is None:
            return ToolResult(
                tool_name=name,
                success=False,
                error=f"Unknown tool: {name}",
            )

        arguments = arguments or {}

        try:
            result = tool["handler"](**arguments)

            return ToolResult(
                tool_name=name,
                success=True,
                data=result,
            )

        except Exception as exc:
            return ToolResult(
                tool_name=name,
                success=False,
                error=str(exc),
            )