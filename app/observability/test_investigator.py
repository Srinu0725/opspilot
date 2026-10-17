from pprint import pprint

from app.observability.investigator import (
    IncidentInvestigator,
)


def main():
    investigator = IncidentInvestigator()

    result = investigator.investigate(
        service="payment-api",
        start_time="2026-09-15T18:15:00Z",
        end_time="2026-09-15T18:30:00Z",
    )

    print()
    print("=" * 80)
    print("STRUCTURED INVESTIGATION")
    print("=" * 80)

    print()
    print("SERVICE")
    print(result["service"])

    print()
    print("METRIC ANALYSIS")
    pprint(
        result["metric_analysis"]
    )

    print()
    print("TIMELINE")

    for event in result["timeline"]:
        print(
            f"{event['timestamp']} "
            f"[{event['event_type'].upper()}] "
            f"{event['description']}"
        )

    print()
    print("EVIDENCE")

    for item in result["evidence"]:
        print(
            f"[{item['strength'].upper()}] "
            f"{item['observation']}"
        )


if __name__ == "__main__":
    main()