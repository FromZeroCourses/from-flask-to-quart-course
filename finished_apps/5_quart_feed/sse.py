import asyncio
from dataclasses import dataclass
from typing import Optional


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
    def __init__(self) -> None:
        self.connections: set[asyncio.Queue] = set()

    async def publish(self, event: ServerSentEvent) -> None:
        for q in list(self.connections):
            await q.put(event)

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self.connections.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self.connections.discard(q)


broker = Broker()  # module-level singleton (single-process demo)
