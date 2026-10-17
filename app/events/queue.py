import asyncio
from typing import Any


class EventQueue:
    """
    Local asynchronous event queue.

    This provides a queue abstraction that can later be
    replaced with Pub/Sub, Kafka, RabbitMQ, etc.
    """

    def __init__(self):
        self._queue: asyncio.Queue[
            dict[str, Any]
        ] = asyncio.Queue()

    async def publish(
        self,
        event: dict[str, Any],
    ) -> None:

        await self._queue.put(
            event
        )

    async def consume(
        self,
    ) -> dict[str, Any]:

        return await self._queue.get()

    def task_done(self) -> None:

        self._queue.task_done()

    def size(self) -> int:

        return self._queue.qsize()