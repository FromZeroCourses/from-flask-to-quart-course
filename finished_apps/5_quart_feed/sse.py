import asyncio
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class ServerSentEvent:
    data: str
    event: Optional[str] = None  # "post" | "comment" | "like"
    id: Optional[str] = None

    def encode(self) -> bytes:
        msg = f"data: {self.data}\n"
        if self.event is not None:
            msg = f"event: {self.event}\n{msg}"
        if self.id is not None:
            msg = f"id: {self.id}\n{msg}"
        return (msg + "\n").encode("utf-8")


class Broker:
    """Routes Server-Sent Events to connected clients, keyed by user id.

    Each user gets their own set of connection queues, so an event is only
    delivered to the users it is addressed to. This mirrors the persisted
    ``feed`` fan-out: a post is pushed live only to the same recipients that
    got a ``feed`` row (the author's followers + the author). Publishing to a
    single global set (the old behavior) leaked every post to every open page,
    so non-followers briefly saw posts that vanished on refresh.
    """

    def __init__(self) -> None:
        self.connections: dict[int, set[asyncio.Queue]] = {}

    async def publish(self, user_id: int, event: ServerSentEvent) -> None:
        """Deliver ``event`` to every open connection for a single user."""
        for q in list(self.connections.get(user_id, ())):
            await q.put(event)

    async def publish_many(
        self, user_ids: Iterable[int], event: ServerSentEvent
    ) -> None:
        """Deliver ``event`` to every open connection for each recipient."""
        for user_id in set(user_ids):
            await self.publish(user_id, event)

    def subscribe(self, user_id: int) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self.connections.setdefault(user_id, set()).add(q)
        return q

    def unsubscribe(self, user_id: int, q: asyncio.Queue) -> None:
        conns = self.connections.get(user_id)
        if conns is not None:
            conns.discard(q)
            if not conns:
                self.connections.pop(user_id, None)


broker = Broker()  # module-level singleton (single-process demo)
