from datetime import datetime, timezone
from typing import Any

from app.db.session import AsyncSessionLocal
from app.incidents.repository import IncidentRepository


class IncidentService:
    """
    Application service for incident lifecycle operations.

    Business logic lives here.
    Database persistence is delegated to IncidentRepository.
    """

    async def create_incident(
        self,
        incident_id: str,
        service: str,
        status: str,
        stage: str,
        severity: str | None,
        description: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
        created_at: datetime,
        metadata: dict[str, Any] | None = None,
    ):
        async with AsyncSessionLocal() as session:
            repository = IncidentRepository(session)

            return await repository.create(
                incident_id=incident_id,
                service=service,
                status=status,
                stage=stage,
                severity=severity,
                description=description,
                start_time=start_time,
                end_time=end_time,
                created_at=created_at,
                metadata=metadata,
            )

    async def get_incident(
        self,
        incident_id: str,
    ):
        async with AsyncSessionLocal() as session:
            repository = IncidentRepository(session)

            return await repository.get_by_id(
                incident_id
            )

    async def start_investigation(
        self,
        incident_id: str,
    ):
        async with AsyncSessionLocal() as session:
            repository = IncidentRepository(session)

            return await repository.start_investigation(
                incident_id=incident_id,
                started_at=datetime.now(timezone.utc),
            )

    async def update_stage(
        self,
        incident_id: str,
        stage: str,
    ):
        async with AsyncSessionLocal() as session:
            repository = IncidentRepository(session)

            return await repository.update_stage(
                incident_id=incident_id,
                stage=stage,
            )

    async def set_report(
        self,
        incident_id: str,
        report: dict[str, Any],
    ):
        async with AsyncSessionLocal() as session:
            repository = IncidentRepository(session)

            return await repository.set_report(
                incident_id=incident_id,
                report=report,
                completed_at=datetime.now(timezone.utc),
            )

    async def set_error(
        self,
        incident_id: str,
        error: str,
    ):
        async with AsyncSessionLocal() as session:
            repository = IncidentRepository(session)

            return await repository.set_error(
                incident_id=incident_id,
                error=error,
                failed_at=datetime.now(timezone.utc),
            )


incident_store = IncidentService()