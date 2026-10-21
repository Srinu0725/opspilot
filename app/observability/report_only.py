
import re
from datetime import datetime
from typing import Any


METRIC_ALIASES = {
    "p95_ms": ("p95", "p95 latency", "api p95 latency"),
    "p99_ms": ("p99", "p99 latency", "api p99 latency"),
    "database_latency_ms": ("database latency", "db latency"),
    "cpu_percent": ("cpu utilization", "cpu usage", "cpu"),
    "memory_percent": ("memory utilization", "memory usage"),
    "error_rate_percent": ("error rate",),
}

SIGNAL_RULES = {
    "latency": ("latency", "slow response", "timeout", "p95", "p99"),
    "database": ("database", "db latency", "slow query", "sql", "deadlock"),
    "errors": ("error", "exception", "5xx", "500"),
    "deployment": ("deployment", "deployed", "release", "rollback"),
    "resources": ("cpu", "memory", "out of memory", "disk usage"),
}


def _reported_service(report: str, fallback: str) -> str:
    match = re.search(
        r"^\s*(?:[-*]\s*)?(?:affected service|service)\s*:\s*`?([a-zA-Z0-9._-]+)",
        report,
        re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1) if match else fallback


def _reported_metrics(report: str) -> dict[str, Any]:
    """Extract labelled metrics, including Markdown tables, without inventing values."""
    metrics = {}

    def parse_number(text: str) -> float | None:
        match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", text)
        if not match:
            return None
        try:
            return float(match.group(0).replace(",", ""))
        except ValueError:
            return None

    for line in report.splitlines():
        cells = (
            [cell.strip() for cell in line.strip().strip("|").split("|")]
            if "|" in line
            else []
        )
        label = cells[0].lower() if cells else line.lower()

        for key, aliases in METRIC_ALIASES.items():
            if not any(alias in label for alias in aliases):
                continue

            baseline = None
            current = None
            reported_change = None

            # Markdown table: Metric | Baseline | Current | Change
            if len(cells) >= 3:
                baseline = parse_number(cells[1])
                current = parse_number(cells[2])

                if len(cells) >= 4:
                    reported_change = parse_number(cells[3])

            else:
                value = parse_number(line)
                if value is None:
                    continue

                if "baseline" in line.lower() or "historical" in line.lower():
                    baseline = value
                elif any(
                    word in line.lower()
                    for word in ("current", "observed", "value")
                ):
                    current = value

            if baseline is None and current is None:
                continue

            change = reported_change
            if change is None and current is not None and baseline is not None:
                if baseline != 0:
                    change = round(
                        (current - baseline) / abs(baseline) * 100, 2
                    )

            anomaly = None
            if current is not None and baseline is not None:
                anomaly = (
                    current >= baseline * 1.5
                    if baseline > 0
                    else current > baseline
                )

            metrics[key] = {
                "current": current,
                "baseline": baseline,
                "change_percent": change,
                "anomaly": anomaly,
                "metric_type": (
                    "latency"
                    if "latency" in key or key.startswith("p")
                    else "error_rate"
                    if key == "error_rate_percent"
                    else "cpu"
                    if key == "cpu_percent"
                    else "memory"
                    if key == "memory_percent"
                    else "unknown"
                ),
                "source": "user_uploaded_report",
                "verified": False,
            }

    return metrics



def _reported_timeline(report: str) -> list[dict[str, Any]]:
    """Use only explicitly timestamped lines from the report."""
    events = []

    for line in report.splitlines():
        match = re.search(
            r"\b(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})?)\b",
            line,
        )
        if not match:
            continue

        timestamp = match.group(1)
        description = line.strip().lstrip("-* ").strip()

        if not description:
            continue

        kind = "report"
        lower = description.lower()
        if any(word in lower for word in ("error", "exception", "warn", "log")):
            kind = "log"
        elif "deploy" in lower or "release" in lower:
            kind = "deployment"
        elif any(word in lower for word in ("latency", "metric", "cpu", "memory")):
            kind = "metric"

        events.append({
            "timestamp": timestamp,
            "event_type": kind,
            "description": description,
            "source": "user_uploaded_report",
            "verified": False,
        })

    return events


