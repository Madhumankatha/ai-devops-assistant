from fastapi import FastAPI

from .llm import analyze_incident
from .schemas import IncidentRequest, IncidentAnalysis


app = FastAPI(
    title="LLM Engineering Lab",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


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