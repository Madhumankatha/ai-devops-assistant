import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from llama_cpp import Llama

from .schemas import IncidentAnalysis


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# Model configuration
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    str(BASE_DIR / "models" / "qwen3.5-2b-ud-q4_k_xl.gguf"),
)

N_CTX = int(os.getenv("N_CTX", "4096"))
N_THREADS = int(
    os.getenv(
        "N_THREADS",
        str(os.cpu_count() or 4),
    )
)
N_BATCH = int(os.getenv("N_BATCH", "256"))


# ---------------------------------------------------------
# Validate model
# ---------------------------------------------------------

if not Path(MODEL_PATH).exists():
    raise FileNotFoundError(
        f"Qwen GGUF model not found:\n{MODEL_PATH}\n\n"
        "Please place the .gguf model inside the models/ "
        "directory or configure MODEL_PATH in .env."
    )


# ---------------------------------------------------------
# Load Qwen
# ---------------------------------------------------------

print("=" * 60)
print("Loading local Qwen model")
print("=" * 60)
print(f"Model       : {MODEL_PATH}")
print(f"Context     : {N_CTX}")
print(f"CPU threads : {N_THREADS}")
print(f"Batch size  : {N_BATCH}")
print("=" * 60)


llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=N_CTX,
    n_threads=N_THREADS,
    n_batch=N_BATCH,
    verbose=False,
)


print("Qwen model loaded successfully.")
print("=" * 60)


# ---------------------------------------------------------
# System prompt
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are an expert Site Reliability Engineer (SRE).

Your job is to analyze production incidents using ONLY
the evidence provided by the user.

IMPORTANT RULES:

1. Do not invent facts.
2. Do not assume information that is not present.
3. Clearly distinguish evidence from inference.
4. Identify the most likely root cause.
5. Recommend practical remediation steps.
6. Severity must be exactly one of:
   LOW, MEDIUM, HIGH, CRITICAL.
7. Confidence must be a number between 0 and 1.
8. Return ONLY valid JSON.
9. Do not include Markdown.
10. Do not include ```json fences.

Return exactly this JSON structure:

{
    "summary": "Short incident summary",
    "severity": "HIGH",
    "root_cause": "Most likely root cause",
    "evidence": [
        "Evidence 1",
        "Evidence 2"
    ],
    "recommended_actions": [
        "Action 1",
        "Action 2"
    ],
    "confidence": 0.90
}
"""


# ---------------------------------------------------------
# JSON extraction helper
# ---------------------------------------------------------

def _extract_json(text: str) -> dict:
    """
    Extract JSON from the model response.

    Qwen may occasionally return additional text even when
    explicitly instructed to return JSON.
    """

    text = text.strip()

    # Remove Markdown fences if the model generates them.
    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

        if text.lower().startswith("json"):
            text = text[4:].strip()

    # Find JSON object boundaries.
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            f"Model did not return valid JSON.\nResponse:\n{text}"
        )

    json_text = text[start:end + 1]

    try:
        return json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse model JSON.\n"
            f"Response:\n{text}"
        ) from exc


# ---------------------------------------------------------
# Incident analysis
# ---------------------------------------------------------

def analyze_incident(
    service: str,
    environment: str,
    logs: str,
    description: str,
) -> IncidentAnalysis:

    user_prompt = f"""
Analyze the following production incident.

SERVICE:
{service}

ENVIRONMENT:
{environment}

INCIDENT DESCRIPTION:
{description}

LOGS:
{logs}

Return only the requested JSON object.
"""

    start_time = time.perf_counter()

    response = llm.create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.1,
        max_tokens=700,
    )

    elapsed = time.perf_counter() - start_time

    content = response["choices"][0]["message"]["content"]

    data = _extract_json(content)

    result = IncidentAnalysis.model_validate(data)

    print(
        f"Incident analysis completed in "
        f"{elapsed:.2f}s"
    )

    return result