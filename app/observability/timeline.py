from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.observability.time_utils import parse_timestamp


@dataclass
class TimelineEvent:
    """
    Represents a single event in an incident timeline.
    """

    timestamp: datetime
    event_type: str
    source: str
    description: str
    data: dict[str, Any]


class IncidentTimeline:
    """
    Builds a chronological timeline from observability data.

    Sources:
        - Metrics
        - Logs
        - Deployments
    """

    def __init__(self):
        self.events: list[TimelineEvent] = []

    def add_metric_events(
        self,
        metrics: dict[str, Any],
    ) -> None:
        """
        Convert historical metric observations into
        timeline events.
        """

        observations = metrics.get(
            "metrics",
            [],
        )

        for observation in observations:

            timestamp = parse_timestamp(
                observation.get("timestamp")
            )

            if timestamp is None:
                continue

            p95 = observation.get("p95_ms")
            db_latency = observation.get(
                "database_latency_ms"
            )
            error_rate = observation.get(
                "error_rate_percent"
            )

            description_parts = []

            if p95 is not None:
                description_parts.append(
                    f"P95 latency={p95}ms"
                )

            if db_latency is not None:
                description_parts.append(
                    f"DB latency={db_latency}ms"
                )

            if error_rate is not None:
                description_parts.append(
                    f"error rate={error_rate}%"
                )

            description = ", ".join(
                description_parts
            )

            self.events.append(
                TimelineEvent(
                    timestamp=timestamp,
                    event_type="metric",
                    source="metrics",
                    description=description,
                    data=observation,
                )
            )

    def add_log_events(
        self,
        logs: list[str],
    ) -> None:
        """
        Convert log lines into timeline events.
        """

        for line in logs:

            timestamp = self._extract_timestamp(
                line
            )

            if timestamp is None:
                continue

            description = line

            self.events.append(
                TimelineEvent(
                    timestamp=timestamp,
                    event_type="log",
                    source="application_logs",
                    description=description,
                    data={
                        "log": line,
                    },
                )
            )

    def add_deployment_event(
        self,
        deployment: dict[str, Any],
    ) -> None:
        """
        Convert deployment information into a timeline event.
        """

        timestamp = parse_timestamp(
            deployment.get("deployed_at")
        )

        if timestamp is None:
            return

        version = deployment.get(
            "version",
            "unknown",
        )

        previous_version = deployment.get(
            "previous_version",
            "unknown",
        )

        deployment_id = deployment.get(
            "deployment_id",
            "unknown",
        )

        changes = deployment.get(
            "changes",
            [],
        )

        change_text = ", ".join(
            str(change)
            for change in changes
        )

        description = (
            f"Deployment {version} "
            f"(previous={previous_version}) "
            f"id={deployment_id}"
        )

        if change_text:
            description += (
                f"; changes: {change_text}"
            )

        self.events.append(
            TimelineEvent(
                timestamp=timestamp,
                event_type="deployment",
                source="deployment_system",
                description=description,
                data=deployment,
            )
        )

    def build(self) -> list[dict[str, Any]]:
        """
        Sort all timeline events chronologically.

        Returns:
            List of serializable timeline events.
        """

        self.events.sort(
            key=lambda event: event.timestamp
        )

        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "source": event.source,
                "description": event.description,
                "data": event.data,
            }
            for event in self.events
        ]

    @staticmethod
    def _extract_timestamp(
        line: str,
    ) -> datetime | None:
        """
        Extract timestamp from a log line.

        Expected format:

        2026-09-15T18:21:44Z WARN ...
        """

        if not line:
            return None

        timestamp_text = line.split(
            " ",
            1,
        )[0]

        return parse_timestamp(
            timestamp_text
        )