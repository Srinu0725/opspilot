from app.observability.investigator import (
    IncidentInvestigator,
)


investigator = IncidentInvestigator()


def investigate_incident(
    service: str,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict:
    """
    Run a structured incident investigation.

    This tool collects metrics, analyzes historical behavior,
    searches relevant logs, retrieves deployment information,
    builds a chronological timeline, and structures evidence
    for downstream reasoning.

    The investigation is read-only.
    """

    print(
        f"[TOOL] investigate_incident("
        f"service={service}, "
        f"start_time={start_time!r}, "
        f"end_time={end_time!r}"
        f")"
    )

    return investigator.investigate(
        service=service,
        start_time=start_time,
        end_time=end_time,
    )