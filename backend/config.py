from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    postgres_host: str = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "appdb")
    postgres_user: str = os.getenv("POSTGRES_USER", "appuser")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "REMOVED_SECRET")
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    secret_key: str = os.getenv("SECRET_KEY", "change-this-secret")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    max_queue_size: int = int(os.getenv("MAX_QUEUE_SIZE", "100"))
    celery_worker_concurrency: int = int(os.getenv("CELERY_WORKER_CONCURRENCY", "4"))
    app_timezone: str = os.getenv("APP_TIMEZONE", "Asia/Kolkata")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"


settings = Settings()
