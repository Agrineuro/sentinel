from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

class ConnectorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    connector_type: Literal["webhook", "mqtt"]
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)
    username: str | None = Field(default=None, max_length=200)
    password: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_connector_config(self):
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
        return self

class ConnectorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    enabled: bool | None = None

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
