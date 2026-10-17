from datetime import timedelta
from app.observability.summary import InvestigationSummaryBuilder
from app.observability.local import LocalObservabilityProvider
from app.observability.analyzer import MetricAnalyzer
from app.observability.timeline import IncidentTimeline
from app.observability.evidence import EvidenceCollector
from app.observability.time_utils import parse_timestamp
from app.observability.rca import RCAEngine
from app.rag.retriever import search_runbook
from app.observability.report import IncidentReportBuilder


class IncidentInvestigator:
    """
    Orchestrates a structured, read-only incident investigation.

    The investigation separates:

        historical baseline
                +
        incident window

    and enriches the investigation with relevant runbook
    context retrieved through the local RAG system.
    """

    def __init__(
        self,
        provider=None,
        analyzer=None,
        summary_builder=None,
        rca_engine=None,
    ):
        self.provider = provider or LocalObservabilityProvider()
        self.analyzer = analyzer or MetricAnalyzer()
        self.summary_builder = (
            summary_builder
            or InvestigationSummaryBuilder()
        )
        self.rca_engine = (
            rca_engine
            or RCAEngine()
        )
        self.report_builder = IncidentReportBuilder()

    def investigate(
        self,
        service: str,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict:

        print(
            f"\n[INVESTIGATOR] Starting investigation "
            f"for service={service}"
        )

        # =========================================================
        # 1. Incident-window metrics
        # =========================================================

        metrics = self.provider.get_service_metrics(
            service=service,
            start_time=start_time,
            end_time=end_time,
        )

        # =========================================================
        # 2. Historical baseline
        # =========================================================

        baseline_metrics = self._get_baseline_metrics(
            service=service,
            start_time=start_time,
            end_time=end_time,
        )

        # =========================================================
        # 3. Analyze incident metrics against clean baseline
        # =========================================================

        metric_analysis = self.analyzer.analyze(
            metrics_data=metrics,
            baseline_data=baseline_metrics,
        )
        logs = self.provider.search_logs(
            service=service,
            start_time=start_time,
            end_time=end_time,
        )

        # =========================================================
        # 5. Recent deployment
        # =========================================================

        deployment = self.provider.get_recent_deployment(
            service=service
        )

        # =========================================================
        # 6. Timeline
        # =========================================================

        timeline_builder = IncidentTimeline()

        timeline_builder.add_metric_events(
            metrics
        )

        timeline_builder.add_log_events(
            logs
        )

        if deployment:
            timeline_builder.add_deployment_event(
                deployment
            )

        timeline = timeline_builder.build()

        # =========================================================
        # 7. Evidence collection
        # =========================================================

        evidence_collector = EvidenceCollector()

        analyzed_metrics = metric_analysis.get(
            "metrics",
            {}
        )

        current_timestamp = metric_analysis.get(
            "current_timestamp"
        )

        for metric_name, metric_data in analyzed_metrics.items():

            evidence_collector.add_metric_evidence(
                metric_name=metric_name,
                metric_data=metric_data,
                timestamp=current_timestamp,
            )

        for log_line in logs:

            evidence_collector.add_log_evidence(
                log_line
            )

        if deployment:

            evidence_collector.add_deployment_evidence(
                deployment
            )

        # =========================================================
        # 8. Missing evidence
        # =========================================================

        evidence_collector.add_missing_evidence(
            description=(
                "Database EXPLAIN ANALYZE execution plan "
                "for the affected payment_lookup query "
                "is unavailable."
            )
        )

        evidence_collector.add_missing_evidence(
            description=(
                "Database CPU, I/O, lock contention, "
                "and index usage metrics are unavailable."
            )
        )

        evidence = evidence_collector.build()

        # =========================================================
        # 9. Retrieve targeted runbook context
        # =========================================================

        runbook_context = self._retrieve_runbook_context(
            service=service,
            metric_analysis=metric_analysis,
            logs=logs,
            deployment=deployment,
        )

        # =========================================================
        # 10. Build LLM-facing investigation summary
        # =========================================================

        investigation_summary = (
            self.summary_builder.build(
                metric_analysis=metric_analysis,
                logs=logs,
                deployment=deployment,
                timeline=timeline,
                evidence=evidence,
                runbook_context=runbook_context,
            )
        )
        investigation_package = {
            "service": service,
            "investigation_window": {
                "start": start_time,
                "end": end_time,
            },
            "metric_analysis": metric_analysis,
            "logs": logs,
            "deployment": deployment,
            "timeline": timeline,
            "evidence": evidence,
            "runbook_context": runbook_context,
            "investigation_summary": investigation_summary,
        }

        rca_analysis = self.rca_engine.analyze(
            investigation_package
        )
        investigation_package["rca_analysis"] = rca_analysis

        final_report = self.report_builder.build(
            investigation_package
        )

        return {
            "service": service,

            "investigation_window": {
                "start": start_time,
                "end": end_time,
            },

            "baseline_metrics": baseline_metrics,

            "metrics": metrics,

            "metric_analysis": metric_analysis,

            "logs": logs,

            "deployment": deployment,

            "timeline": timeline,

            "evidence": evidence,

            "runbook_context": runbook_context,

            "investigation_summary": investigation_summary,
            "rca_analysis": rca_analysis,
            "final_report": final_report,
        }

    # =============================================================
    # Historical baseline
    # =============================================================

    def _get_baseline_metrics(
        self,
        service: str,
        start_time: str | None,
        end_time: str | None,
    ) -> dict:

        if not start_time:

            return {
                "service": service,
                "metrics": [],
            }

        incident_start = parse_timestamp(
            start_time
        )

        if incident_start is None:

            return {
                "service": service,
                "metrics": [],
            }

        if end_time:

            incident_end = parse_timestamp(
                end_time
            )

            if incident_end and incident_end > incident_start:

                duration = (
                    incident_end - incident_start
                )

            else:

                duration = timedelta(
                    minutes=15
                )

        else:

            duration = timedelta(
                minutes=15
            )

        baseline_end = (
            incident_start
            - timedelta(
                microseconds=1
            )
        )

        baseline_start = (
            incident_start
            - duration
        )

        baseline_start_iso = (
            baseline_start
            .isoformat()
            .replace(
                "+00:00",
                "Z",
            )
        )

        baseline_end_iso = (
            baseline_end
            .isoformat()
            .replace(
                "+00:00",
                "Z",
            )
        )

        print(
            "[INVESTIGATOR] Historical baseline window: "
            f"{baseline_start_iso} → "
            f"{baseline_end_iso}"
        )

        return self.provider.get_service_metrics(
            service=service,
            start_time=baseline_start_iso,
            end_time=baseline_end_iso,
        )

    # =============================================================
    # RAG / Runbook retrieval
    # =============================================================

    def _retrieve_runbook_context(
        self,
        service: str,
        metric_analysis: dict,
        logs: list[str],
        deployment: dict | None,
    ) -> list[dict]:

        queries: list[str] = []

        analyzed_metrics = metric_analysis.get(
            "metrics",
            {}
        )

        # ---------------------------------------------------------
        # Identify important metric anomalies
        # ---------------------------------------------------------

        anomalous_metrics = []

        for metric_name, metric_data in analyzed_metrics.items():

            if metric_data.get("anomaly"):

                anomalous_metrics.append(
                    metric_name
                )

        if anomalous_metrics:

            queries.append(
                f"{service} high latency "
                f"database latency error rate troubleshooting"
            )

        # ---------------------------------------------------------
        # Identify slow database queries from logs
        # ---------------------------------------------------------

        query_names = []

        for log_line in logs:

            if (
                "database query" in log_line.lower()
                and "query=" in log_line
            ):

                query_part = log_line.split(
                    "query=",
                    1,
                )[1]

                query_name = query_part.split(
                    " ",
                    1,
                )[0]

                if query_name not in query_names:

                    query_names.append(
                        query_name
                    )

        for query_name in query_names:

            queries.append(
                f"{service} slow database query "
                f"{query_name} investigation"
            )

        # ---------------------------------------------------------
        # Identify deployment-related investigation
        # ---------------------------------------------------------

        if deployment:

            changes = deployment.get(
                "changes",
                []
            )

            if changes:

                changes_text = " ".join(
                    str(change)
                    for change in changes
                )

                queries.append(
                    f"{service} recent deployment "
                    f"query changes latency "
                    f"{changes_text}"
                )

            else:

                queries.append(
                    f"{service} recent deployment "
                    f"changed query causing latency"
                )

        # ---------------------------------------------------------
        # Always have a fallback query
        # ---------------------------------------------------------

        if not queries:

            queries.append(
                f"{service} incident "
                f"high latency investigation"
            )

        # ---------------------------------------------------------
        # Execute RAG searches
        # ---------------------------------------------------------

        runbook_context = []

        for query in queries:

            print(
                "[INVESTIGATOR] Runbook query: "
                f"{query}"
            )

            try:

                results = search_runbook(
                    service=service,
                    query=query,
                    top_k=3,
                )

            except Exception as exc:

                print(
                    "[INVESTIGATOR] Runbook retrieval "
                    f"failed: {exc}"
                )

                continue

            if not results:
                continue

            runbook_context.append(
                {
                    "query": query,
                    "results": results,
                }
            )

        return runbook_context
