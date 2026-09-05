import pytest
from pydantic import ValidationError

from app.schemas.incident import IncidentRequest, Severity


def test_valid_incident_request():
    request = IncidentRequest(
        service="payment-service",
        environment="production",
        description="Pods are restarting",
        logs="ERROR database connection timeout",
    )
    assert request.service == "payment-service"


def test_empty_service_is_rejected():
    with pytest.raises(ValidationError):
        IncidentRequest(
            service="",
            environment="production",
            description="Pods are restarting",
            logs="ERROR database connection timeout",
        )


def test_severity_values():
    assert Severity.HIGH.value == "HIGH"
    assert Severity.CRITICAL.value == "CRITICAL"
