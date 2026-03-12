from datetime import datetime, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, EmailStr, field_serializer

from backend.config import settings


Operation = Literal["add", "subtract", "multiply", "divide"]


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> datetime:
        return to_app_timezone(value)


class CalculationCreate(BaseModel):
    operand_a: float
    operand_b: float
    operation: Operation


class CalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    operation: str
    operand_a: float
    operand_b: float
    status: str
    result: float | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    user_id: int

    @field_serializer("created_at", "updated_at")
    def serialize_timestamps(self, value: datetime) -> datetime:
        return to_app_timezone(value)


class QueueResponse(BaseModel):
    message: str
    request_id: int
    task_id: str
    status: str


APP_TIMEZONE = ZoneInfo(settings.app_timezone)


def to_app_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(APP_TIMEZONE)
