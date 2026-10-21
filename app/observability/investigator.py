from datetime import timedelta
import re
from datetime import timedelta
from app.observability.summary import InvestigationSummaryBuilder
from app.observability.local import LocalObservabilityProvider
from app.observability.analyzer import MetricAnalyzer
from app.observability.timeline import IncidentTimeline
from app.observability.evidence import EvidenceCollector
from app.observability.time_utils import parse_timestamp
from app.observability.rca import RCAEngine
from app.rag.retriever import search_runbook
from app.observability.report_only import build_report_only_investigation
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
    def _run_stage(self, stage_name: str, operation, *args, **kwargs):
        print(f"[INVESTIGATOR] Starting: {stage_name}")

        try:
            result = operation(*args, **kwargs)
            print(f"[INVESTIGATOR] Completed: {stage_name}")
            return result
        except Exception:
            import logging

            logging.exception(
                "[INVESTIGATOR] Failed during stage: %s",
                stage_name,
            )
            raise

    def _infer_incident_window(
        self,
        incident_report: str,
    ) -> tuple[str | None, str | None]:
        """
        Infer an incident time window from timestamps in a report.

        Multiple timestamps:
            Use the earliest and latest timestamps.

        One timestamp:
            Use a 15-minute window before and after it.

        No timestamps:
            Return (None, None), allowing the existing provider
            defaults to apply.
        """
        from datetime import datetime, timezone

        timestamp_pattern = re.compile(
            r"\b\d{4}-\d{2}-\d{2}"
            r"(?:[T ]\d{2}:\d{2}"
            r"(?::\d{2}(?:\.\d{1,6})?)?"
            r"(?:Z|[+-]\d{2}:?\d{2})?"
            r")?\b"
        )

        timestamps = []

        for match in timestamp_pattern.finditer(incident_report):
            value = match.group(0)

            try:
                parsed = datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )

                # Treat timestamps without a timezone as UTC.
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                else:
                    parsed = parsed.astimezone(timezone.utc)

                timestamps.append(parsed)

            except ValueError:
                continue

        if not timestamps:
            print(
                "[INVESTIGATOR] No usable timestamps found "
                "in the uploaded report."
            )
            return None, None

        earliest = min(timestamps)
        latest = max(timestamps)

        # A single timestamp needs a surrounding investigation window.
        if earliest == latest:
            earliest -= timedelta(minutes=15)
            latest += timedelta(minutes=15)

        start = earliest.isoformat().replace("+00:00", "Z")
        end = latest.isoformat().replace("+00:00", "Z")

        print(
            "[INVESTIGATOR] Inferred incident window: "
            f"{start} -> {end}"
        )

        return start, end



    def investigate(
    self,
    service: str,
    start_time: str | None = None,
    end_time: str | None = None,
    incident_report: str | None = None,
) -> dict:
        """
        Investigate an incident using observability data and an optional
        user-provided incident report.

        If a report is provided, infer the incident time window from its
        timestamps when explicit times are absent. Collect metrics, baseline
        metrics, logs, and deployment data for independent validation.

        Report-derived claims remain unverified until corroborated by
        observability evidence.
        """

        print(
            f"\n[INVESTIGATOR] Starting investigation "
            f"for service={service}"
        )

        # 1. Preserve uploaded report context without treating it as verified.
        reported_incident_context = None

        if incident_report and incident_report.strip():
            reported_incident_context = {
                "source": "user_uploaded_report",
                "content": incident_report[:10000],
                "verified": False,
            }

            print(
                "[INVESTIGATOR] Incident report received. "
                "Inferring its time window and collecting "
                "independent observability evidence."
            )

            # 2. Infer the time window dynamically.
            # Explicitly supplied start/end times take precedence.
            inferred_start, inferred_end = self._infer_incident_window(
                incident_report
            )

            if start_time is None:
                start_time = inferred_start

            if end_time is None:
                end_time = inferred_end

            reported_incident_context["timestamp_range"] = {
                "start": inferred_start,
                "end": inferred_end,
            }

        print(
            f"[INVESTIGATOR] Investigation window: "
            f"{start_time or 'provider default'} to "
            f"{end_time or 'provider default'}"
        )

        # 3. Collect metrics for the incident window.
        # 1. Collect incident-window metrics.
        metrics = self._run_stage(
            "collect incident metrics",
            self.provider.get_service_metrics,
            service=service,
            start_time=start_time,
            end_time=end_time,
        )

        # 2. Collect historical baseline metrics.
        baseline_metrics = self._run_stage(
            "collect baseline metrics",
            self._get_baseline_metrics,
            service=service,
            start_time=start_time,
            end_time=end_time,
        )
         # 5. Analyze current metrics against the baseline.
        metric_analysis = self.analyzer.analyze(
            metrics_data=metrics,
            baseline_data=baseline_metrics,
        )

        # 3. Collect incident-window logs.
        logs = self._run_stage(
            "search incident logs",
            self.provider.search_logs,
            service=service,
            start_time=start_time,
            end_time=end_time,
        )




        # 7. Retrieve recent deployment information.
        deployment = self.provider.get_recent_deployment(
            service=service
        )

        # 8. Build an incident timeline from collected evidence.
        timeline_builder = IncidentTimeline()

        timeline_builder.add_metric_events(metrics)
        timeline_builder.add_log_events(logs)

        if deployment:
            timeline_builder.add_deployment_event(deployment)

        timeline = timeline_builder.build()

        # 9. Collect evidence from metrics, logs, and deployments.
        evidence_collector = EvidenceCollector()

        analyzed_metrics = metric_analysis.get("metrics", {})
        current_timestamp = metric_analysis.get("current_timestamp")

        for metric_name, metric_data in analyzed_metrics.items():
            evidence_collector.add_metric_evidence(
                metric_name=metric_name,
                metric_data=metric_data,
                timestamp=current_timestamp,
            )

        for log_line in logs:
            evidence_collector.add_log_evidence(log_line)

        if deployment:
            evidence_collector.add_deployment_evidence(deployment)

        # 10. Document missing evidence explicitly.
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

        # 11. Retrieve relevant runbook context.
        runbook_context = self._retrieve_runbook_context(
            service=service,
            metric_analysis=metric_analysis,
            logs=logs,
            deployment=deployment,
        )

        # 12. Build the investigation summary.
        investigation_summary = self.summary_builder.build(
            metric_analysis=metric_analysis,
            logs=logs,
            deployment=deployment,
            timeline=timeline,
            evidence=evidence,
            runbook_context=runbook_context,
        )

        # 13. Package all investigation inputs.
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
            "reported_incident_context": reported_incident_context,
        }

        # 14. Perform root-cause analysis using collected evidence.
        rca_analysis = self.rca_engine.analyze(
            investigation_package
        )

        investigation_package["rca_analysis"] = rca_analysis

        # 15. Generate the final incident investigation report.
        final_report = self.report_builder.build(
            investigation_package
        )

        # Include report provenance and retrieved guidance in the final report.
        if isinstance(final_report, dict):
            final_report["reported_incident_context"] = (
                reported_incident_context
            )
            final_report["runbook_guidance"] = runbook_context

        # 16. Return the complete investigation result.
        result = {
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
            "reported_incident_context": reported_incident_context,
            "rca_analysis": rca_analysis,
            "final_report": final_report,
        }

        print(
            "[INVESTIGATOR] Investigation completed. "
            f"Metrics collected: "
            f"{len(metrics) if isinstance(metrics, (list, dict)) else 'unknown'}, "
            f"Logs collected: "
            f"{len(logs) if isinstance(logs, (list, dict)) else 'unknown'}, "
            f"Deployment: "
            f"{'available' if deployment else 'unavailable'}"
        )

        if reported_incident_context:
            print(
                "[INVESTIGATOR] Report claims remain unverified "
                "unless corroborated by observability evidence."
            )

        return result



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

        analyzed_metrics = metric_analysis.get("metrics", {})

        # 1. Identify important metric anomalies.
        anomalous_metrics = []

        for metric_name, metric_data in analyzed_metrics.items():
            if (
                isinstance(metric_data, dict)
                and metric_data.get("anomaly")
            ):
                anomalous_metrics.append(metric_name)

        if anomalous_metrics:
            queries.append(
                f"{service} high latency "
                "database latency error rate troubleshooting"
            )

        # 2. Identify slow database queries from logs.
        query_names = []

        for log_line in logs or []:
            if (
                "database query" in log_line.lower()
                and "query=" in log_line
            ):
                query_part = log_line.split("query=", 1)[1]
                query_name = query_part.split()[0].strip()

                if query_name and query_name not in query_names:
                    query_names.append(query_name)

        for query_name in query_names:
            queries.append(
                f"{service} slow database query "
                f"{query_name} investigation"
            )

        # 3. Identify deployment-related investigation.
        if deployment:
            changes = deployment.get("changes", [])

            if changes:
                changes_text = " ".join(
                    str(change) for change in changes
                )

                queries.append(
                    f"{service} recent deployment "
                    f"query changes latency {changes_text}"
                )
            else:
                queries.append(
                    f"{service} recent deployment "
                    "changed query causing latency"
                )

        # 4. Always have a fallback query.
        if not queries:
            queries.append(
                f"{service} incident high latency investigation"
            )

        # 5. Execute RAG searches and deduplicate results globally.
        runbook_context = []
        best_results = {}

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
                    "[INVESTIGATOR] Runbook retrieval failed: "
                    f"{exc}"
                )
                continue

            if not results:
                continue

            unique_query_results = []

            for result in results:
                if not isinstance(result, dict):
                    continue

                document = result.get("document", result)

                content = str(document.get("content", "")).strip()
                source = str(document.get("source", "")).strip()
                section = str(document.get("section", "")).strip()

                if not content:
                    continue

                # Treat results as duplicates only when their source,
                # section, and content match.
                result_key = (
                    source.casefold(),
                    section.casefold(),
                    content.casefold(),
                )

                try:
                    score = float(
                        result.get("relevance_score", 0.0)
                    )
                except (TypeError, ValueError):
                    score = 0.0

                normalized_result = {
                    "document": {
                        "content": content,
                        "source": source,
                        "section": section,
                    },
                    "relevance_score": score,
                }

                existing = best_results.get(result_key)

                if existing is None:
                    best_results[result_key] = {
                        "result": normalized_result,
                        "query": query,
                    }
                elif score > existing["result"]["relevance_score"]:
                    best_results[result_key] = {
                        "result": normalized_result,
                        "query": query,
                    }

            # Keep the original query-group structure.
            # Results are attached to the query that retrieved
            # their highest-scoring version.
            runbook_context.append(
                {
                    "query": query,
                    "results": unique_query_results,
                }
            )

        # 6. Assign each unique result to its best-matching query group.
        for entry in runbook_context:
            entry["results"] = []

        query_groups = {
            entry["query"]: entry
            for entry in runbook_context
        }

        for item in best_results.values():
            query = item["query"]
            result = item["result"]

            if query in query_groups:
                query_groups[query]["results"].append(result)

        # Remove groups that contain no unique results.
        runbook_context = [
            entry
            for entry in runbook_context
            if entry["results"]
        ]

        # 7. Return the same structure expected by downstream components.
        return runbook_context
