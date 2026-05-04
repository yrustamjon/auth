# tasks.py

from celery import shared_task
from .models import Organization

from apps.org.models import OrgToken


@shared_task
def generate_daily_tokens():
    for org in Organization.objects.all():
        OrgToken.rotate_daily_for_org(org)

    # expired tokenlarni ham tozalash
    OrgToken.cleanup_expired()
