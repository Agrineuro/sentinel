from typing import Any, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from email.utils import parseaddr
import re


class NotificationDestinationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    channel_type: Literal["email", "sms"]
    destination: str = Field(min_length=3, max_length=320)
    provider_secret: str = Field(default='', max_length=4000)
    config: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_destination(self):
        if self.channel_type == "email":
            if set(self.config) - {"smtp_host", "smtp_port", "security", "from_address", "smtp_username"}:
                raise ValueError("Unsupported SMTP configuration field")
            recipient = self.destination.strip()
            if parseaddr(recipient)[1] != recipient or "@" not in recipient:
                raise ValueError("Enter a valid notification email address")
            host = str(self.config.get("smtp_host") or "").strip()
            try:
                port = int(self.config.get("smtp_port", 587))
            except (TypeError, ValueError) as exc:
                raise ValueError("SMTP port must be a number") from exc
            security = self.config.get("security", "starttls")
            if not host or any(ch.isspace() for ch in host):
                raise ValueError("SMTP host is required")
            if not 1 <= port <= 65535:
                raise ValueError("SMTP port must be between 1 and 65535")
            if security not in {"starttls", "ssl"}:
                raise ValueError("SMTP security must be STARTTLS or SSL/TLS")
            from_address = str(self.config.get("from_address") or "").strip()
            if parseaddr(from_address)[1] != from_address or "@" not in from_address:
                raise ValueError("Enter a valid sender email address")
            username = self.config.get("smtp_username")
            if username is not None and (not isinstance(username, str) or len(username) > 320):
                raise ValueError("SMTP username is invalid")
            if username and not self.provider_secret:
                raise ValueError("SMTP password is required when SMTP authentication is enabled")
        else:
            if set(self.config) - {"account_sid", "from_number"}:
                raise ValueError("Unsupported SMS configuration field")
            if not re.fullmatch(r"\+[1-9][0-9]{7,14}", self.destination.strip()):
                raise ValueError("Use an international phone number in E.164 format, such as +14155550123")
            if not self.provider_secret:
                raise ValueError("Twilio Auth Token is required")
            if not re.fullmatch(r"AC[0-9a-fA-F]{32}", str(self.config.get("account_sid") or "")):
                raise ValueError("Twilio Account SID is invalid")
            if not re.fullmatch(r"\+[1-9][0-9]{7,14}", str(self.config.get("from_number") or "")):
                raise ValueError("Twilio sender number must use E.164 format")
        return self


class NotificationDestinationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    channel_type: str
    masked_destination: str
    enabled: bool
    status: str
    last_error: str | None = None
    created_at: datetime


class NotificationDestinationUpdate(BaseModel):
    enabled: bool


class NotificationSubscriptionUpdate(BaseModel):
    destination_ids: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("destination_ids")
    @classmethod
    def destinations_are_unique(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Notification destinations cannot be repeated")
        return value
