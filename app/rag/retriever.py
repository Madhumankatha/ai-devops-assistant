from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class RunbookChunk:
    """A small searchable runbook section."""

    runbook_id: str
    title: str
    content: str
    score: float


class RunbookRetriever:
    """Lightweight local retriever for the mock DevOps runbook corpus.

    This intentionally uses deterministic lexical retrieval so the project can
    run fully offline on CPU. It is an upgrade point for embeddings/pgvector
    or Qdrant without changing the agent-facing interface.
    """

    def __init__(self, documents: list[dict[str, Any]] | None = None) -> None:
        self.documents = documents or DEFAULT_RUNBOOKS

    def search(self, query: str, top_k: int = 3) -> list[RunbookChunk]:
        tokens = self._tokens(query)
        if not tokens:
            return []

        results: list[RunbookChunk] = []
        for document in self.documents:
            text = f"{document['title']} {document['content']}".lower()
            doc_tokens = self._tokens(text)
            overlap = tokens & doc_tokens
            if not overlap:
                continue

            # Favor exact diagnostic terms while keeping retrieval deterministic.
            score = len(overlap) / max(len(tokens), 1)
            phrase_bonus = sum(0.15 for token in tokens if token in text)
            score += min(phrase_bonus, 0.75)
            results.append(
                RunbookChunk(
                    runbook_id=document["id"],
                    title=document["title"],
                    content=document["content"],
                    score=round(score, 4),
                )
            )

        results.sort(key=lambda item: (-item.score, item.runbook_id))
        return results[: max(top_k, 0)]

    @staticmethod
    def _tokens(text: str) -> set[str]:
        stop_words = {
            "the", "a", "an", "is", "are", "to", "of", "and", "or",
            "for", "in", "on", "with", "why", "what", "how", "service",
        }
        return {
            token
            for token in re.findall(r"[a-z0-9][a-z0-9_-]+", text.lower())
            if token not in stop_words
        }


DEFAULT_RUNBOOKS = [
    {
        "id": "db-connection-failure",
        "title": "Runbook: Database Connection Failures",
        "content": (
            "Symptoms: CrashLoopBackOff, database connection timeout, failed to "
            "connect to database, application startup failure, readiness probe "
            "failure. Checks: verify database availability; validate credentials "
            "and connection strings; test network connectivity from the pod; "
            "check connection pool and database connection limits. Remediation: "
            "correct configuration or credentials, restore database availability, "
            "adjust connection limits when justified, then restart the affected "
            "deployment and verify readiness."
        ),
    },
    {
        "id": "high-latency-errors",
        "title": "Runbook: High Error Rate and Latency",
        "content": (
            "Symptoms: elevated error rate, high P95 latency, increased request "
            "rate. Checks: inspect application logs, dependency health, CPU and "
            "memory saturation, downstream latency, and recent deployments. "
            "Remediation: address the failing dependency, reduce overload, scale "
            "the constrained component when appropriate, and verify error rate "
            "and P95 latency recover."
        ),
    },
    {
        "id": "pod-crashloop",
        "title": "Runbook: Kubernetes CrashLoopBackOff",
        "content": (
            "Symptoms: repeated pod restarts, CrashLoopBackOff, failed readiness "
            "or liveness probes. Checks: inspect pod status, previous container "
            "logs, Kubernetes events, probes, resource limits, and dependency "
            "connectivity. Remediation: fix the startup failure or probe "
            "configuration, then verify stable replicas and readiness."
        ),
    },
]
