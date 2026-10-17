from typing import Any

from app.incidents.state import IncidentState


class IncidentStore:
    """
    In-memory incident store.

    This is intentionally simple for local development.

    Later this can be replaced with PostgreSQL without changing
    the event or investigation layers.
    """

    def __init__(self):
        self._incidents: dict[
            str,
            IncidentState,
        ] = {}

    def create(
        self,
        incident_id: str,
        service: str,
        severity: str = "unknown",
        description: str = "",
        start_time: str | None = None,
        end_time: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> IncidentState:

        incident = IncidentState(
            incident_id=incident_id,
            service=service,
            severity=severity,
            description=description,
            start_time=start_time,
            end_time=end_time,
            metadata=metadata or {},
        )

        self._incidents[incident_id] = incident

        return incident

    def get(
        self,
        incident_id: str,
    ) -> IncidentState | None:

        return self._incidents.get(
            incident_id
        )

    def update_status(
        self,
        incident_id: str,
        status: str,
    ) -> IncidentState | None:

        incident = self.get(
            incident_id
        )

        if incident is None:
            return None

        incident.status = status

        return incident

    def set_report(
        self,
        incident_id: str,
        report: dict[str, Any],
    ) -> IncidentState | None:

        incident = self.get(
            incident_id
        )

        if incident is None:
            return None

        incident.report = report
        incident.status = "COMPLETED"

        return incident

    def set_error(
        self,
        incident_id: str,
        error: str,
    ) -> IncidentState | None:

        incident = self.get(
            incident_id
        )

        if incident is None:
            return None

        incident.error = error
        incident.status = "FAILED"

        return incident