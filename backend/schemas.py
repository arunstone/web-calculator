from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr


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


class QueueResponse(BaseModel):
    message: str
    request_id: int
    task_id: str
    status: str