def build_report_only_investigation(
    service: str,
    incident_report: str,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    report = incident_report[:10000]
    service = _reported_service(report, service)

    metrics = _reported_metrics(report)
    timeline = _reported_timeline(report)
    lower = report.lower()

    signals = [
        signal
        for signal, keywords in SIGNAL_RULES.items()
        if any(keyword in lower for keyword in keywords)
    ]

    recommendations = []
    recommendation_rules = {
        "latency": "Correlate the reported latency symptoms with available service telemetry.",
        "database": "Inspect database query performance and connection-pool telemetry if available.",
        "errors": "Correlate the reported errors with application logs and error-rate telemetry.",
        "deployment": "Compare the reported incident timeline with deployment records if available.",
        "resources": "Check resource utilization using an available telemetry source.",
    }

    for signal in signals:
        recommendations.append(recommendation_rules[signal])

    if not recommendations:
        recommendations.append(
            "Collect additional incident details and relevant operational telemetry."
        )

    hypotheses = []
    if signals:
        hypotheses.append({
            "hypothesis": (
                "The incident may involve: " + ", ".join(signals) + "."
            ),
            "support": [
                "The uploaded report mentions these symptoms; they have not been independently verified."
            ],
            "confidence": {
                "score": 0,
                "level": "UNVERIFIED",
                "reasons": [
                    "The report is the source of these clues.",
                    "No independent telemetry was queried in report-only mode.",
                ],
                "limitations": [
                    "The report alone does not establish root cause."
                ],
            },
        })

    metric_analysis = {
        "metrics": metrics,
        "source": "user_uploaded_report",
        "verified": False,
    }

    missing_evidence = [
        "Independent metrics, logs, and deployment records were not queried in report-only mode."
    ]

    for key in METRIC_ALIASES:
        if key not in metrics:
            missing_evidence.append(
                f"{key} was not explicitly supplied in the uploaded report."
            )

    runbook_context = []
    observed_anomalies = [
    {
        "metric": key,
        "current": value["current"],
        "baseline": value["baseline"],
        "change_percent": value["change_percent"],
    }
    for key, value in metrics.items()
    if value.get("anomaly") is True
]

    summary = {
        "incident": (
            "Uploaded incident report analyzed; reported symptoms are unverified."
            if signals
            else "Report received. More incident details are needed."
        ),
        "observed_anomalies": observed_anomalies,
        "key_logs": [],
        "supporting_evidence": [],
    }

    rca = {
        "hypotheses": hypotheses,
        "strong_evidence": [],
        "limitations": [
            "Report statements are unverified and are not independent telemetry."
        ],
        "missing_evidence": missing_evidence,
        "recommendations": recommendations,
        "runbook_guidance": runbook_context,
        "reported_signals": [
            {
                "signal": signal,
                "source": "user_uploaded_report",
                "verified": False,
            }
            for signal in signals
        ],
        "reported_incident_context": {
            "source": "user_uploaded_report",
            "content": report,
        },
    }

    final_report = {
        "report_version": "1.0",
        "incident": summary["incident"],
        "affected_service": service,
        "investigation_window": {"start": start_time, "end": end_time},
        "impact": {
            "latency_degradation": None,
            "error_rate_degradation": None,
            "database_degradation": None,
        },
        "timeline": timeline,
        "observed_evidence": {
            "anomalies": [],
            "key_logs": [],
            "deployment": None,
            "strong_evidence": [],
            "supporting_evidence": [],
        },
        "root_cause_hypotheses": hypotheses,
        "limitations": rca["limitations"],
        "missing_evidence": missing_evidence,
        "runbook_guidance": [],
        "recommended_next_steps": recommendations,
    }

    return {
        "service": service,
        "investigation_window": {"start": start_time, "end": end_time},
        "baseline_metrics": {},
        "metrics": {},
        "metric_analysis": metric_analysis,
        "logs": [],
        "deployment": None,
        "timeline": timeline,
        "evidence": [],
        "runbook_context": [],
        "investigation_summary": summary,
        "reported_incident_context": {
            "source": "user_uploaded_report",
            "content": report,
        },
        "rca_analysis": rca,
        "final_report": final_report,
    }
