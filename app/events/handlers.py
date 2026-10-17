from typing import Any

from app.incidents.service import incident_store
from app.observability.investigator import IncidentInvestigator


investigator = IncidentInvestigator()


async def handle_incident_created(
    event: dict[str, Any],
) -> None:

    incident_id = event.get("event_id")
    service = event.get("service")
    start_time = event.get("start_time")
    end_time = event.get("end_time")

    print(
        "\n[EVENT HANDLER] "
        f"Starting investigation for {service}"
    )

    try:

        await incident_store.start_investigation(
            incident_id
        )

        await incident_store.update_stage(
            incident_id,
            "ANALYZING",
        )

        result = investigator.investigate(
            service=service,
            start_time=start_time,
            end_time=end_time,
        )

        await incident_store.update_stage(
            incident_id,
            "RCA",
        )

        rca_analysis = result.get(
            "rca_analysis"
        )

        if rca_analysis is None:
            print(
                "[EVENT HANDLER] "
                "Warning: RCA analysis missing."
            )

        await incident_store.update_stage(
            incident_id,
            "REPORT_GENERATED",
        )

        final_report = result.get(
            "final_report",
            result,
        )

        await incident_store.set_report(
            incident_id,
            final_report,
        )

        print(
            "\n[EVENT HANDLER] "
            "Investigation completed."
        )

        print(
            f"[EVENT HANDLER] Service: {service}"
        )

        print(
            f"[EVENT HANDLER] Incident ID: {incident_id}"
        )

    except Exception as exc:

        await incident_store.set_error(
            incident_id,
            str(exc),
        )

        print(
            "\n[EVENT HANDLER] "
            f"Investigation failed: {exc}"
        )