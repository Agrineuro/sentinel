from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any
from uuid import uuid4


@dataclass
class SentinelEvent:
    type: str
    source: str
    severity: str = "info"
    data: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"evt_{uuid4().hex}")
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


EventHandler = Callable[[SentinelEvent], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)

    async def publish(self, event: SentinelEvent) -> None:
        handlers = self._subscribers.get(event.type, [])
        wildcard_handlers = self._subscribers.get("*", [])

        for handler in handlers + wildcard_handlers:
            await handler(event)


event_bus = EventBus()
