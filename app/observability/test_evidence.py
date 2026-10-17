from app.observability.local import (
    LocalObservabilityProvider,
)

from app.observability.analyzer import (
    MetricAnalyzer,
)

from app.observability.evidence import (
    EvidenceCollector,
)


def main():
    provider = LocalObservabilityProvider()

    metrics = provider.get_service_metrics(
        service="payment-api"
    )

    deployment = provider.get_recent_deployment(
        service="payment-api"
    )

    logs = provider.search_logs(
        service="payment-api",
        start_time="2026-09-15T18:15:00Z",
        end_time="2026-09-15T18:30:00Z",
    )

    analyzer = MetricAnalyzer()

    metric_analysis = analyzer.analyze(
        metrics
    )

    collector = EvidenceCollector()

    # Add metric evidence
    for (
        metric_name,
        metric_data,
    ) in metric_analysis.get(
        "metrics",
        {},
    ).items():

        collector.add_metric_evidence(
            metric_name=metric_name,
            metric_data=metric_data,
            timestamp=metric_analysis.get(
                "current_timestamp"
            ),
        )

    # Add log evidence
    for log_line in logs:
        collector.add_log_evidence(
            log_line
        )

    # Add deployment evidence
    collector.add_deployment_evidence(
        deployment
    )

    # Explicitly record important missing evidence
    collector.add_missing_evidence(
        "Database EXPLAIN ANALYZE execution plan "
        "for the updated payment_lookup query is unavailable."
    )

    collector.add_missing_evidence(
        "Database CPU, I/O, lock contention, and "
        "index usage metrics are unavailable."
    )

    evidence = collector.build()

    print()
    print("=" * 80)
    print("EVIDENCE")
    print("=" * 80)

    for index, item in enumerate(
        evidence,
        start=1,
    ):
        print()
        print(
            f"{index}. "
            f"[{item['strength'].upper()}] "
            f"{item['evidence_type']}"
        )

        print(
            f"Timestamp: "
            f"{item['timestamp']}"
        )

        print(
            f"Source: "
            f"{item['source']}"
        )

        print(
            f"Observation: "
            f"{item['observation']}"
        )


if __name__ == "__main__":
    main()