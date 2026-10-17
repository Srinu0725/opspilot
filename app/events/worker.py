import asyncio
from typing import Any

from app.events.handlers import (
    handle_incident_created,
)
from app.events.queue import EventQueue


class IncidentWorker:
    """
    Background worker responsible for processing
    incident events from the event queue.
    """

    def __init__(
        self,
        queue: EventQueue,
    ):
        self.queue = queue

        self._running = False

    async def start(self) -> None:
        """
        Start consuming events continuously.
        """

        self._running = True

        print(
            "[WORKER] Incident worker started."
        )

        while self._running:

            event = await self.queue.consume()

            try:

                await self._process(
                    event
                )

            except Exception as exc:

                print(
                    "[WORKER] "
                    f"Event processing failed: {exc}"
                )

            finally:

                self.queue.task_done()

    async def _process(
        self,
        event: dict[str, Any],
    ) -> None:

        event_type = event.get(
            "event_type"
        )

        print(
            "[WORKER] Processing event: "
            f"{event_type}"
        )

        if event_type == "incident.created":

            await handle_incident_created(
                event
            )

        else:

            print(
                "[WORKER] Unknown event type: "
                f"{event_type}"
            )

    def stop(self) -> None:

        self._running = False