from app.rag.retriever import RunbookRetriever


def test_database_failure_retrieves_database_runbook() -> None:
    retriever = RunbookRetriever()

    results = retriever.search(
        "payment-service CrashLoopBackOff database connection timeout"
    )

    assert results
    assert results[0].runbook_id == "db-connection-failure"
    assert "database" in results[0].content.lower()


def test_retriever_is_deterministic() -> None:
    retriever = RunbookRetriever()
    query = "high error rate and P95 latency"

    first = retriever.search(query)
    second = retriever.search(query)

    assert first == second
