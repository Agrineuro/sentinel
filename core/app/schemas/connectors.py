from datetime import datetime
import re
from typing import Any
from urllib.parse import urlparse
from pydantic import BaseModel, Field, model_validator

from app.plugins.registry import plugin_registry

FIELD_MAP_TARGETS = {"type", "severity", "summary", "timestamp", "entity", "entity_id", "value"}


def validate_field_map(field_map):
    if not isinstance(field_map, dict):
        raise ValueError("Translation field map must be an object")
    if set(field_map) - FIELD_MAP_TARGETS:
        raise ValueError("Translation field map contains an unsupported target")
    for target, path in field_map.items():
        if not isinstance(path, str) or len(path) > 200:
            raise ValueError(f"Translation path for {target} must be a short dotted field path")
        if not all(re.fullmatch(r"[A-Za-z0-9_-]{1,80}", part) for part in path.split(".")):
            raise ValueError(f"Translation path for {target} must use dot-separated JSON object keys")


class ConnectorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    connector_type: str = Field(min_length=1, max_length=100)
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)
    username: str | None = Field(default=None, max_length=200)
    password: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_connector_config(self):
        translation = self.config.get("translation") or {}
        field_map = translation.get("field_map", {}) if isinstance(translation, dict) else None
        validate_field_map(field_map)
        supported = {"webhook", "mqtt", "http_poll", "websocket", "proxmox"}
        manifest = plugin_registry.get_manifest(self.connector_type)
        if self.connector_type not in supported and manifest is None:
            raise ValueError("Connector type is not built in or provided by a loaded plugin")
        if manifest is not None and self.connector_type not in supported:
            fields = manifest.get("configuration_schema", {})
            if not isinstance(fields, dict):
                raise ValueError("Plugin configuration schema is invalid")
            unknown = set(self.config) - set(fields) - {"translation"}
            if unknown:
                raise ValueError("Unsupported plugin configuration field: " + sorted(unknown)[0])
            for key, spec in fields.items():
                if not isinstance(spec, dict):
                    raise ValueError("Plugin configuration schema is invalid")
                value = self.config.get(key, spec.get("default"))
                if spec.get("required") and value in (None, ""):
                    raise ValueError("Plugin setting is required: " + key)
                if value is None:
                    continue
                kind = spec.get("type", "string")
                if kind in {"string", "textarea", "url"} and not isinstance(value, str):
                    raise ValueError("Plugin setting must be text: " + key)
                if kind in {"string", "textarea", "url"} and "max_length" in spec and len(value) > spec["max_length"]:
                    raise ValueError("Plugin setting exceeds maximum length: " + key)
                if kind in {"string", "textarea", "url"} and spec.get("minimum_length") and len(value) < spec["minimum_length"]:
                    raise ValueError("Plugin setting is too short: " + key)
                if kind == "integer" and (isinstance(value, bool) or not isinstance(value, int)):
                    raise ValueError("Plugin setting must be an integer: " + key)
                if kind == "boolean" and not isinstance(value, bool):
                    raise ValueError("Plugin setting must be true or false: " + key)
                if kind == "url":
                    parsed = urlparse(value)
                    schemes = spec.get("schemes", ["https"])
                    if not parsed.hostname or parsed.scheme not in schemes or parsed.username or parsed.password:
                        raise ValueError("Plugin URL is invalid: " + key)
                if kind == "integer":
                    if "minimum" in spec and value < spec["minimum"]:
                        raise ValueError("Plugin setting is below minimum: " + key)
                    if "maximum" in spec and value > spec["maximum"]:
                        raise ValueError("Plugin setting exceeds maximum: " + key)
            credential_spec = manifest.get("credentials", {})
            if credential_spec.get("required") and not self.password:
                raise ValueError("Plugin credential is required")
            if bool(self.username) != bool(self.password):
                raise ValueError("Provide both plugin credential fields")
        if self.connector_type == "mqtt":
            if not str(self.config.get("host") or "").strip():
                raise ValueError("MQTT host is required")
            if not str(self.config.get("topic") or "").strip():
                raise ValueError("MQTT topic filter is required")
            try:
                port = int(self.config.get("port", 1883))
                qos = int(self.config.get("qos", 0))
            except (TypeError, ValueError) as exc:
                raise ValueError("MQTT port and QoS must be numbers") from exc
            if not 1 <= port <= 65535:
                raise ValueError("MQTT port must be between 1 and 65535")
            if qos not in (0, 1, 2):
                raise ValueError("MQTT QoS must be 0, 1, or 2")
            if bool(self.username) != bool(self.password):
                raise ValueError("Provide both MQTT username and password")
        if self.connector_type == "proxmox":
            url = str(self.config.get("url") or "").strip()
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("Proxmox URL must be an absolute HTTPS URL without embedded credentials")
            if "!" not in str(self.username or "") or not self.password:
                raise ValueError("Proxmox requires an API token ID and secret")
            if "verify_tls" in self.config and not isinstance(self.config.get("verify_tls"), bool):
                raise ValueError("Proxmox TLS verification setting must be true or false")
            try:
                interval = int(self.config.get("poll_interval_seconds", 60))
            except (TypeError, ValueError) as exc:
                raise ValueError("Proxmox polling interval must be a number") from exc
            if not 30 <= interval <= 3600:
                raise ValueError("Proxmox polling interval must be between 30 and 3600 seconds")
        if self.connector_type == "websocket":
            url = str(self.config.get("url") or "").strip()
            parsed = urlparse(url)
            if parsed.scheme not in {"ws", "wss"} or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("WebSocket URL must be an absolute ws:// or wss:// URL without embedded credentials")
            auth_type = str(self.config.get("auth_type", "none"))
            if auth_type not in {"none", "bearer"}:
                raise ValueError("WebSocket authentication must be none or bearer")
            if auth_type == "bearer" and (self.username or not self.password):
                raise ValueError("WebSocket bearer authentication requires a token and no username")
            if auth_type == "none" and (self.username or self.password):
                raise ValueError("Credentials were provided while WebSocket authentication is disabled")
        if self.connector_type == "http_poll":
            url = str(self.config.get("url") or "").strip()
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("HTTP connector URL must be an absolute HTTP or HTTPS URL without embedded credentials")
            try:
                interval = int(self.config.get("poll_interval_seconds", 60))
                timeout = int(self.config.get("timeout_seconds", 10))
            except (TypeError, ValueError) as exc:
                raise ValueError("HTTP polling interval and timeout must be numbers") from exc
            if not 15 <= interval <= 3600:
                raise ValueError("HTTP polling interval must be between 15 and 3600 seconds")
            if not 1 <= timeout <= 30:
                raise ValueError("HTTP timeout must be between 1 and 30 seconds")
            auth_type = str(self.config.get("auth_type", "none"))
            if auth_type not in {"none", "basic", "bearer"}:
                raise ValueError("HTTP authentication must be none, basic, or bearer")
            if auth_type == "basic" and (not self.username or not self.password):
                raise ValueError("Basic authentication requires both a username and password")
            if auth_type == "bearer" and (self.username or not self.password):
                raise ValueError("Bearer authentication requires a token and no username")
            if auth_type == "none" and (self.username or self.password):
                raise ValueError("Credentials were provided while HTTP authentication is disabled")
        return self

class ConnectorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    enabled: bool | None = None
    translation_field_map: dict[str, str] | None = None

    @model_validator(mode="after")
    def validate_translation(self):
        if self.translation_field_map is not None:
            validate_field_map(self.translation_field_map)
        return self

class ConnectorRead(BaseModel):
    id: str
    name: str
    connector_type: str
    direction: str
    enabled: bool
    status: str
    config: dict[str, Any]
    credential_id: str | None = None
    last_checked_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime
    ingest_path: str | None = None

class ConnectorCreated(ConnectorRead):
    webhook_token: str | None = None

class ConnectorTestResult(BaseModel):
    status: str
    message: str
    latency_ms: float | None = None
