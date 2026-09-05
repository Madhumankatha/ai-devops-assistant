from app.agent.controller import DevOpsAgent


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def create_chat_completion(
        self,
        messages,
        temperature,
        max_tokens,
    ):
        self.calls += 1

        if self.calls == 1:
            content = """
{
  "action": "tool",
  "tool_name": "get_pod_status",
  "arguments": {
    "namespace": "production"
  }
}
"""
        else:
            content = """
{
  "action": "final",
  "summary": "Payment service has an unhealthy pod.",
  "root_cause": "The payment service pod is in CrashLoopBackOff.",
  "evidence": [
    "Pod status is CrashLoopBackOff",
    "The pod has restarted multiple times"
  ],
  "recommended_actions": [
    "Inspect application logs",
    "Check Kubernetes events"
  ],
  "confidence": 0.85
}
"""

        return {
            "choices": [
                {
                    "message": {
                        "content": content
                    }
                }
            ]
        }


def test_agent_executes_tool_and_returns_final_result():

    agent = DevOpsAgent(
        llm=FakeLLM(),
        max_iterations=3,
    )

    result = agent.investigate(
        service="payment-service",
        namespace="production",
        question="Why is payment-service failing?",
    )

    assert result["summary"]
    assert result["root_cause"]

    assert len(result["tools_used"]) == 1
    assert result["tools_used"][0]["tool_name"] == "get_pod_status"

    assert result["iterations"] == 2