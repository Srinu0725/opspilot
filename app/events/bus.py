import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable


EventHandler = Callable[
    [dict[str, Any]],
    Awaitable[None],
]


class LocalEventBus:
    """
    Lightweight in-process event bus.

    Used for local development and testing.

    Later this interface can be backed by Google Pub/Sub,
    Kafka, RabbitMQ, etc.
    """

    def __init__(self):

        self._handlers: dict[
            str,
            list[EventHandler],
        ] = defaultdict(list)

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:

        self._handlers[event_type].append(
            handler
        )

    async def publish(
        self,
        event: dict[str, Any],
    ) -> None:

        event_type = event.get(
            "event_type"
        )

        handlers = self._handlers.get(
            event_type,
            [],
        )

        if not handlers:
            return

        await asyncio.gather(
            *[
                handler(event)
                for handler in handlers
            ]
        )