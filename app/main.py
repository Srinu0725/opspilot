
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.config import settings
from app.api.routes.incidents import router as incidents_router
from app.events.service import event_queue
from app.events.worker import IncidentWorker


# ---------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    description=(
        "Agentic AI platform for automated "
        "production incident investigation."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://opspilot-frontend-qmhv.onrender.com",
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Router
# ---------------------------------------------------------

app.include_router(incidents_router)


# ---------------------------------------------------------
# Background Worker
# ---------------------------------------------------------

worker = IncidentWorker(event_queue)

worker_task: asyncio.Task | None = None


@app.on_event("startup")
async def start_worker():
    global worker_task

    worker_task = asyncio.create_task(worker.start())


@app.on_event("shutdown")
async def stop_worker():
    worker.stop()

    if worker_task:
        worker_task.cancel()

        try:
            await worker_task
        except asyncio.CancelledError:
            pass


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
    }
