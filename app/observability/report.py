from typing import Any


class IncidentReportBuilder:
    """
    Builds the canonical OpsPilot incident report.

    This is the final structured representation of an
    investigation before it is presented through the API,
    agent, CLI, or future UI.

    The builder does not create new evidence.
    It only organizes information already produced by
    the investigation and RCA layers.
    """

    def build(
        self,
        investigation: dict[str, Any],
    ) -> dict[str, Any]:

        service = investigation.get(
            "service",
            "unknown",
        )

        investigation_window = investigation.get(
            "investigation_window",
            {},
        )

        summary = investigation.get(
            "investigation_summary",
            {},
        )

        rca = investigation.get(
            "rca_analysis",
            {},
        )

        timeline = investigation.get(
            "timeline",
            [],
        )

        metric_analysis = investigation.get(
            "metric_analysis",
            {},
        )

        deployment = investigation.get(
            "deployment",
        )

        # ---------------------------------------------------------
        # Incident
        # ---------------------------------------------------------

        incident = self._build_incident_summary(
            metric_analysis=metric_analysis,
            logs=summary.get("key_logs", []),
        )

        # ---------------------------------------------------------
        # Impact
        # ---------------------------------------------------------

        impact = self._build_impact(
            metric_analysis=metric_analysis,
        )

        # ---------------------------------------------------------
        # Timeline
        # ---------------------------------------------------------

        timeline_summary = self._build_timeline(
            timeline,
        )

        # ---------------------------------------------------------
        # Hypotheses
        # ---------------------------------------------------------

        hypotheses = rca.get(
            "hypotheses",
            [],
        )

        # ---------------------------------------------------------
        # Final report
        # ---------------------------------------------------------

        return {
            "report_version": "1.0",

            "incident": incident,

            "affected_service": service,

            "investigation_window": {
                "start": investigation_window.get("start"),
                "end": investigation_window.get("end"),
            },

            "impact": impact,

            "timeline": timeline_summary,

            "observed_evidence": {
                "anomalies": summary.get(
                    "observed_anomalies",
                    [],
                ),
                "key_logs": summary.get(
                    "key_logs",
                    [],
                ),
                "deployment": deployment,
                "strong_evidence": rca.get(
                    "strong_evidence",
                    [],
                ),
                "supporting_evidence": summary.get(
                    "supporting_evidence",
                    [],
                ),
            },

            "root_cause_hypotheses": hypotheses,

            "limitations": rca.get(
                "limitations",
                [],
            ),

            "missing_evidence": rca.get(
                "missing_evidence",
                [],
            ),

            "runbook_guidance": rca.get(
                "runbook_guidance",
                [],
            ),

            "recommended_next_steps": rca.get(
                "recommendations",
                [],
            ),
        }

    @staticmethod
    def _build_incident_summary(
        metric_analysis: dict[str, Any],
        logs: list[str],
    ) -> str:

        anomalies = metric_analysis.get(
            "metrics",
            {},
        )

        anomaly_count = sum(
            1
            for metric in anomalies.values()
            if metric.get("anomaly")
        )

        error_logs = [
            log
            for log in logs
            if "ERROR" in log.upper()
        ]

        if anomaly_count and error_logs:
            return (
                "Service degradation detected with "
                f"{anomaly_count} anomalous metrics and "
                f"{len(error_logs)} error log events."
            )

        if anomaly_count:
            return (
                "Service degradation detected with "
                f"{anomaly_count} anomalous metrics."
            )

        return "No significant anomaly was detected."

    @staticmethod
    def _build_impact(
        metric_analysis: dict[str, Any],
    ) -> dict[str, Any]:

        metrics = metric_analysis.get(
            "metrics",
            {},
        )

        impact = {
            "latency_degradation": False,
            "error_rate_degradation": False,
            "database_degradation": False,
        }

        for metric in metrics.values():

            metric_type = metric.get(
                "metric_type"
            )

            if (
                metric_type == "latency"
                and metric.get("anomaly")
            ):
                impact["latency_degradation"] = True

            if (
                metric_type == "error_rate"
                and metric.get("anomaly")
            ):
                impact["error_rate_degradation"] = True

            if (
                metric_type == "database_latency"
                and metric.get("anomaly")
            ):
                impact["database_degradation"] = True

        return impact

    @staticmethod
    def _build_timeline(
        timeline: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        return [
            {
                "timestamp": event.get("timestamp"),
                "event_type": event.get("event_type"),
                "description": event.get("description"),
            }
            for event in timeline
        ]
