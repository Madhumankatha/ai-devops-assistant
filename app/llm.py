import json
import logging
import time
from pathlib import Path

from llama_cpp import Llama

from .core.config import MODEL_PATH, N_BATCH, N_CTX, N_THREADS
from .schemas.incident import IncidentAnalysis

logger = logging.getLogger(__name__)

if not Path(MODEL_PATH).exists():
    raise FileNotFoundError(
        f"Qwen GGUF model not found: {MODEL_PATH}. "
        "Place the model under models/ or set MODEL_PATH in .env."
    )

logger.info(
    "Loading Qwen model | path=%s | context=%s | threads=%s | batch=%s",
    MODEL_PATH,
    N_CTX,
    N_THREADS,
    N_BATCH,
)

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=N_CTX,
    n_threads=N_THREADS,
    n_batch=N_BATCH,
    verbose=False,
)

logger.info("Qwen model loaded successfully")

SYSTEM_PROMPT = """
You are an expert Site Reliability Engineer (SRE).

Analyze production incidents using ONLY the evidence provided.

Rules:
1. Never invent facts.
2. Do not claim a root cause unless the evidence supports it.
3. Every root-cause claim must be supported by at least one evidence item.
4. If evidence is insufficient, use exactly:
   "Insufficient evidence to determine the root cause."
5. Recommended actions must be relevant to the evidence.
6. Severity must be exactly LOW, MEDIUM, HIGH, or CRITICAL.
7. Confidence must be between 0 and 1.
8. Return ONLY valid JSON. No Markdown or code fences.

Return exactly:
{
  "summary": "Short incident summary",
  "severity": "HIGH",
  "root_cause": "Evidence-supported root cause or insufficient evidence",
  "evidence": ["Evidence 1"],
  "recommended_actions": ["Action 1"],
  "confidence": 0.90
}
"""


def _extract_json(text: str) -> dict:
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
    if start == -1 or end == -1:
        raise ValueError(f"Model did not return JSON: {text}")

    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON from model: {text}") from exc


def analyze_incident(
    service: str,
    environment: str,
    logs: str,
    description: str,
) -> IncidentAnalysis:
    prompt = f"""
SERVICE: {service}
ENVIRONMENT: {environment}

INCIDENT DESCRIPTION:
{description}

LOGS:
{logs}

Return only the requested JSON object.
"""

    start = time.perf_counter()

    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=700,
    )

    elapsed_ms = (time.perf_counter() - start) * 1000
    content = response["choices"][0]["message"]["content"]
    data = _extract_json(content)
    data["processing_time_ms"] = round(elapsed_ms, 2)

    result = IncidentAnalysis.model_validate(data)

    logger.info(
        "Incident analysis completed | service=%s | severity=%s | latency_ms=%.2f",
        service,
        result.severity.value,
        elapsed_ms,
    )

    return result
