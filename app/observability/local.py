import json
from datetime import datetime
from pathlib import Path

from app.observability.base import ObservabilityProvider
from app.observability.time_utils import parse_timestamp


class LocalObservabilityProvider(ObservabilityProvider):
    """
    Local observability provider.

    Reads mock metrics, logs, and deployment information
    from the local data directory.

    This provider allows OpsPilot to run without external
    observability infrastructure.
    """

    METRICS_DIR = Path("data/metrics")
    LOGS_DIR = Path("data/logs")
    DEPLOYMENTS_DIR = Path("data/deployments")

    def get_service_metrics(
        self,
        service: str,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict:
        """
        Retrieve service metrics.

        If start_time and end_time are provided, only metric
        observations inside that time window are returned.

        Args:
            service: Name of the service.
            start_time: Optional ISO-8601 start timestamp.
            end_time: Optional ISO-8601 end timestamp.

        Returns:
            Dictionary containing metric observations.
        """

        print(
            f"[LOCAL] get_service_metrics("
            f"service={service}, "
            f"start_time={start_time!r}, "
            f"end_time={end_time!r}"
            f")"
        )

        metrics_file = self.METRICS_DIR / f"{service}.json"

        if not metrics_file.exists():
            return {
                "error": (
                    f"No metrics available for service: {service}"
                )
            }

        try:
            with metrics_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except json.JSONDecodeError:
            return {
                "error": (
                    f"Invalid metrics data for service: {service}"
                )
            }

        # Support the old single-snapshot format.
        if "metrics" not in data:
            return data

        observations = data["metrics"]

        start_dt = parse_timestamp(start_time)
        end_dt = parse_timestamp(end_time)

        filtered_observations = []

        for observation in observations:
            timestamp = observation.get("timestamp")

            if not timestamp:
                continue

            observation_dt = parse_timestamp(timestamp)

            if observation_dt is None:
                continue

            if start_dt and observation_dt < start_dt:
                continue

            if end_dt and observation_dt > end_dt:
                continue

            filtered_observations.append(observation)

        return {
            "service": data.get(
                "service",
                service,
            ),
            "metrics": filtered_observations,
            "start_time": start_time,
            "end_time": end_time,
        }

    def search_logs(
        self,
        service: str,
        keyword: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[str]:
        """
        Search service logs.

        Supports both keyword filtering and timestamp filtering.

        Args:
            service: Name of the service.
            keyword: Optional keyword to search for.
            start_time: Optional ISO-8601 start timestamp.
            end_time: Optional ISO-8601 end timestamp.

        Returns:
            Matching log lines.
        """

        print(
            f"[LOCAL] search_logs("
            f"service={service}, "
            f"keyword={keyword!r}, "
            f"start_time={start_time!r}, "
            f"end_time={end_time!r}"
            f")"
        )

        log_file = self.LOGS_DIR / f"{service}.log"

        if not log_file.exists():
            return [
                f"No logs available for service: {service}"
            ]

        start_dt = parse_timestamp(start_time)
        end_dt = parse_timestamp(end_time)

        keyword_lower = (
            keyword.lower()
            if keyword
            else None
        )

        matching_lines = []

        with log_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:
                line = line.strip()

                if not line:
                    continue

                timestamp = self._extract_log_timestamp(
                    line
                )

                if timestamp is not None:

                    if start_dt and timestamp < start_dt:
                        continue

                    if end_dt and timestamp > end_dt:
                        continue

                if (
                    keyword_lower
                    and keyword_lower not in line.lower()
                ):
                    continue

                matching_lines.append(line)

        return matching_lines

    def get_recent_deployment(
        self,
        service: str,
    ) -> dict:
        """
        Retrieve the most recent deployment information.

        Args:
            service: Name of the service.

        Returns:
            Deployment information.
        """

        print(
            f"[LOCAL] get_recent_deployment("
            f"service={service}"
            f")"
        )

        deployment_file = (
            self.DEPLOYMENTS_DIR / f"{service}.json"
        )

        if not deployment_file.exists():
            return {
                "error": (
                    "No deployment information available "
                    f"for service: {service}"
                )
            }

        try:
            with deployment_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                return json.load(file)

        except json.JSONDecodeError:
            return {
                "error": (
                    "Invalid deployment data available "
                    f"for service: {service}"
                )
            }

    @staticmethod
    def _extract_log_timestamp(
        line: str,
    ) -> datetime | None:
        """
        Extract the timestamp from a log line.

        Expected format:

        2026-09-15T18:18:12Z INFO ...
        """

        if not line:
            return None

        timestamp_text = line.split(
            " ",
            1,
        )[0]

        return parse_timestamp(timestamp_text)
