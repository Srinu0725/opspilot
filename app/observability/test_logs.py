from app.observability.local import LocalObservabilityProvider


def main():
    provider = LocalObservabilityProvider()

    results = provider.search_logs(
        service="payment-api",
        start_time="2026-09-15T18:20:00Z",
        end_time="2026-09-15T18:30:00Z",
    )

    print()
    print("=" * 80)
    print("TIME-WINDOW LOG SEARCH")
    print("=" * 80)

    print(
        f"Results: {len(results)}"
    )

    for line in results:
        print(line)


if __name__ == "__main__":
    main()