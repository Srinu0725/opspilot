
import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from pydantic import BaseModel, Field

from app.rag.retriever import search_runbook
from app.tools.metrics import get_service_metrics


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opspilot.api")

MCP_SERVER_URL = os.getenv(
    "OPSPILOT_MCP_URL",
    "https://opspilot-odgn.onrender.com/mcp",
)

ALLOWED_MCP_TOOLS = {
    "investigate_service",
    "get_metrics",
    "find_runbook_guidance",
}

MAX_REPORT_SIZE = 1_000_000

ALLOWED_REPORT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".log",
}


# ---------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------

app = FastAPI(
    title="OpsPilot API",
    version="1.1.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://opspilot-frontend-qmhv.onrender.com",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )
    history: list[dict[str, str]] = Field(
        default_factory=list,
    )
    context: dict | None = None


class RunbookRequest(BaseModel):
    service: str = Field(
        default="payment-api",
        min_length=1,
        max_length=100,
    )
    query: str = Field(
        min_length=1,
        max_length=500,
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
    )


class MCPToolCallRequest(BaseModel):
    tool: str = Field(
        min_length=1,
        max_length=100,
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict,
    )


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "OpsPilot API",
    }


# ---------------------------------------------------------
# Upload Incident Report — Temporary Upload Test
# ---------------------------------------------------------

@app.post("/api/investigate")
async def investigate(
    service: str = Form(
        default="payment-api",
        min_length=1,
        max_length=100,
    ),
    file: UploadFile = File(...),
):
    """
    Temporary upload test.

    Receives the file and returns its metadata.
    Investigation and report parsing are intentionally
    not performed in this stage.
    """

    try:
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
                    "Unsupported file type. Upload a "
                    ".txt, .md, .csv, or .log file."
                ),
            )

        # Read at most 1 MB plus one byte.
        content = await file.read(MAX_REPORT_SIZE + 1)

        if len(content) > MAX_REPORT_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Report must not exceed 1 MB.",
            )

        if not content.strip():
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        logger.info(
            "File received: service=%s, filename=%s, bytes=%d",
            service,
            file.filename,
            len(content),
        )

        return {
            "success": True,
            "service": service.strip(),
            "file_name": file.filename,
            "file_size_bytes": len(content),
            "message": "File received by the backend successfully.",
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("File upload failed")
        raise HTTPException(
            status_code=500,
            detail="File upload failed. Check API server logs.",
        ) from exc

    finally:
        await file.close()


# ---------------------------------------------------------
# Metrics
# ---------------------------------------------------------

@app.get("/api/metrics/{service}")
def metrics(service: str):
    try:
        return get_service_metrics(service)

    except Exception as exc:
        logger.exception("Metrics retrieval failed")
        raise HTTPException(
            status_code=500,
            detail="Metrics retrieval failed. Check server logs.",
        ) from exc


# ---------------------------------------------------------
# Runbook Search
# ---------------------------------------------------------

@app.post("/api/runbook")
def runbook(request: RunbookRequest):
    try:
        return search_runbook(
            request.service,
            request.query,
            request.top_k,
        )

    except Exception as exc:
        logger.exception("Runbook search failed")
        raise HTTPException(
            status_code=500,
            detail="Runbook search failed. Check server logs.",
        ) from exc


# ---------------------------------------------------------
# MCP Tool Calls
# ---------------------------------------------------------

@app.post("/api/mcp/call")
async def call_mcp_tool(request: MCPToolCallRequest):
    if request.tool not in ALLOWED_MCP_TOOLS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported MCP tool: {request.tool}",
        )

    try:
        logger.info("Calling MCP tool: %s", request.tool)

        async with streamablehttp_client(
            MCP_SERVER_URL
        ) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(
                read_stream,
                write_stream,
            ) as session:
                await session.initialize()

                result = await session.call_tool(
                    request.tool,
                    request.arguments,
                )

                content = []

                for item in result.content or []:
                    if getattr(item, "type", None) == "text":
                        content.append({
                            "type": "text",
                            "text": item.text,
                        })

                structured_content = getattr(
                    result,
                    "structuredContent",
                    None,
                )

                return {
                    "tool": request.tool,
                    "is_error": bool(result.isError),
                    "content": content,
                    "structured_content": structured_content,
                }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "MCP tool call failed: %s",
            request.tool,
        )
        raise HTTPException(
            status_code=502,
            detail=f"MCP tool call failed: {exc}",
        ) from exc


# ---------------------------------------------------------
# Chat
# ---------------------------------------------------------

@app.post("/api/chat")
def chat(request: ChatRequest):
    api_key = (
        os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY")
    )

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key is not configured.",
        )

    history = request.history[-10:]
    context = request.context or {}

    prompt = f"""
You are OpsPilot, an incident investigation assistant for software engineers.

Answer the user's question using the conversation and investigation evidence below.

Rules:
- Ground conclusions in the supplied evidence.
- Never invent metrics, logs, deployments, or tool results.
- Clearly distinguish a likely cause from a confirmed root cause.
- If evidence is missing, say what is needed to verify the hypothesis.
- Give concise, practical troubleshooting steps.
- Do not claim to have executed an action or called a tool.
- If the user asks a follow-up, answer it directly using the prior investigation.

Investigation context:
{json.dumps(context, ensure_ascii=False)[:18000]}

Recent conversation:
{json.dumps(history, ensure_ascii=False)[:10000]}

Current user question:
{request.question}
"""

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=os.getenv(
                "GEMINI_MODEL",
                "gemini-3.6-flash",
            ),
            contents=prompt,
        )

        answer = response.text

        if not answer:
            raise ValueError(
                "Gemini returned an empty response."
            )

        return {"answer": answer}

    except Exception as exc:
        logger.exception("Chat response generation failed")
        raise HTTPException(
            status_code=502,
            detail=(
                "OpsPilot could not generate a response. "
                "Check the API server logs."
            ),
        ) from exc
