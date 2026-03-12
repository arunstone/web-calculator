from celery import Celery

from backend.config import settings


celery_app = Celery("calculator", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_routes = {"backend.tasks.process_calculation": {"queue": "calculator"}}
