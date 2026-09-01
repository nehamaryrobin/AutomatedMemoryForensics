from celery import Celery

# Use the redis service defined in docker-compose
# Fallback to localhost if running outside docker directly on host during dev
celery_app = Celery(
    "forensics_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Import tasks so the worker registers them
    imports=["worker.tasks"]
)
