from celery import shared_task
from .telemetry import detect_missing


@shared_task(name='agent.check_health')
def check_health():
    detect_missing()
