from typing import Any


def get_service_metrics(
    service: str,
    namespace: str,
) -> dict[str, Any]:
    """
    Return mock Prometheus metrics for a service.
    """

    return {
        "success": True,
        "service": service,
        "namespace": namespace,
        "metrics": {
            "cpu_percent": 87.5,
            "memory_percent": 91.2,
            "request_rate_per_second": 245,
            "error_rate_percent": 18.7,
            "p95_latency_ms": 1850,
        },
    }


def get_error_rate(
    service: str,
    namespace: str,
) -> dict[str, Any]:
    """
    Return mock error-rate metrics for a service.
    """

    return {
        "success": True,
        "service": service,
        "namespace": namespace,
        "metric": {
            "name": "error_rate_percent",
            "value": 18.7,
            "unit": "percent",
        },
    }


def get_latency(
    service: str,
    namespace: str,
) -> dict[str, Any]:
    """
    Return mock latency metrics for a service.
    """

    return {
        "success": True,
        "service": service,
        "namespace": namespace,
        "metric": {
            "name": "p95_latency_ms",
            "value": 1850,
            "unit": "milliseconds",
        },
    }
