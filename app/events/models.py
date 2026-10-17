from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


@dataclass
class IncidentEvent:
    """
    Event representing a production incident.

    This event is intentionally independent of the
    observability implementation.
    """

    event_id: str
    event_type: str
    service: str

    start_time: str | None = None
    end_time: str | None = None

    severity: str = "unknown"

    description: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=lambda:
            datetime.utcnow().isoformat() + "Z"
    )

    @classmethod
    def create(
        cls,
        service: str,
        description: str,
        severity: str = "unknown",
        start_time: str | None = None,
        end_time: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "IncidentEvent":

        return cls(
            event_id=str(uuid.uuid4()),
            event_type="incident.created",
            service=service,
            start_time=start_time,
            end_time=end_time,
            severity=severity,
            description=description,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "service": self.service,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "severity": self.severity,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }