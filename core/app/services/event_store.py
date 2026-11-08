from datetime import datetime
from typing import Any


class EventStore:
    def __init__(self, max_events: int = 1000):
        self.events: list[dict[str, Any]] = []
        self.max_events = max_events

    def add(self, event: dict[str, Any]):
        event_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
        }

        self.events.append(event_record)

        if len(self.events) > self.max_events:
            self.events.pop(0)

    def list(self):
        return list(reversed(self.events))


event_store = EventStore()
