from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.events.models import IncidentEvent
from app.events.service import event_queue
from app.incidents.service import incident_store


router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
)


# =========================================================
# Request Models
# =========================================================


class CreateIncidentRequest(BaseModel):
    """
    Request body for creating a new production incident.
    """

    service: str = Field(
        ...,
        min_length=1,
        description="Affected service name.",
    )

    description: str = Field(
        ...,
        min_length=1,
        description="Description of the incident.",
    )

    severity: str = Field(
        default="unknown",
        description="Incident severity.",
    )

    start_time: str | None = Field(
        default=None,
        description="Start of the investigation window.",
    )

    end_time: str | None = Field(
        default=None,
        description="End of the investigation window.",
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional incident metadata.",
    )


# =========================================================
# Helpers
# =========================================================


def parse_datetime(
    value: str | None,
) -> datetime | None:
    """
    Convert an ISO-8601 timestamp string into a datetime.

    Returns None when no timestamp is provided.
    """

    if value is None:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid datetime format: {value}",
        ) from exc


# =========================================================
# Create Incident
# =========================================================


@router.post(
    "",
    status_code=202,
)
async def create_incident(
    request: CreateIncidentRequest,
):
    """
    Create a new incident and enqueue it for investigation.

    Flow:

        API
          ↓
        PostgreSQL
          ↓
        Incident Event
          ↓
        asyncio Queue
          ↓
        Background Worker
    """

    # -----------------------------------------------------
    # Create incident event
    # -----------------------------------------------------

    event = IncidentEvent.create(
        service=request.service,
        description=request.description,
        severity=request.severity,
        start_time=request.start_time,
        end_time=request.end_time,
        metadata=request.metadata,
    )

    # -----------------------------------------------------
    # Parse timestamps for PostgreSQL
    # -----------------------------------------------------

    start_time = parse_datetime(
        event.start_time
    )

    end_time = parse_datetime(
        event.end_time
    )

    # -----------------------------------------------------
    # Persist initial incident state
    # -----------------------------------------------------

    incident = await incident_store.create_incident(
        incident_id=event.event_id,
        service=event.service,
        status="CREATED",
        stage="CREATED",
        severity=event.severity,
        description=event.description,
        start_time=start_time,
        end_time=end_time,
        created_at=parse_datetime(event.created_at),
        metadata=event.metadata,
    )

    # -----------------------------------------------------
    # Publish event to queue
    # -----------------------------------------------------

    await event_queue.publish(
        event.to_dict()
    )

    # -----------------------------------------------------
    # Return immediately
    # -----------------------------------------------------

    return {
        "incident_id": incident.incident_id,
        "status": incident.status,
        "stage": incident.stage,
        "message": (
            "Incident created and queued "
            "for investigation."
        ),
    }


# =========================================================
# Get Incident Status
# =========================================================


@router.get(
    "/{incident_id}/status",
)
async def get_incident_status(
    incident_id: str,
):
    """
    Return lightweight incident lifecycle information.

    Possible statuses:

        CREATED
        INVESTIGATING
        COMPLETED
        FAILED
    """

    incident = await incident_store.get_incident(
        incident_id
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    return {
        "incident_id": incident.incident_id,
        "service": incident.service,
        "status": incident.status,
        "stage": incident.stage,
        "created_at": incident.created_at,
        "started_at": incident.started_at,
        "completed_at": incident.completed_at,
        "failed_at": incident.failed_at,
        "error": incident.error,
    }


# =========================================================
# Get Complete Incident
# =========================================================


@router.get(
    "/{incident_id}",
)
async def get_incident(
    incident_id: str,
):
    """
    Retrieve the complete persisted incident.

    Once the investigation is completed, the response
    also contains the final incident report.
    """

    incident = await incident_store.get_incident(
        incident_id
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found.",
        )

    return {
        "incident_id": incident.incident_id,
        "service": incident.service,
        "status": incident.status,
        "stage": incident.stage,
        "severity": incident.severity,
        "description": incident.description,
        "start_time": incident.start_time,
        "end_time": incident.end_time,
        "created_at": incident.created_at,
        "started_at": incident.started_at,
        "completed_at": incident.completed_at,
        "failed_at": incident.failed_at,
        "error": incident.error,
        "metadata": incident.metadata_json,
        "report": incident.report,
    }