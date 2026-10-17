# OpsPilot

**Agentic AI for production incident investigation and root-cause analysis.**

OpsPilot investigates service incidents by correlating metrics, application logs, recent deployments, and runbook guidance. It produces evidence-backed root-cause hypotheses, identifies missing evidence, and recommends the next steps for an engineer.

OpsPilot currently uses a deterministic investigation and RCA pipeline with lightweight keyword-based runbook retrieval in its Docker deployment. Its observability inputs are local sample data, not live production integrations.

## The Problem

When an API becomes slow, engineers often have to inspect multiple sources independently:

- Metrics: API latency, database latency, CPU, memory, and request throughput
- Logs: slow queries, errors, and application behavior
- Deployments: recent releases and potentially relevant code changes
- Runbooks: operational procedures and troubleshooting guidance

OpsPilot brings these signals into one structured investigation.

## How It Works

```text
Incident / Service
       |
       v
OpsPilot MCP Server
       |
       v
Collect Observability Evidence
  |         |          |
Metrics    Logs    Deployments
  |         |          |
  +---------+----------+
            |
            v
       Analyze Changes
            |
            v
     Retrieve Runbook Guidance
            |
            v
     Correlate Supporting Evidence
            |
            v
     Root-Cause Hypotheses
            |
            v
  Missing Evidence + Next Steps
```

The investigation is read-only. OpsPilot recommends actions but does not automatically change production systems.

## MCP Tools

OpsPilot exposes these tools through the Model Context Protocol (MCP) using Streamable HTTP.

| Tool | Purpose |
|---|---|
| `investigate_service` | Runs the structured investigation for a service and returns evidence, hypotheses, limitations, and recommendations. |
| `get_metrics` | Retrieves observability metrics for a service. |
| `find_runbook_guidance` | Searches runbook sections relevant to a troubleshooting query. |

MCP endpoint: `/mcp`

## Example Investigation

For the sample `payment-api` service, OpsPilot correlates:

- Anomalous API and database latency
- Application logs showing slow `payment_lookup` queries
- A recent deployment that changed the payment lookup query
- Relevant runbook guidance

The system may identify a database/query performance regression associated with the deployment as a likely contributor. It also reports missing evidence, such as the database execution plan and index-usage information.

This is a hypothesis based on the included sample data, not a verified production root cause.

## Technology Stack

- **Language:** Python
- **MCP:** MCP Python SDK, Streamable HTTP
- **Investigation:** Metrics analysis, log correlation, deployment analysis, evidence collection, and deterministic RCA
- **Runbook retrieval:** Lightweight keyword matching in the Docker deployment
- **Local infrastructure:** Docker
- **Optional local application components:** FastAPI, PostgreSQL, and the existing semantic RAG implementation

## Project Structure

```text
OpsPilot/
├── app/
│   ├── mcp_server.py
│   ├── tools/
│   ├── observability/
│   └── rag/
├── data/
│   ├── deployments/
│   ├── logs/
│   ├── metrics/
│   └── runbooks/
├── tests/
├── Dockerfile
├── requirements-mcp.txt
├── requirements.txt
├── docker-compose.yml
└── test_mcp_client.py
```

## Run with Docker

Prerequisites: Docker Desktop and Git.

Build the MCP image:

```bash
docker build -t opspilot-mcp:local .
```

Start the server:

```bash
docker run -d --name opspilot-mcp \
  -p 8002:8000 \
  opspilot-mcp:local
```

The MCP endpoint will be available locally at:

```text
http://localhost:8002/mcp
```

Check the server logs:

```bash
docker logs opspilot-mcp
```

Stop and remove the test container when finished:

```bash
docker stop opspilot-mcp
docker rm opspilot-mcp
```

## Connect an MCP Client

Configure your MCP-compatible client to connect to the Streamable HTTP endpoint:

```text
http://localhost:8002/mcp
```

For a local Python client, install the MCP SDK and run:

```bash
pip install "mcp==1.30.0"
python test_mcp_client.py
```

The included test client lists the available tools and exercises runbook retrieval and incident investigation. Ensure the client URL matches the port used by your container.

## Configuration and Security

- Never commit `.env` or API keys.
- `.env.example` provides a configuration template.
- The Docker deployment uses local sample data and does not require a production database connection.
- Do not expose the PostgreSQL development database publicly.
- The investigation pipeline is read-only and does not perform automated remediation.

## Current Limitations

- Metrics, logs, and deployment information are supplied as local sample files.
- Runbook retrieval in the Docker image uses keyword matching; it is not semantic retrieval.
- Root-cause findings are hypotheses and should be validated by an engineer.
- Database query plans, index usage, locks, and other unavailable telemetry cannot be inferred reliably from the sample data.
- No live integrations with production observability platforms are currently claimed.

## Roadmap

- Integrate live observability data sources.
- Improve runbook retrieval and evidence ranking.
- Add richer time-window correlation and investigation evaluation.
- Support configurable service adapters.
- Add human-approved remediation workflows.

## License

No license has been specified yet. Contact the repository owner before reusing this project.
