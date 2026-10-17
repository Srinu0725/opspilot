from app.observability.local import (
    LocalObservabilityProvider,
)

from app.observability.timeline import (
    IncidentTimeline,
)


def main():
    provider = LocalObservabilityProvider()

    metrics = provider.get_service_metrics(
        service="payment-api"
    )

    logs = provider.search_logs(
        service="payment-api",
        start_time="2026-09-15T18:15:00Z",
        end_time="2026-09-15T18:30:00Z",
    )

    deployment = provider.get_recent_deployment(
        service="payment-api"
    )

    timeline = IncidentTimeline()

    timeline.add_metric_events(
        metrics
    )

    timeline.add_log_events(
        logs
    )

    timeline.add_deployment_event(
        deployment
    )

    events = timeline.build()

    print()
    print("=" * 80)
    print("INCIDENT TIMELINE")
    print("=" * 80)

    for event in events:
        print()
        print(
            f"{event['timestamp']} "
            f"[{event['event_type'].upper()}]"
        )

        print(
            f"Source: {event['source']}"
        )

        print(
            f"Event: {event['description']}"
        )


if __name__ == "__main__":
    main()