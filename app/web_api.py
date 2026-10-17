
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.tools.investigation import investigate_incident
from app.tools.metrics import get_service_metrics
from app.rag.retriever import search_runbook

app = FastAPI(title="OpsPilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://opspilot-frontend-qmhv.onrender.com",
],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class InvestigationRequest(BaseModel):
    service: str = Field(default="payment-api", min_length=1, max_length=100)


class RunbookRequest(BaseModel):
    service: str = Field(default="payment-api", min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=3, ge=1, le=10)


@app.get("/health")
def health():
    return {"status": "ok", "service": "OpsPilot API"}


@app.post("/api/investigate")
def investigate(request: InvestigationRequest):
    try:
        return investigate_incident(request.service)
    except Exception:
        raise HTTPException(status_code=500, detail="Investigation failed. Check server logs.")


@app.get("/api/metrics/{service}")
def metrics(service: str):
    try:
        return get_service_metrics(service)
    except Exception:
        raise HTTPException(status_code=500, detail="Metrics retrieval failed. Check server logs.")


@app.post("/api/runbook")
def runbook(request: RunbookRequest):
    try:
        return search_runbook(request.service, request.query, request.top_k)
    except Exception:
        raise HTTPException(status_code=500, detail="Runbook search failed. Check server logs.")
