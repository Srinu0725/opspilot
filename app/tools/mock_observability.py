
from datetime import datetime, timezone


def get_service_metrics(service: str) -> dict:
    """Simulated telemetry for the hackathon demo."""
    return {
        "service": service,
        "source": "mock_observability",
        "simulated": True,
        "metrics": {
            "p95_ms": {"current": 1460, "baseline": 185},
            "p99_ms": {"current": 2180, "baseline": 290},
            "database_latency_ms": {"current": 1120, "baseline": 95},
            "error_rate_percent": {"current": 0.64, "baseline": 0.08},
            "cpu_percent": {"current": 41, "baseline": 38},
            "memory_percent": {"current": 53, "baseline": 51},
        },
    }


def search_logs(service: str) -> dict:
    """Simulated logs for the payment API incident."""
    return {
        "service": service,
        "source": "mock_observability",
        "simulated": True,
        "logs": [
            {
                "timestamp": "2026-10-19T14:38:22Z",
                "level": "WARN",
                "message": "Payment endpoint latency elevated: 740ms",
            },
            {
                "timestamp": "2026-10-19T14:41:07Z",
                "level": "WARN",
                "message": "Slow database query: payment_lookup, 680ms",
            },
            {
                "timestamp": "2026-10-19T14:48:12Z",
                "level": "ERROR",
                "message": "Payment request timed out",
            },
        ],
    }


def get_recent_deployment(service: str) -> dict:
    """Simulated deployment history for the demo."""
    return {
        "service": service,
        "source": "mock_observability",
        "simulated": True,
        "deployments": [
            {
                "version": "v2.4.1",
                "timestamp": "2026-10-19T14:34:10Z",
                "status": "completed",
            }
        ],
    }
