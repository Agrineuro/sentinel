from datetime import datetime, timezone
import json
from typing import Any

from app.schemas.canonical_event import CanonicalEvent

ALLOWED_SEVERITIES = {"info", "warning", "error", "critical"}
ALIASES = {
    "type": ("type", "event_type", "eventType", "event_name", "event.type", "event.name"),
    "severity": ("severity", "level", "event.severity", "status.severity"),
    "summary": ("summary", "message", "description", "detail", "title", "event.message"),
    "timestamp": ("timestamp", "time", "ts", "created_at", "occurred_at", "datetime", "event.timestamp"),
    "entity_id": ("entity_id", "asset_id", "device_id", "system_id", "device.id", "system.id"),
    "entity": ("entity", "entity_name", "device_name", "host_name", "device.name", "system.name", "hostname", "host"),
    "value": ("value", "data", "payload", "metrics", "reading"),
}


def _at_path(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _first(payload: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        value = _at_path(payload, name)
        if value is not None:
            return value
    return None


def _mapped(payload: dict[str, Any], target: str, field_map: dict[str, str]) -> Any:
    path = field_map.get(target)
    if not path:
        return _first(payload, ALIASES[target])
    value = _at_path(payload, path)
    if value is None:
        raise ValueError(f"Translation path for {target!r} was not found: {path}")
    return value


def _severity(value: Any) -> str:
    text = str(value or "info").strip().casefold()
    normalized = {
        "debug": "info", "trace": "info", "notice": "info", "low": "info", "ok": "info", "healthy": "info",
        "warn": "warning", "medium": "warning", "degraded": "warning",
        "high": "error", "major": "error", "fatal": "critical",
    }.get(text, text)
    if normalized not in ALLOWED_SEVERITIES:
        raise ValueError("Translated severity must be info, warning, error, or critical")
    return normalized


def _text(value: Any, default: str) -> str:
    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def translate_payload(
    payload: dict[str, Any],
    source: str,
    field_map: dict[str, str] | None = None,
) -> CanonicalEvent:
    """Translate a source JSON event to Sentinel's canonical event shape.

    Explicit field_map paths use safe dotted object keys, for example
    {"summary": "alarm.message", "value": "sensor.reading"}.
    Unmapped targets use common aliases automatically.
    """
    mapping = field_map or {}
    event_type = _text(_mapped(payload, "type", mapping), "connector.event")[:80]
    severity = _severity(_mapped(payload, "severity", mapping))
    summary = _text(_mapped(payload, "summary", mapping), "Event received from " + source)[:2000]
    timestamp = _mapped(payload, "timestamp", mapping) or datetime.now(timezone.utc)
    entity_id = _mapped(payload, "entity_id", mapping)
    entity = _mapped(payload, "entity", mapping)
    value = _mapped(payload, "value", mapping)
    if isinstance(entity, dict):
        entity = entity.get("name") or entity.get("hostname") or entity.get("id")
    return CanonicalEvent(
        type=event_type,
        severity=severity,
        summary=summary,
        source=source,
        timestamp=timestamp,
        entity_id=str(entity_id) if entity_id is not None else None,
        entity=str(entity) if entity is not None else None,
        value=value,
        raw=payload,
    )
