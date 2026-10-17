from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IncidentDB


class IncidentRepository:
    """
    Persistence layer for incidents.

    The repository is responsible only for database operations.
    Business logic remains in the service layer.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
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
    ) -> IncidentDB:

        incident = IncidentDB(
            incident_id=incident_id,
            service=service,
            status=status,
            stage=stage,
            severity=severity,
            description=description,
            start_time=start_time,
            end_time=end_time,
            created_at=created_at,
            metadata_json=metadata,
        )

        self.session.add(incident)

        await self.session.commit()
        await self.session.refresh(incident)

        return incident

    async def get_by_id(
        self,
        incident_id: str,
    ) -> IncidentDB | None:

        result = await self.session.execute(
            select(IncidentDB).where(
                IncidentDB.incident_id == incident_id
            )
        )

        return result.scalar_one_or_none()

    async def update_status(
        self,
        incident_id: str,
        status: str,
    ) -> IncidentDB | None:

        incident = await self.get_by_id(incident_id)

        if incident is None:
            return None

        incident.status = status

        await self.session.commit()
        await self.session.refresh(incident)

        return incident

    async def update_stage(
        self,
        incident_id: str,
        stage: str,
    ) -> IncidentDB | None:

        incident = await self.get_by_id(incident_id)

        if incident is None:
            return None

        incident.stage = stage

        await self.session.commit()
        await self.session.refresh(incident)

        return incident

    async def start_investigation(
        self,
        incident_id: str,
        started_at: datetime,
    ) -> IncidentDB | None:

        incident = await self.get_by_id(incident_id)

        if incident is None:
            return None

        incident.status = "INVESTIGATING"
        incident.stage = "COLLECTING_EVIDENCE"
        incident.started_at = started_at

        await self.session.commit()
        await self.session.refresh(incident)

        return incident

    async def set_report(
        self,
        incident_id: str,
        report: dict[str, Any],
        completed_at: datetime,
    ) -> IncidentDB | None:

        incident = await self.get_by_id(incident_id)

        if incident is None:
            return None

        incident.status = "COMPLETED"
        incident.stage = "REPORT_GENERATED"
        incident.report = report
        incident.completed_at = completed_at

        await self.session.commit()
        await self.session.refresh(incident)

        return incident

    async def set_error(
        self,
        incident_id: str,
        error: str,
        failed_at: datetime,
    ) -> IncidentDB | None:

        incident = await self.get_by_id(incident_id)

        if incident is None:
            return None

        incident.status = "FAILED"
        incident.stage = "FAILED"
        incident.error = error
        incident.failed_at = failed_at

        await self.session.commit()
        await self.session.refresh(incident)

        return incident