from pydantic import BaseModel, Field


class IncidentRequest(BaseModel):
    service: str
    environment: str
    logs: str
    description: str


class IncidentAnalysis(BaseModel):
    summary: str
    severity: str
    root_cause: str
    evidence: list[str]
    recommended_actions: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float