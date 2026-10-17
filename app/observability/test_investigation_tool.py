from pprint import pprint

from app.tools.investigation import (
    investigate_incident,
)


def main():
    result = investigate_incident(
        service="payment-api",
        start_time="2026-09-15T18:15:00Z",
        end_time="2026-09-15T18:30:00Z",
    )

    print()
    print("=" * 80)
    print("INVESTIGATION TOOL")
    print("=" * 80)

    print()
    print("Service:")
    print(result["service"])

    print()
    print("Metric Analysis:")
    pprint(
        result["metric_analysis"]
    )

    print()
    print("Timeline:")

    for event in result["timeline"]:
        print(
            f"{event['timestamp']} "
            f"[{event['event_type'].upper()}] "
            f"{event['description']}"
        )

    print()
    print("Evidence:")

    for evidence in result["evidence"]:
        print(
            f"[{evidence['strength'].upper()}] "
            f"{evidence['observation']}"
        )
    print("\nRunbook Context:")
    print("\nRCA Analysis:")

    pprint(
        result.get(
            "rca_analysis"
        )
    )

    for context in result.get("runbook_context", []):
        print(f"\nQuery: {context['query']}")

        for item in context["results"]:
            print(
                f"[{item.get('score', 'N/A')}] "
                f"{item.get('title', item.get('section', 'unknown'))}"
            )

            print(
                item.get(
                    "text",
                    item.get("content", item)
                )            )
if __name__ == "__main__":
    main()
