from unittest.mock import Mock

from app.agent.controller import DevOpsAgent


def test_final_analysis_includes_relevant_runbooks() -> None:
    llm = Mock()
    agent = DevOpsAgent(llm=llm)

    evidence = [
        {
            "tool_name": "get_pod_logs",
            "success": True,
            "data": "ERROR database connection timeout after 30 seconds",
            "error": None,
        },
        {
            "tool_name": "get_pod_status",
            "success": True,
            "data": "CrashLoopBackOff",
            "error": None,
        },
    ]

    llm.create_chat_completion.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"summary":"DB failure","root_cause":"Database connection failure","evidence":["timeout"],"recommended_actions":["Check DB"],"confidence":0.95}'
                }
            }
        ]
    }

    result = agent._synthesize_final_analysis(
        service="payment-service",
        namespace="production",
        question="Why is payment-service in CrashLoopBackOff due to database timeout?",
        evidence=evidence,
        tools_used=[],
        iterations=5,
    )

    assert result["runbooks"]
    assert result["runbooks"][0]["id"] == "db-connection-failure"
    assert "runbook" in llm.create_chat_completion.call_args.kwargs["messages"][1]["content"].lower()
