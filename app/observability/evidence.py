from dataclasses import dataclass
from typing import Any


@dataclass
class Evidence:
    """
    Represents a piece of evidence collected during
    an incident investigation.
    """

    evidence_type: str
    source: str
    observation: str
    strength: str
    timestamp: str | None = None
    data: dict[str, Any] | None = None


class EvidenceCollector:
    """
    Collects and structures evidence from observability
    sources.

    Evidence strength is assigned deterministically based
    on the type of observation.
    """

    def __init__(self):
        self.evidence: list[Evidence] = []

    def add_metric_evidence(
        self,
        metric_name: str,
        metric_data: dict[str, Any],
        timestamp: str | None = None,
    ) -> None:
        """
        Add evidence from metric analysis.
        """

        anomaly = metric_data.get(
            "anomaly",
            False,
        )

        baseline = metric_data.get(
            "baseline"
        )

        current = metric_data.get(
            "current"
        )

        change_percent = metric_data.get(
            "change_percent"
        )

        metric_type = metric_data.get(
            "metric_type",
            "unknown",
        )

        observation = (
            f"{metric_name}: "
            f"baseline={baseline}, "
            f"current={current}, "
            f"change={change_percent}%"
        )

        if anomaly:
            strength = "strong"
        else:
            strength = "supporting"

        self.evidence.append(
            Evidence(
                evidence_type="metric",
                source="metric_analyzer",
                observation=observation,
                strength=strength,
                timestamp=timestamp,
                data={
                    "metric_name": metric_name,
                    "metric_type": metric_type,
                    **metric_data,
                },
            )
        )

    def add_log_evidence(
        self,
        log_line: str,
    ) -> None:
        """
        Add evidence from an application log.

        Error and warning logs are treated as strong
        operational evidence because they directly describe
        observed service behavior.
        """

        strength = self._log_strength(
            log_line
        )

        timestamp = self._extract_timestamp(
            log_line
        )

        self.evidence.append(
            Evidence(
                evidence_type="log",
                source="application_logs",
                observation=log_line,
                strength=strength,
                timestamp=timestamp,
                data={
                    "log": log_line,
                },
            )
        )

    def add_deployment_evidence(
        self,
        deployment: dict[str, Any],
    ) -> None:
        """
        Add deployment information as evidence.

        A recent deployment is potentially important for
        temporal correlation, but deployment information
        alone does not prove causality.
        """

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

        deployed_at = deployment.get(
            "deployed_at"
        )

        changes = deployment.get(
            "changes",
            [],
        )

        observation = (
            f"Deployment {version} "
            f"(previous={previous_version}) "
            f"id={deployment_id}"
        )

        if changes:
            observation += (
                f"; changes={changes}"
            )

        self.evidence.append(
            Evidence(
                evidence_type="deployment",
                source="deployment_system",
                observation=observation,
                strength="strong",
                timestamp=deployed_at,
                data=deployment,
            )
        )

    def add_missing_evidence(
        self,
        description: str,
        evidence_type: str = "missing",
    ) -> None:
        """
        Record evidence that would be useful but is
        currently unavailable.
        """

        self.evidence.append(
            Evidence(
                evidence_type=evidence_type,
                source="investigation",
                observation=description,
                strength="missing",
            )
        )

    def build(self) -> list[dict[str, Any]]:
        """
        Return serializable evidence records.
        """

        return [
            {
                "evidence_type": item.evidence_type,
                "source": item.source,
                "observation": item.observation,
                "strength": item.strength,
                "timestamp": item.timestamp,
                "data": item.data,
            }
            for item in self.evidence
        ]

    @staticmethod
    def _log_strength(
        log_line: str,
    ) -> str:
        """
        Determine the strength of a log observation.
        """

        upper_line = log_line.upper()

        if "ERROR" in upper_line:
            return "strong"

        if "WARN" in upper_line:
            return "strong"

        if "INFO" in upper_line:
            return "supporting"

        return "supporting"

    @staticmethod
    def _extract_timestamp(
        log_line: str,
    ) -> str | None:
        """
        Extract the timestamp from a log line.
        """

        if not log_line:
            return None

        return log_line.split(
            " ",
            1,
        )[0]