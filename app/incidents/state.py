from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class IncidentState:
    """
    In-memory/domain representation of an incident.

    This class represents the lifecycle state of an incident
    inside the application. Persistent storage is handled
    separately by IncidentDB and IncidentRepository.
    """

    incident_id: str
    service: str

    status: str = "CREATED"
    stage: str = "CREATED"

    severity: str | None = None
    description: str | None = None

    start_time: str | None = None
    end_time: str | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None

    report: dict[str, Any] | None = None
    error: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def start_investigation(self) -> None:
        self.status = "INVESTIGATING"
        self.stage = "COLLECTING_EVIDENCE"
        self.started_at = datetime.now(timezone.utc)

    def update_stage(self, stage: str) -> None:
        self.stage = stage

    def complete(
        self,
        report: dict[str, Any],
    ) -> None:
        self.status = "COMPLETED"
        self.stage = "REPORT_GENERATED"
        self.report = report
        self.completed_at = datetime.now(timezone.utc)

    def fail(
        self,
        error: str,
    ) -> None:
        self.status = "FAILED"
        self.stage = "FAILED"
        self.error = error
        self.failed_at = datetime.now(timezone.utc)