from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentRequest(BaseModel):
    service: str = Field(min_length=1, max_length=200)
    environment: str = Field(min_length=1, max_length=100)
    logs: str = Field(min_length=1, max_length=20000)
    description: str = Field(min_length=1, max_length=5000)


class IncidentAnalysis(BaseModel):
    summary: str
    severity: Severity
    root_cause: str
    evidence: list[str]
    recommended_actions: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float = Field(ge=0.0)
