import asyncio
from pprint import pprint

from app.events.bus import LocalEventBus
from app.events.handlers import (
    handle_incident_created,
)
from app.events.models import IncidentEvent
from app.incidents.service import incident_store


async def main():

    # ---------------------------------------------------------
    # Create event bus
    # ---------------------------------------------------------

    bus = LocalEventBus()

    bus.subscribe(
        "incident.created",
        handle_incident_created,
    )

    # ---------------------------------------------------------
    # Create incident event
    # ---------------------------------------------------------

    event = IncidentEvent.create(
        service="payment-api",

        description=(
            "Payment API latency has increased "
            "significantly."
        ),

        severity="high",

        start_time="2026-09-15T18:15:00Z",

        end_time="2026-09-15T18:30:00Z",

        metadata={
            "source": "local-test",
        },
    )

    # ---------------------------------------------------------
    # Create incident state
    # ---------------------------------------------------------

    incident = incident_store.create(
        incident_id=event.event_id,
        service=event.service,
        severity=event.severity,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time,
        metadata=event.metadata,
    )

    print("\nINITIAL INCIDENT STATE:")

    pprint(
        incident.to_dict()
    )

    # ---------------------------------------------------------
    # Publish event
    # ---------------------------------------------------------

    print(
        "\nPUBLISHING INCIDENT EVENT..."
    )

    await bus.publish(
        event.to_dict()
    )

    # ---------------------------------------------------------
    # Read final state
    # ---------------------------------------------------------

    final_incident = incident_store.get(
        event.event_id
    )

    print(
        "\nFINAL INCIDENT STATE:"
    )

    pprint(
        final_incident.to_dict()
    )


if __name__ == "__main__":
    asyncio.run(main())