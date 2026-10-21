from typing import Any

from app.observability.confidence import ConfidenceCalibrator


class RCAEngine:
    """
    Deterministic RCA preparation layer.

    This layer does NOT claim causality by itself.

    It:
    - identifies relationships between evidence sources
    - builds root-cause hypotheses
    - calibrates confidence using available evidence
    - identifies missing evidence
    - produces investigation recommendations

    The confidence score represents evidence-supported confidence,
    not the statistical probability that a hypothesis is correct.
    """

    def __init__(self):
        self.confidence_calibrator = ConfidenceCalibrator()

    def analyze(
        self,
        investigation: dict[str, Any],
    ) -> dict[str, Any]:

        summary = investigation.get(
            "investigation_summary",
            {},
        )
        reported_incident_context = investigation.get(
            "reported_incident_context"
        )

        reported_incident_text = ""

        if isinstance(reported_incident_context, dict):
            reported_incident_text = str(
                reported_incident_context.get("content", "")
            )[:10000]

        anomalies = summary.get(
            "observed_anomalies",
            [],
        )

        logs = summary.get(
            "key_logs",
            [],
        )

        deployment = summary.get(
            "deployment_correlation",
        )

        strong_evidence = summary.get(
            "strong_evidence",
            [],
        )

        missing_evidence = summary.get(
            "missing_evidence",
            [],
        )

        runbook_guidance = summary.get(
            "runbook_guidance",
            [],
        )

        # ---------------------------------------------------------
        # Identify database-related evidence
        # ---------------------------------------------------------

        database_anomalies = [
            item
            for item in anomalies
            if item.get("metric_type")
            == "database_latency"
        ]

        database_logs = [
            log
            for log in logs
            if (
                "database" in log.lower()
                or "payment_lookup" in log.lower()
            )
        ]

        # ---------------------------------------------------------
        # Identify latency evidence
        # ---------------------------------------------------------

        latency_anomalies = [
            item
            for item in anomalies
            if item.get("metric_type")
            == "latency"
        ]

        # ---------------------------------------------------------
        # Identify deployment/query correlation
        # ---------------------------------------------------------

        deployment_query_change = False

        if deployment:

            for change in deployment.get(
                "changes",
                [],
            ):

                change_text = str(change).lower()

                if (
                    "query" in change_text
                    or "payment" in change_text
                    or "database" in change_text
                ):
                    deployment_query_change = True
                    break

        # ---------------------------------------------------------
        # Build hypotheses
        # ---------------------------------------------------------

        hypotheses = []

        if (
            database_anomalies
            and database_logs
            and deployment_query_change
        ):

            hypotheses.append(
                {
                    "hypothesis": (
                        "A database/query performance regression "
                        "associated with the recent deployment "
                        "is a likely contributor to the incident."
                    ),
                    "support": [
                        "Database latency is anomalous.",
                        "Application logs show repeated slow "
                        "payment_lookup queries.",
                        "The recent deployment changed the "
                        "payment lookup query.",
                    ],
                    "confidence": "medium",
                }
            )

        elif (
            database_anomalies
            and database_logs
        ):

            hypotheses.append(
                {
                    "hypothesis": (
                        "Database/query performance degradation "
                        "is a likely contributor to the incident."
                    ),
                    "support": [
                        "Database latency is anomalous.",
                        "Application logs show slow database "
                        "queries.",
                    ],
                    "confidence": "medium",
                }
            )

        elif latency_anomalies:

            hypotheses.append(
                {
                    "hypothesis": (
                        "The service is experiencing a significant "
                        "latency degradation."
                    ),
                    "support": [
                        "Latency metrics are anomalous.",
                    ],
                    "confidence": "low",
                }
            )

        # ---------------------------------------------------------
        # Identify limitations
        # ---------------------------------------------------------

        limitations = []

        if any(
            "EXPLAIN ANALYZE" in item
            for item in missing_evidence
        ):
            limitations.append(
                "Query execution plan is unavailable."
            )

        if any(
            "index" in item.lower()
            for item in missing_evidence
        ):
            limitations.append(
                "Index usage information is unavailable."
            )

        if any(
            "lock" in item.lower()
            for item in missing_evidence
        ):
            limitations.append(
                "Database lock contention information "
                "is unavailable."
            )

        # ---------------------------------------------------------
        # Recommended diagnostics
        # ---------------------------------------------------------

        recommendations = [
            (
                "Compare the affected payment_lookup query "
                "execution plan between the current and previous "
                "deployment."
            ),
            (
                "Check whether the expected database indexes "
                "are being used."
            ),
            (
                "Inspect database I/O, CPU, and lock contention."
            ),
        ]        
        # ---------------------------------------------------------
        # Use uploaded report to guide diagnostic recommendations
        # These are reported signals, not verified evidence.
        # ---------------------------------------------------------

        report_text = reported_incident_text.lower()

        reported_signal_checks = {
            "latency": (
                ("latency", "slow response", "p95", "p99", "timeout"),
                "Validate reported latency or timeout symptoms against service metrics.",
            ),
            "database": (
                ("database", "sql", "slow query", "deadlock", "connection pool"),
                "Check database latency, query performance, and connection-pool metrics.",
            ),
            "errors": (
                ("error", "exception", "5xx", "500", "failed request"),
                "Correlate reported errors with application logs and error-rate metrics.",
            ),
            "deployment": (
                ("deployment", "deployed", "release", "rollback", "new version"),
                "Compare the reported incident timeline with recent deployment records.",
            ),
            "resources": (
                ("cpu", "memory", "out of memory", "oom", "disk usage"),
                "Validate reported resource-pressure symptoms against infrastructure metrics.",
            ),
        }

        reported_signals = []

        for signal, (keywords, recommendation) in reported_signal_checks.items():
            if any(keyword in report_text for keyword in keywords):
                reported_signals.append({
                    "signal": signal,
                    "source": "user_uploaded_report",
                    "verified": False,
                })

                if recommendation not in recommendations:
                    recommendations.append(recommendation)


        if deployment_query_change:

            recommendations.append(
                (
                    "Review the query changes introduced by "
                    f"{deployment.get('version', 'the recent deployment')}."
                )
            )

        # ---------------------------------------------------------
        # Confidence calibration
        # ---------------------------------------------------------
        #
        # The initial "confidence" field above is retained for
        # backward compatibility.
        #
        # The calibrated confidence below is the authoritative
        # evidence-based confidence assessment.
        # ---------------------------------------------------------

        calibrated_hypotheses = []

        for hypothesis in hypotheses:

            confidence = (
                self.confidence_calibrator.calibrate(
                    hypothesis=hypothesis,
                    investigation=investigation,
                )
            )

            calibrated_hypotheses.append(
                {
                    **hypothesis,
                    "confidence": confidence,
                }
            )
        # ---------------------------------------------------------
        # Return structured RCA
        # ---------------------------------------------------------

        return {
            "hypotheses": calibrated_hypotheses,
            "strong_evidence": strong_evidence,
            "limitations": limitations,
            "missing_evidence": missing_evidence,
            "recommendations": recommendations,
            "reported_signals": reported_signals,
            "runbook_guidance": runbook_guidance,
            "reported_incident_context": (
                {
                    "source": "user_uploaded_report",
                    "content": reported_incident_text,
                }
                if reported_incident_text
                else None
            ),
        }
