from typing import Any


class InvestigationSummaryBuilder:
    """
    Converts the complete investigation package into a compact,
    LLM-friendly reasoning summary.

    Raw evidence is preserved separately for auditability.
    """

    def build(
        self,
        metric_analysis: dict,
        logs: list[str],
        deployment: dict | None,
        timeline: list[dict],
        evidence: list[dict],
        runbook_context: list[dict],
    ) -> dict:

        return {
            "observed_anomalies": self._extract_anomalies(
                metric_analysis
            ),
            "key_logs": self._extract_key_logs(
                logs
            ),
            "deployment_correlation": self._build_deployment_summary(
                deployment
            ),
            "timeline": self._build_timeline_summary(
                timeline
            ),
            "strong_evidence": self._extract_evidence(
                evidence,
                strength="strong",
            ),
            "supporting_evidence": self._extract_evidence(
                evidence,
                strength="supporting",
            ),
            "missing_evidence": self._extract_missing_evidence(
                evidence
            ),
            "runbook_guidance": self._extract_runbook_guidance(
                runbook_context
            ),
        }

    # =============================================================
    # Metrics
    # =============================================================

    @staticmethod
    def _extract_anomalies(
        metric_analysis: dict,
    ) -> list[dict[str, Any]]:

        anomalies = []

        for metric_name, metric_data in metric_analysis.get(
            "metrics",
            {},
        ).items():

            if not metric_data.get("anomaly"):
                continue

            anomalies.append(
                {
                    "metric": metric_name,
                    "baseline": metric_data.get("baseline"),
                    "current": metric_data.get("current"),
                    "change_percent": metric_data.get(
                        "change_percent"
                    ),
                    "metric_type": metric_data.get(
                        "metric_type"
                    ),
                }
            )

        return anomalies

    # =============================================================
    # Logs
    # =============================================================

    @staticmethod
    def _extract_key_logs(
        logs: list[str],
    ) -> list[str]:

        key_logs = []

        for log_line in logs:

            upper_line = log_line.upper()

            if (
                "ERROR" in upper_line
                or "WARN" in upper_line
            ):
                key_logs.append(log_line)

        return key_logs

    # =============================================================
    # Deployment
    # =============================================================

    @staticmethod
    def _build_deployment_summary(
        deployment: dict | None,
    ) -> dict | None:

        if not deployment:
            return None

        return {
            "version": deployment.get("version"),
            "previous_version": deployment.get(
                "previous_version"
            ),
            "deployment_id": deployment.get(
                "deployment_id"
            ),
            "deployed_at": deployment.get(
                "deployed_at"
            ),
            "status": deployment.get(
                "status"
            ),
            "changes": deployment.get(
                "changes",
                [],
            ),
        }

    # =============================================================
    # Timeline
    # =============================================================

    @staticmethod
    def _build_timeline_summary(
        timeline: list[dict],
    ) -> list[dict]:

        summary = []

        for event in timeline:

            summary.append(
                {
                    "timestamp": event.get(
                        "timestamp"
                    ),
                    "event_type": event.get(
                        "event_type"
                    ),
                    "description": event.get(
                        "description"
                    ),
                }
            )

        return summary

    # =============================================================
    # Evidence
    # =============================================================

    @staticmethod
    def _extract_evidence(
        evidence: list[dict],
        strength: str,
    ) -> list[dict]:

        return [
            {
                "evidence_type": item.get(
                    "evidence_type"
                ),
                "observation": item.get(
                    "observation"
                ),
                "timestamp": item.get(
                    "timestamp"
                ),
                "source": item.get(
                    "source"
                ),
            }
            for item in evidence
            if item.get("strength") == strength
        ]

    # =============================================================
    # Missing evidence
    # =============================================================

    @staticmethod
    def _extract_missing_evidence(
        evidence: list[dict],
    ) -> list[str]:

        return [
            item.get("observation")
            for item in evidence
            if item.get("strength") == "missing"
        ]

    # =============================================================
    # Runbook
    # =============================================================

    @staticmethod
    def _extract_runbook_guidance(
        runbook_context: list[dict],
    ) -> list[dict]:

        guidance = []

        for context in runbook_context:

            query = context.get(
                "query"
            )

            for result in context.get(
                "results",
                [],
            ):

                document = result.get(
                    "document",
                    {},
                )

                guidance.append(
                    {
                        "query": query,
                        "section": document.get(
                            "section"
                        ),
                        "content": document.get(
                            "content"
                        ),
                        "relevance_score": result.get(
                            "relevance_score"
                        ),
                        "source": document.get(
                            "source"
                        ),
                    }
                )

        return guidance