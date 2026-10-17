from pprint import pprint

from app.observability.reasoner import GeminiRCAReasoner


def main():
    reasoner = GeminiRCAReasoner()

    investigation = {
        "service": "payment-api",

        "investigation_window": {
            "start": "2026-09-15T18:15:00Z",
            "end": "2026-09-15T18:30:00Z",
        },

        "investigation_summary": {
            "observed_anomalies": [
                {
                    "metric": "database_latency",
                    "baseline": 390,
                    "current": 4900,
                    "change_percent": 1156.41,
                    "metric_type": "database_latency",
                },
                {
                    "metric": "p95",
                    "baseline": 415,
                    "current": 5800,
                    "change_percent": 1297.59,
                    "metric_type": "latency",
                },
                {
                    "metric": "p99",
                    "baseline": 445,
                    "current": 7200,
                    "change_percent": 1517.98,
                    "metric_type": "latency",
                },
            ],

            "key_logs": [
                "2026-09-15T18:21:44Z WARN database query latency=3200ms query=payment_lookup",
                "2026-09-15T18:23:18Z WARN database query latency=3700ms query=payment_lookup",
                "2026-09-15T18:24:01Z WARN database query latency=4100ms query=payment_lookup",
                "2026-09-15T18:25:42Z WARN database query latency=4500ms query=payment_lookup",
                "2026-09-15T18:27:33Z ERROR request latency=5800ms endpoint=/payments",
            ],

            "deployment_correlation": {
                "version": "v1.8.3",
                "previous_version": "v1.8.2",
                "deployed_at": "2026-09-15T18:15:00Z",
                "status": "successful",
                "changes": [
                    "Updated payment lookup query",
                    "Added transaction metadata filtering",
                ],
            },

            "missing_evidence": [
                "Database EXPLAIN ANALYZE execution plan for affected payment_lookup query unavailable",
                "Database CPU, I/O, lock contention, index usage unavailable",
            ],
        },

        "rca_analysis": {
            "hypotheses": [
                {
                    "hypothesis": (
                        "A database/query performance regression "
                        "associated with the recent deployment "
                        "is a likely contributor to the incident."
                    ),
                    "confidence": "medium",
                }
            ],

            "limitations": [
                "Query execution plan is unavailable.",
                "Index usage information is unavailable.",
                "Database lock contention information is unavailable.",
            ],

            "recommendations": [
                "Compare the affected payment_lookup query execution plan between the current and previous deployment.",
                "Check whether the expected database indexes are being used.",
                "Inspect database I/O, CPU, and lock contention.",
            ],
        },
    }

    result = reasoner.reason(investigation)

    pprint(result)


if __name__ == "__main__":
    main()