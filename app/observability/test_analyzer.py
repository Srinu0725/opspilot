from app.observability.local import LocalObservabilityProvider
from app.observability.analyzer import MetricAnalyzer


def main():
    provider = LocalObservabilityProvider()

    metrics = provider.get_service_metrics(
        service="payment-api"
    )

    analyzer = MetricAnalyzer()

    result = analyzer.analyze(metrics)

    print()
    print("=" * 80)
    print("METRIC ANALYSIS")
    print("=" * 80)

    print(f"Service: {result['service']}")
    print(f"Status: {result['status']}")

    print()
    print("Baseline:")
    print(result["baseline_window"])

    print()
    print("Current timestamp:")
    print(result["current_timestamp"])

    print()
    print("Metrics:")

    for metric_name, metric in result["metrics"].items():
        print()
        print(metric_name)
        print(f"  Type: {metric['metric_type']}")
        print(f"  Baseline: {metric['baseline']}")
        print(f"  Current: {metric['current']}")
        print(
            f"  Change: "
            f"{metric['change_percent']}%"
        )
        print(
            f"  Anomaly: "
            f"{metric['anomaly']}"
        )


if __name__ == "__main__":
    main()