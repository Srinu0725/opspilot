FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MCP_HOST=0.0.0.0
ENV OPSPILOT_LIGHTWEIGHT_RAG=1

COPY requirements-mcp.txt .
RUN pip install --no-cache-dir -r requirements-mcp.txt

COPY app ./app
COPY data/runbooks ./data/runbooks
COPY data/metrics ./data/metrics
COPY data/logs ./data/logs
COPY data/deployments ./data/deployments

EXPOSE 8000

CMD ["python", "-m", "app.mcp_server"]
