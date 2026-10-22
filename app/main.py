
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes.incidents import router as incidents_router
from app.events.service import event_queue
from app.events.worker import IncidentWorker
from app.web_api import router as web_api_router


# ---------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    description=(
        "Agentic AI platform for automated "
        "production incident investigation."
    ),
    version="1.2.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://opspilot-frontend-qmhv.onrender.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# API Routers
# ---------------------------------------------------------

# Incident management:
# POST /incidents/investigate
# POST /incidents
# GET  /incidents/{incident_id}
# GET  /incidents/{incident_id}/status

app.include_router(incidents_router)

# Additional API features:
# POST /api/investigate
# GET  /api/metrics/{service}
# POST /api/runbook
# POST /api/mcp/call
# POST /api/chat

app.include_router(web_api_router)


# ---------------------------------------------------------
# Background Incident Worker
# ---------------------------------------------------------

worker = IncidentWorker(event_queue)
worker_task: asyncio.Task | None = None


@app.on_event("startup")
async def start_worker():
    global worker_task

    if worker_task is None or worker_task.done():
        worker_task = asyncio.create_task(worker.start())


@app.on_event("shutdown")
async def stop_worker():
    global worker_task

    worker.stop()

    if worker_task is not None:
        worker_task.cancel()

        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        finally:
            worker_task = None


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
        "version": app.version,
    }
