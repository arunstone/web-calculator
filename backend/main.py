from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.celery_app import celery_app
from backend.config import settings
from backend.database import Base, engine, get_db
from backend.models import CalculationRequest, User
from backend.schemas import (
    CalculationCreate,
    CalculationResponse,
    QueueResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from backend.security import create_access_token, get_current_user, hash_password, verify_password
from backend.tasks import process_calculation


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Calculator App", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing_user = db.execute(
        select(User).where((User.email == payload.email) | (User.username == payload.username))
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.email))


@app.get("/api/auth/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@app.post("/api/calculate", response_model=QueueResponse, status_code=status.HTTP_202_ACCEPTED)
def enqueue_calculation(
    payload: CalculationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QueueResponse:
    redis_client = Redis.from_url(settings.redis_url)
    pending_count = redis_client.llen("calculator")

    if pending_count >= settings.max_queue_size:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Queue limit reached ({settings.max_queue_size})",
        )

    calculation = CalculationRequest(
        operation=payload.operation,
        operand_a=payload.operand_a,
        operand_b=payload.operand_b,
        status="pending",
        user_id=current_user.id,
    )
    db.add(calculation)
    db.commit()
    db.refresh(calculation)

    task = process_calculation.delay(calculation.id)
    return QueueResponse(
        message="Calculation queued",
        request_id=calculation.id,
        task_id=task.id,
        status=calculation.status,
    )


@app.get("/api/calculations", response_model=list[CalculationResponse])
def list_calculations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CalculationRequest]:
    calculations = db.execute(
        select(CalculationRequest)
        .where(CalculationRequest.user_id == current_user.id)
        .order_by(CalculationRequest.created_at.desc())
    ).scalars()
    return list(calculations)


@app.get("/api/calculations/{request_id}", response_model=CalculationResponse)
def get_calculation(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CalculationRequest:
    calculation = db.execute(
        select(CalculationRequest).where(
            CalculationRequest.id == request_id, CalculationRequest.user_id == current_user.id
        )
    ).scalar_one_or_none()
    if not calculation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return calculation


@app.get("/api/tasks/{task_id}")
def get_task_status(task_id: str, current_user: User = Depends(get_current_user)) -> dict[str, str]:
    result = celery_app.AsyncResult(task_id)
    return {"task_id": task_id, "status": result.status}
