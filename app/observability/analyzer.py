from statistics import mean

from app.observability.time_utils import parse_timestamp


class MetricAnalyzer:
    """
    Analyze service metrics using a historical baseline.

    The analyzer separates:
    - baseline observations
    - current/incident observations

    This prevents degraded incident-period data from contaminating
    the baseline.
    """

    def __init__(
        self,
        baseline_points: int = 4,
        anomaly_multiplier: float = 2.0,
    ):
        self.baseline_points = baseline_points
        self.anomaly_multiplier = anomaly_multiplier

    def analyze(
        self,
        metrics_data: dict,
        baseline_data: dict | None = None,
    ) -> dict:
        """
        Analyze incident metrics against a separate historical baseline.

        metrics_data:
            Metrics from the incident/current window.

        baseline_data:
            Historical metrics from before the incident.

        If baseline_data is not provided, the analyzer falls back
        to using the first baseline_points observations from metrics_data.
        This preserves backward compatibility with existing tests/code.
        """

        service = metrics_data.get("service")

        observations = metrics_data.get("metrics", [])

        if not observations:
            return {
                "service": service,
                "status": "no_data",
                "metrics": {},
            }

        observations = sorted(
            observations,
            key=lambda item: parse_timestamp(item.get("timestamp"))
            or parse_timestamp("1970-01-01T00:00:00Z"),
        )

        baseline_observations = []
        if baseline_data is not None:
            baseline_observations = baseline_data.get(
                "metrics", []
        )
            baseline_observations = sorted(
                baseline_observations,
                key=lambda item: (
                    parse_timestamp(item.get("timestamp"))
                    or parse_timestamp("1970-01-01T00:00:00Z")
                ),
            )

        # Fall back only when no historical baseline is available.
        if not baseline_observations:
            baseline_observations = observations[
                : self.baseline_points
            ]

        if not baseline_observations:
            return {
                "service": service,
                "status": "insufficient_baseline",
                "metrics": {},
            }


        # ---------------------------------------------------------
        # Current observation
        # ---------------------------------------------------------

        current = observations[-1]

        # ---------------------------------------------------------
        # Baseline window
        # ---------------------------------------------------------

        baseline_start = baseline_observations[0].get("timestamp")
        baseline_end = baseline_observations[-1].get("timestamp")

        current_timestamp = current.get("timestamp")

        # ---------------------------------------------------------
        # Metrics to analyze
        # ---------------------------------------------------------

        metric_definitions = {
            "p50_ms": "latency",
            "p95_ms": "latency",
            "p99_ms": "latency",
            "database_latency_ms": "database_latency",
            "requests_per_second": "traffic",
            "error_rate_percent": "error_rate",
            "cpu_percent": "cpu",
            "memory_percent": "memory",
        }

        results = {}

        for metric_name, metric_type in metric_definitions.items():

            baseline_values = [
                observation.get(metric_name)
                for observation in baseline_observations
                if isinstance(observation.get(metric_name), (int, float))
            ]

            current_value = current.get(metric_name)

            if not baseline_values:
                continue

            if not isinstance(current_value, (int, float)):
                continue

            baseline_value = mean(baseline_values)

            change_percent = self._percentage_change(
                baseline_value,
                current_value,
            )

            anomaly = self._is_anomaly(
                metric_type=metric_type,
                baseline_value=baseline_value,
                current_value=current_value,
            )

            results[metric_name] = {
                "metric_type": metric_type,
                "baseline": round(baseline_value, 4),
                "current": current_value,
                "change_percent": round(change_percent, 2),
                "anomaly": anomaly,
            }

        return {
            "service": service,
            "status": "analyzed",
            "baseline_window": {
                "start": baseline_start,
                "end": baseline_end,
                "points": len(baseline_observations),
            },
            "current_timestamp": current_timestamp,
            "metrics": results,
        }

    def _percentage_change(
        self,
        baseline: float,
        current: float,
    ) -> float:
        if baseline == 0:
            if current == 0:
                return 0.0

            return float("inf")

        return ((current - baseline) / baseline) * 100

    def _is_anomaly(
        self,
        metric_type: str,
        baseline_value: float,
        current_value: float,
    ) -> bool:

        if baseline_value <= 0:
            return False

        # Traffic is contextual evidence rather than an automatic
        # anomaly signal.
        if metric_type == "traffic":
            return False

        return current_value > (
            baseline_value * self.anomaly_multiplier
        )


def analyze_service_metrics(
    metrics_data: dict,
    baseline_data: dict | None = None,
) -> dict:
    """
    Convenience wrapper around MetricAnalyzer.
    """

    analyzer = MetricAnalyzer()

    return analyzer.analyze(
        metrics_data=metrics_data,
        baseline_data=baseline_data,
    )
