from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AuthStatus(BaseModel):
    setup_required: bool


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=72)


class AdminSetup(Credentials):
    display_name: str = Field(min_length=1, max_length=120)


class UserCreate(Credentials):
    display_name: str = Field(min_length=1, max_length=120)
    role: str = Field(pattern="^(admin|operator|viewer)$")


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    role: str | None = Field(default=None, pattern="^(admin|operator|viewer)$")
    is_active: bool | None = None


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=12, max_length=72)


class AdminPasswordReset(BaseModel):
    new_password: str = Field(min_length=12, max_length=72)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str
    role: str
    is_active: bool
    created_at: datetime | None = None
