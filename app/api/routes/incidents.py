from datetime import datetime
from pathlib import Path
from typing import Any
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel, Field

from app.events.models import IncidentEvent
from app.events.service import event_queue
from app.incidents.service import incident_store
from app.tools.investigation import investigate_incident
# from app.observability.investigator import investigate_incident


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
# Constants
# =========================================================


MAX_REPORT_SIZE = 1_000_000

ALLOWED_REPORT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".log",
}


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


async def read_incident_report(
    file: UploadFile,
) -> str:
    """
    Read and validate an uploaded text-based incident report.

    The file is processed in memory and is not saved to disk.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A report file is required.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_REPORT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported report format. "
                "Upload a .txt, .md, .csv, or .log file."
            ),
        )

    # Read at most MAX_REPORT_SIZE + 1 bytes so that an oversized
    # upload can be rejected without reading the entire file.
    raw_content = await file.read(
        MAX_REPORT_SIZE + 1
    )

    if len(raw_content) > MAX_REPORT_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Report must not exceed 1 MB.",
        )

    try:
        report_text = raw_content.decode("utf-8-sig").strip()
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Report must be UTF-8 encoded text.",
        ) from exc

    if not report_text:
        raise HTTPException(
            status_code=400,
            detail="The uploaded report is empty.",
        )

    return report_text


# =========================================================
# Investigate Incident From Uploaded File
# =========================================================

@router.post("/investigate")
async def investigate_uploaded_report(
    service: str = Form(
        ...,
        min_length=1,
        description="Affected service name, e.g. payment-api.",
    ),
    file: UploadFile = File(
        ...,
        description="Incident report in TXT, MD, CSV, or LOG format.",
    ),
):
    """Investigate an uploaded report and persist its lifecycle."""

    incident_id = str(uuid4())
    now = datetime.now(timezone.utc)

    try:
        report_text = await read_incident_report(file)

        # 1. Persist the initial incident.
        await incident_store.create_incident(
            incident_id=incident_id,
            service=service.strip(),
            status="CREATED",
            stage="CREATED",
            severity="unknown",
            description=f"Investigation from uploaded report: {file.filename}",
            start_time=None,
            end_time=None,
            created_at=now,
            metadata={
                "source": "user_uploaded_report",
                "file_name": file.filename,
                "report_length": len(report_text),
            },
        )

        # 2. Mark the investigation as running.
        await incident_store.start_investigation(incident_id)

        # 3. Run the existing investigation.
        result = investigate_incident(
            service=service.strip(),
            incident_report=report_text,
        )

        result["incident_id"] = incident_id
        result["incident_report"] = {
            "file_name": file.filename,
            "report_received": True,
            "report_length": len(report_text),
            "source": "user_uploaded_report",
            "verified": False,
        }

        # 4. Persist the final report.
        saved = await incident_store.set_report(
            incident_id=incident_id,
            report=result,
        )

        if saved is None:
            raise RuntimeError(
                f"Incident {incident_id} disappeared before report persistence."
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        import logging

        logging.getLogger(__name__).exception(
            "Uploaded incident investigation failed; incident_id=%s",
            incident_id,
        )

        # Mark the record as failed if it was created successfully.
        try:
            existing = await incident_store.get_incident(incident_id)
            if existing is not None:
                await incident_store.set_error(
                    incident_id=incident_id,
                    error=str(exc)[:2000],
                )
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to persist investigation failure; incident_id=%s",
                incident_id,
            )

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Investigation failed. Check server logs.",
                "incident_id": incident_id,
            },
        ) from exc

    finally:
        await file.close()


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

    # Create incident event.
    event = IncidentEvent.create(
        service=request.service,
        description=request.description,
        severity=request.severity,
        start_time=request.start_time,
        end_time=request.end_time,
        metadata=request.metadata,
    )

    # Parse timestamps for PostgreSQL.
    start_time = parse_datetime(
        event.start_time
    )

    end_time = parse_datetime(
        event.end_time
    )

    # Persist initial incident state.
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

    # Publish event to queue.
    await event_queue.publish(
        event.to_dict()
    )

    # Return immediately.
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
