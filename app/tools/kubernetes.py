from typing import Any


def get_pod_status(
    namespace: str = "default",
) -> dict[str, Any]:

    """
    Read-only Kubernetes pod status.

    This first implementation uses mock data so that
    the project can be developed and tested without
    requiring a Kubernetes cluster.
    """

    return {
        "namespace": namespace,
        "pods": [
            {
                "name": "payment-service-7d9f8c6f7d-x2k9p",
                "status": "CrashLoopBackOff",
                "ready": "0/1",
                "restarts": 12,
            },
            {
                "name": "payment-service-7d9f8c6f7d-r8m2q",
                "status": "Running",
                "ready": "1/1",
                "restarts": 0,
            },
        ],
    }


def get_pod_logs(
    pod_name: str,
    namespace: str = "default",
    tail_lines: int = 100,
) -> dict[str, Any]:

    return {
        "namespace": namespace,
        "pod": pod_name,
        "tail_lines": tail_lines,
        "logs": [
            "INFO Starting payment service",
            "INFO Connecting to database",
            "ERROR database connection timeout after 30 seconds",
            "ERROR failed to connect to database",
            "ERROR application startup failed",
        ],
    }


def get_kubernetes_events(
    namespace: str = "default",
) -> dict[str, Any]:

    return {
        "namespace": namespace,
        "events": [
            {
                "type": "Warning",
                "reason": "BackOff",
                "message": (
                    "Back-off restarting failed container"
                ),
            },
            {
                "type": "Warning",
                "reason": "Unhealthy",
                "message": (
                    "Readiness probe failed"
                ),
            },
        ],
    }


def get_deployment_status(
    deployment_name: str,
    namespace: str = "default",
) -> dict[str, Any]:

    return {
        "namespace": namespace,
        "deployment": deployment_name,
        "desired_replicas": 2,
        "ready_replicas": 1,
        "available_replicas": 1,
        "updated_replicas": 2,
    }