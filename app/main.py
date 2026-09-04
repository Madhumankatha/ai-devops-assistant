from fastapi import FastAPI

from .llm import analyze_incident
from .schemas import IncidentRequest, IncidentAnalysis


app = FastAPI(
    title="LLM Engineering Lab",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": "qwen3.5-2b",
        "inference": "llama.cpp",
        "device": "cpu",
    }


@app.post(
    "/api/v1/analyze",
    response_model=IncidentAnalysis,
)
def analyze(request: IncidentRequest):

    return analyze_incident(
        service=request.service,
        environment=request.environment,
        logs=request.logs,
        description=request.description,
    )