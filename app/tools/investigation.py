from app.observability.investigator import (
    IncidentInvestigator,
)

investigator = IncidentInvestigator()


def investigate_incident(
    service: str,
    start_time: str | None = None,
    end_time: str | None = None,
    incident_report: str | None = None,
) -> dict:
    """
    Run a structured, read-only incident investigation.

    The optional incident report provides user-reported context.
    It is not treated as verified operational evidence.
    """
    print(
        f"[TOOL] investigate_incident("
        f"service={service}, "
        f"start_time={start_time!r}, "
        f"end_time={end_time!r}, "
        f"report_provided={bool(incident_report and incident_report.strip())}"
        f")"
    )

    return investigator.investigate(
        service=service,
        start_time=start_time,
        end_time=end_time,
        incident_report=incident_report,
    )
