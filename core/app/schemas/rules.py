from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Severity = Literal["debug", "info", "notice", "warning", "error", "critical"]
Operator = Literal["gt", "gte", "lt", "lte"]
FIELD_PATTERN = r"^[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*$"


class RuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)
    observation_type: str = Field(default="*", min_length=1, max_length=80)
    minimum_severity: Severity = "warning"
    source_contains: str | None = Field(default=None, max_length=200)
    entity_contains: str | None = Field(default=None, max_length=200)
    summary_contains: str | None = Field(default=None, max_length=500)
    condition_field: str | None = Field(default=None, max_length=160, pattern=FIELD_PATTERN)
    condition_operator: Operator | None = None
    condition_value: float | None = Field(default=None, allow_inf_nan=False)
    enabled: bool = True

    @model_validator(mode="after")
    def complete_numeric_condition(self):
        parts = (self.condition_field, self.condition_operator, self.condition_value)
        if any(part is not None for part in parts) and not all(part is not None for part in parts):
            raise ValueError("Numeric conditions require a field, operator, and threshold")
        return self


class RuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    observation_type: str | None = Field(default=None, min_length=1, max_length=80)
    minimum_severity: Severity | None = None
    source_contains: str | None = Field(default=None, max_length=200)
    entity_contains: str | None = Field(default=None, max_length=200)
    summary_contains: str | None = Field(default=None, max_length=500)
    condition_field: str | None = Field(default=None, max_length=160, pattern=FIELD_PATTERN)
    condition_operator: Operator | None = None
    condition_value: float | None = Field(default=None, allow_inf_nan=False)
    enabled: bool | None = None


class Rule(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: str
    observation_type: str
    minimum_severity: str
    source_contains: str | None = None
    entity_contains: str | None = None
    summary_contains: str | None = None
    condition_field: str | None = None
    condition_operator: str | None = None
    condition_value: float | None = Field(default=None, allow_inf_nan=False)
    enabled: bool
    created_at: datetime
    updated_at: datetime
